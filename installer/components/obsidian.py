import json
import os
from pathlib import Path

from .. import children, shell, ui
from ..model import Context, Platform, Result, Support
from ..paths import absolute_vault_path

KEY = "obsidian"
TITLE = "Obsidian einrichten"
DESCRIPTION = "Obsidian-Setup herunterladen und dessen Auswahl starten; ist Obsidian schon da, nur den Vault-Pfad übernehmen"
DEFAULT = False
ALREADY_INSTALLED = "obsidian:vorhanden"


def supported(platform: Platform) -> Support:
    return Support("ja")


def config_dirs(ctx: Context) -> list[Path]:
    if ctx.platform == "macos":
        return [ctx.home / "Library/Application Support/obsidian"]
    if ctx.platform == "windows":
        return [Path(os.environ.get("APPDATA", ctx.home / "AppData/Roaming")) / "obsidian"]
    return [ctx.home / ".config/obsidian",
            ctx.home / ".var/app/md.obsidian.Obsidian/config/obsidian",
            ctx.home / "snap/obsidian/current/.config/obsidian"]


def app_paths(ctx: Context) -> list[Path]:
    if ctx.platform == "macos":
        return [Path("/Applications/Obsidian.app"), ctx.home / "Applications/Obsidian.app"]
    if ctx.platform == "windows":
        local = Path(os.environ.get("LOCALAPPDATA", ctx.home / "AppData/Local"))
        return [local / "Programs/Obsidian/Obsidian.exe", local / "Obsidian/Obsidian.exe"]
    return []


def is_installed(ctx: Context) -> bool:
    # Die Vault-Liste entsteht beim ersten Start und erkennt damit auch Flatpak, Snap und AppImage.
    if any((directory / "obsidian.json").is_file() for directory in config_dirs(ctx)):
        return True
    return any(path.exists() for path in app_paths(ctx)) or bool(shell.which("obsidian"))


def known_vaults(ctx: Context) -> list[str]:
    found = []
    for directory in config_dirs(ctx):
        try:
            records = json.loads((directory / "obsidian.json").read_text(encoding="utf-8")).get("vaults", {})
        except (OSError, ValueError, AttributeError):
            continue
        for record in records.values() if isinstance(records, dict) else ():
            path = record.get("path") if isinstance(record, dict) else None
            if isinstance(path, str) and path and path not in found:
                found.append(path)
    return found


def prepare(ctx: Context) -> None:
    if is_installed(ctx):
        ctx.values[ALREADY_INSTALLED] = "1"
        print("Obsidian ist schon installiert. Die Einrichtung entfällt, gebraucht wird nur der Vault-Pfad.")
    if not ctx.values.get("vault"):
        ask_vault_path(ctx)


def ask_vault_path(ctx: Context) -> None:
    if ctx.values.get(ALREADY_INSTALLED):
        vaults = known_vaults(ctx)
        for path in vaults:
            print(f"  Bekannter Vault: {path}")
        default = vaults[0] if len(vaults) == 1 else ""
        value = ui.ask_text("Pfad zu deinem Vault?", default, ctx)
    else:
        value = ui.ask_text("Pfad zum vorhandenen oder neuen Vault?", "", ctx)
    if value:
        ctx.values["vault"] = absolute_vault_path(value)


def is_done(ctx: Context) -> bool:
    # Die Auswahl und Erkennung einzelner Obsidian-Bausteine gehören dem Kind-Installer.
    return False


def plan(ctx: Context) -> list[str]:
    if ctx.values.get(ALREADY_INSTALLED):
        return ["Obsidian ist installiert: Einrichtung entfällt, nur der Vault-Pfad wird übernommen."]
    return ["obsidian-setup im Cache klonen oder aktualisieren und mit --vault starten."]


def apply(ctx: Context) -> Result:
    vault = ctx.values.get("vault")
    if not vault:
        return Result(KEY, "handarbeit", "Mit --vault PFAD einen vorhandenen oder neuen Vault angeben.")
    if ctx.values.get(ALREADY_INSTALLED):
        return keep_existing_obsidian(vault)
    return children.launch("obsidian-setup", KEY, ctx)


def keep_existing_obsidian(vault: str) -> Result:
    if not Path(vault).is_dir():
        return Result(KEY, "handarbeit", f"{vault} existiert nicht. Vault in Obsidian anlegen oder --vault PFAD korrigieren.")
    return Result(KEY, "übersprungen", f"Obsidian schon installiert, Vault übernommen: {vault}")

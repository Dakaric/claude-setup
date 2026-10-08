from .. import children, ui
from ..model import Context, Platform, Result, Support
from ..paths import absolute_vault_path

KEY = "obsidian"
TITLE = "Obsidian einrichten"
DESCRIPTION = "Obsidian-Setup herunterladen und dessen Auswahl starten"
DEFAULT = False


def supported(platform: Platform) -> Support:
    return Support("ja")


def prepare(ctx: Context) -> None:
    if not ctx.values.get("vault"):
        value = ui.ask_text("Pfad zum vorhandenen oder neuen Vault?", "", ctx)
        if value:
            ctx.values["vault"] = absolute_vault_path(value)


def is_done(ctx: Context) -> bool:
    # Die Auswahl und Erkennung einzelner Obsidian-Bausteine gehören dem Kind-Installer.
    return False


def plan(ctx: Context) -> list[str]:
    return ["obsidian-setup im Cache klonen oder aktualisieren und mit --vault starten."]


def apply(ctx: Context) -> Result:
    if not ctx.values.get("vault"):
        return Result(KEY, "handarbeit", "Mit --vault PFAD einen vorhandenen oder neuen Vault angeben.")
    return children.launch("obsidian-setup", KEY, ctx)

from pathlib import Path

from .. import children, shell
from ..model import Context, Platform, Result, Support

KEY = "vault-suche"
TITLE = "Semantische Vault-Suche"
DESCRIPTION = "Vault-Suche herunterladen und deren Installer starten"
DEFAULT = False


def supported(platform: Platform) -> Support:
    return Support("ja")


def is_done(ctx: Context) -> bool:
    if not shell.which("claude"):
        return False
    result = shell.run(["claude", "mcp", "list"], ctx, check=False, capture=True)
    registered = result.returncode == 0 and any(line.strip().startswith("vault-search:") for line in result.stdout.splitlines())
    # Nur der Kind-Installer kann prüfen, ob die Registrierung zum gewünschten Vault passt.
    return registered and not ctx.values.get("vault")


def plan(ctx: Context) -> list[str]:
    return ["vault-search-mcp im Cache klonen oder aktualisieren und mit --vault starten; vorhandener Vault erforderlich."]


def apply(ctx: Context) -> Result:
    value = ctx.values.get("vault")
    if not value:
        return Result(KEY, "handarbeit", "Zuerst einen Vault wählen: --vault PFAD.")
    if not Path(value).is_dir():
        return Result(KEY, "handarbeit", "Der Vault muss existieren. Zuerst Obsidian einrichten oder --vault PFAD korrigieren.")
    return children.launch("vault-search-mcp", KEY, ctx)

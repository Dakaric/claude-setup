from .. import plugins, shell
from ..github import GITHUB_OWNER
from ..model import Context, Platform, Result, Support

KEY = "toolkit"
TITLE = "Eigenes Toolkit"
DESCRIPTION = "Neun Skills sowie Context7 und Playwright, benötigt Node.js"
DEFAULT = True
PLUGIN = "toolkit@claude-setup"


def supported(platform: Platform) -> Support:
    return Support("ja")


def is_done(ctx: Context) -> bool:
    return plugins.installed(PLUGIN, ctx)


def plan(ctx: Context) -> list[str]:
    return ["Toolkit-Marketplace hinzufügen und toolkit@claude-setup im Benutzerbereich installieren."]


def apply(ctx: Context) -> Result:
    if not shell.which("node") or not shell.which("npx"):
        return Result(KEY, "handarbeit", "Node.js für die MCP-Server installieren: https://nodejs.org/; danach erneut starten.")
    if not shell.which("claude"):
        return Result(KEY, "handarbeit", "Zuerst Claude Code installieren und anmelden: claude auth login")
    plugins.install(f"{GITHUB_OWNER}/claude-setup", PLUGIN, ctx)
    return Result(KEY, "erledigt")

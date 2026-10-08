import os

from .. import downloads, shell
from ..model import Context, Platform, Result, Support
from ..platform import cache_dir

KEY = "claude-code"
TITLE = "Claude Code"
DESCRIPTION = "Claude Code über den offiziellen Installer installieren"
DEFAULT = True


def supported(platform: Platform) -> Support:
    return Support("ja", "Git für Windows wird für das Bash-Werkzeug empfohlen.") if platform == "windows" else Support("ja")


def is_done(ctx: Context) -> bool:
    return bool(shell.which("claude"))


def plan(ctx: Context) -> list[str]:
    return ["Offiziellen Installer von https://claude.ai laden und ausführen."]


def apply(ctx: Context) -> Result:
    if ctx.platform == "windows":
        if not shell.which("powershell"):
            return Result(KEY, "handarbeit", "PowerShell öffnen und den offiziellen Installer unter https://claude.ai/install.ps1 ausführen.")
        shell.run(["powershell", "-NoProfile", "-Command", "irm https://claude.ai/install.ps1 | iex"], ctx)
    else:
        if not shell.which("bash"):
            return Result(KEY, "handarbeit", "Bash installieren und erneut starten.")
        script = cache_dir("claude-setup", ctx) / "claude-install.sh"
        downloads.download("https://claude.ai/install.sh", script)
        shell.run(["bash", str(script)], ctx)
    os.environ["PATH"] = str(ctx.home / ".local/bin") + os.pathsep + os.environ.get("PATH", "")
    note = "Zum Anmelden claude auth login ausführen."
    if ctx.platform == "windows" and not shell.which("git"):
        note += " Git für Windows wird für das Bash-Werkzeug empfohlen: https://git-scm.com/download/win"
    return Result(KEY, "erledigt", note)

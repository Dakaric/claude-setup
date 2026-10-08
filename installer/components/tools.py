from .. import shell
from ..model import Context, Platform, Result, Support

KEY = "werkzeuge"
TITLE = "Werkzeuge"
DESCRIPTION = "Git, Node.js, GitHub CLI und jq prüfen und installieren"
DEFAULT = True
TOOLS = (
    ("git", "git", "Git.Git", "https://git-scm.com/downloads"),
    ("node", "node", "OpenJS.NodeJS.LTS", "https://nodejs.org/"),
    ("gh", "gh", "GitHub.cli", "https://cli.github.com/"),
    ("jq", "jq", "jqlang.jq", "https://jqlang.org/download/"),
)


def supported(platform: Platform) -> Support:
    return Support("ja", "Unter Linux: Installationslinks für fehlende Werkzeuge.") if platform == "linux" else Support("ja")


def missing():
    return [tool for tool in TOOLS if not shell.which(tool[0])]


def is_done(ctx: Context) -> bool:
    return not missing()


def plan(ctx: Context) -> list[str]:
    return ["Fehlende Werkzeuge mit Homebrew (macOS) oder winget (Windows) installieren, sonst Links anzeigen."]


def apply(ctx: Context) -> Result:
    notes, errors = [], []
    for name, brew, winget, url in missing():
        try:
            if ctx.platform == "windows" and shell.which("winget"):
                shell.run(["winget", "install", "--id", winget, "-e", "--accept-package-agreements", "--accept-source-agreements"], ctx)
                notes.append(f"{name}: Neues Terminal öffnen und erneut starten.")
            elif ctx.platform == "macos" and shell.which("brew"):
                shell.run(["brew", "install", brew], ctx)
            else:
                notes.append(f"{name} installieren: {url}")
        except Exception as error:
            errors.append(f"{name}: {error}")
    status = "fehler" if errors else "handarbeit" if notes else "erledigt"
    return Result(KEY, status, "; ".join(errors + notes))

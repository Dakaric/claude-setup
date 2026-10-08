import os

from . import shell
from .github import GITHUB_OWNER
from .model import Context, Result
from .platform import cache_dir


def launch(repo: str, key: str, ctx: Context) -> Result:
    for command in ("git", "uv"):
        if not shell.which(command):
            link = "https://git-scm.com/downloads" if command == "git" else "https://docs.astral.sh/uv/"
            return Result(key, "handarbeit", f"{command} installieren: {link}; danach erneut starten.")
    checkout = cache_dir("claude-setup", ctx) / repo
    checkout.parent.mkdir(parents=True, exist_ok=True)
    if (checkout / ".git").is_dir():
        shell.run(["git", "-C", str(checkout), "pull", "--ff-only"], ctx)
    elif checkout.exists():
        return Result(key, "handarbeit", f"{checkout} ist kein Git-Klon. Ordner prüfen und zur Seite verschieben.")
    else:
        shell.run(["git", "clone", "--depth", "1", f"https://github.com/{GITHUB_OWNER}/{repo}.git", str(checkout)], ctx)
    command = [shell.which("uv"), "run", "--directory", str(checkout)]
    command += ["--project", str(checkout)] if repo == "vault-search-mcp" else ["--no-project", "--python", "3.12"]
    command += ["python", "-m", "installer", "--vault", ctx.values["vault"]]
    if ctx.assume_yes:
        command.append("--yes")
    env = {**os.environ, "PYTHONPATH": str(checkout), "PYTHONUTF8": "1"}
    shell.run(command, ctx, env=env)
    return Result(key, "erledigt", "Unterinstaller beendet; seine Hinweise zu Handarbeit beachten.")

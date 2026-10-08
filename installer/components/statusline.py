import json

from .. import downloads, shell
from ..config import includes, merge_file, settings_path
from ..fsutil import backup, merge_json, read_json, write_json
from ..github import GITHUB_OWNER
from ..model import Context, Platform, Result, Support
from ..platform import cache_dir

KEY = "statuszeile"
TITLE = "Statuszeile"
DESCRIPTION = "Kontextanzeige für Claude Code, benötigt bash, jq und curl"
DEFAULT = True
URL = f"https://github.com/{GITHUB_OWNER}/claude-code-statusline/releases/latest/download/install.sh"


def supported(platform: Platform) -> Support:
    return Support("nein", "Skript braucht bash und jq; Windows wird nicht unterstützt.") if platform == "windows" else Support("ja")


def desired(ctx: Context) -> dict:
    return {"statusLine": {"type": "command", "command": '"' + str(ctx.home / ".claude/statusline.sh") + '"'}}


def is_done(ctx: Context) -> bool:
    return (ctx.home / ".claude/statusline.sh").is_file() and includes(settings_path(ctx), desired(ctx))


def plan(ctx: Context) -> list[str]:
    return [f"{URL} herunterladen und mit bash und --yes ausführen."]


def apply(ctx: Context) -> Result:
    links = {"jq": "https://jqlang.org/download/", "curl": "https://curl.se/download.html", "bash": "https://www.gnu.org/software/bash/"}
    for name, url in links.items():
        if not shell.which(name):
            return Result(KEY, "handarbeit", f"{name} installieren: {url}; danach erneut starten.")
    script = cache_dir("claude-setup", ctx) / "statusline-install.sh"
    downloads.download(URL, script)
    path = settings_path(ctx)
    previous = read_json(path, {})
    backup(path)
    backup(ctx.home / ".claude/statusline.sh")
    try:
        shell.run(["bash", str(script), "--yes"], ctx)
    finally:
        # Auch bei einem abgebrochenen Fremdinstaller behalten Nutzerwerte Vorrang.
        if path.exists() or previous:
            try:
                current = read_json(path, {})
            except json.JSONDecodeError:
                write_json(path, previous)
                raise
            preserved = merge_json(previous, current)
            if preserved != current:
                write_json(path, preserved)
    merge_file(settings_path(ctx), desired(ctx))
    return Result(KEY, "erledigt")

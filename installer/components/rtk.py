import json
import re
import shlex
import tomllib
from pathlib import Path

from .. import plugins, shell
from ..config import includes, merge_file, settings_path
from ..fsutil import backup
from ..model import Context, Platform, Result, Support

KEY = "rtk"
TITLE = "RTK"
DESCRIPTION = "Terminal-Ausgaben kürzen, Git-Diffs vollständig behalten"
DEFAULT = True
URL = "https://github.com/rtk-ai/rtk"


def supported(platform: Platform) -> Support:
    return Support("nein", "RTK-Einrichtung unter Windows wird nicht unterstützt.") if platform == "windows" else Support("ja")


def hook_settings() -> dict:
    command = shlex.quote(shell.which("rtk") or "rtk") + " hook claude"
    return {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": command}]}]}}


def config_path(ctx: Context) -> Path | None:
    result = shell.run(["rtk", "config"], ctx, check=False, capture=True)
    if result.returncode:
        return None
    for line in result.stdout.splitlines():
        if line.startswith("Config: "):
            path = Path(line.removeprefix("Config: ").strip()).expanduser()
            if path.is_absolute():
                return path
    return None


def exclude_git_diff(path: Path) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    data = tomllib.loads(text)
    commands = data.get("hooks", {}).get("exclude_commands", [])
    if not isinstance(commands, list) or not all(isinstance(value, str) for value in commands):
        raise ValueError("RTK: hooks.exclude_commands muss eine Liste von Befehlen sein.")
    if "git diff" in commands:
        return
    line = "exclude_commands = " + json.dumps(commands + ["git diff"], ensure_ascii=False)
    section = re.search(r"(?m)^\[hooks\][^\n]*(?:\n|$)", text)
    if section:
        following = re.search(r"(?m)^\[", text[section.end():])
        end = section.end() + following.start() if following else len(text)
        body = text[section.end():end]
        assignment = re.compile(r"(?ms)^exclude_commands\s*=\s*\[.*?\][^\n]*")
        if "exclude_commands" in data.get("hooks", {}) and not assignment.search(body):
            raise ValueError("RTK-Konfiguration verwendet eine unbekannte Schreibweise; git diff bitte von Hand ausnehmen.")
        body = assignment.sub(lambda _: line, body, count=1) if assignment.search(body) else line + "\n" + body
        updated = text[:section.end()] + body + text[end:]
    elif "hooks" in data:
        raise ValueError("RTK-Konfiguration verwendet eine Inline-Tabelle; git diff bitte von Hand ausnehmen.")
    else:
        updated = text.rstrip() + "\n\n[hooks]\n" + line + "\n"
    # Erst nach erfolgreicher Prüfung schreiben, damit Sonderformen keine Daten verlieren.
    parsed = tomllib.loads(updated)
    expected = {**data, "hooks": {**data.get("hooks", {}), "exclude_commands": commands + ["git diff"]}}
    if parsed != expected:
        raise ValueError("RTK-Konfiguration kann nicht sicher ergänzt werden.")
    backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(updated, encoding="utf-8")


def is_done(ctx: Context) -> bool:
    if not shell.which("rtk") or not includes(settings_path(ctx), hook_settings()):
        return False
    if plugins.installed(plugins.TOKEN_PLUGIN, ctx) and not includes(settings_path(ctx), {"env": {"TOKEN_OPTIMIZER_BASH_COMPRESS": "0"}}):
        return False
    path = config_path(ctx)
    return bool(path and path.exists() and "git diff" in tomllib.loads(path.read_text(encoding="utf-8")).get("hooks", {}).get("exclude_commands", []))


def plan(ctx: Context) -> list[str]:
    return ["RTK bei Bedarf über Homebrew installieren, Bash-Hook ergänzen und git diff in der RTK-Konfiguration ausnehmen."]


def apply(ctx: Context) -> Result:
    if not shell.which("rtk"):
        if not shell.which("brew"):
            return Result(KEY, "handarbeit", f"RTK installieren: {URL}; danach erneut starten.")
        shell.run(["brew", "install", "rtk"], ctx)
        if not shell.which("rtk"):
            return Result(KEY, "handarbeit", "Neues Terminal öffnen und Installer erneut starten, damit RTK im PATH liegt.")
    merge_file(settings_path(ctx), hook_settings())
    plugins.coordinate_compression(ctx)
    path = config_path(ctx)
    if path is None:
        return Result(KEY, "handarbeit", "RTK-Hook eingerichtet. RTK hat keinen Konfigurationspfad ausgegeben; git diff unter hooks.exclude_commands von Hand ausnehmen.")
    try:
        exclude_git_diff(path)
    except ValueError as error:
        return Result(KEY, "handarbeit", str(error))
    return Result(KEY, "erledigt")

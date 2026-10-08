import os
from pathlib import Path

from .. import shell
from ..config import merge_file, template
from ..fsutil import read_json
from ..model import Context, Platform, Result, Support

KEY = "claude-desktop"
TITLE = "Claude Desktop"
DESCRIPTION = "Context7 und bei bekanntem Vault den Dateizugriff ergänzen"
DEFAULT = False


def supported(platform: Platform) -> Support:
    return Support("nein", "Keine offizielle Desktop-App für Linux.") if platform == "linux" else Support("ja")


def config_path(ctx: Context) -> Path:
    if ctx.platform == "windows":
        base = Path(os.environ.get("APPDATA", ctx.home / "AppData/Roaming")) / "Claude"
    else:
        base = ctx.home / "Library/Application Support/Claude"
    return base / "claude_desktop_config.json"


def desired(ctx: Context) -> dict:
    result = template("claude_desktop_config.json")
    if vault := ctx.values.get("vault"):
        result["mcpServers"]["filesystem"] = {
            "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", vault]}
    return result


def is_done(ctx: Context) -> bool:
    current = read_json(config_path(ctx), {}).get("mcpServers", {})
    return all(current.get(key) == value for key, value in desired(ctx)["mcpServers"].items())


def plan(ctx: Context) -> list[str]:
    return [f"MCP-Server in {config_path(ctx)} zusammenführen; eigene Einträge bleiben erhalten."]


def apply(ctx: Context) -> Result:
    path = config_path(ctx)
    if ctx.platform == "windows" and not path.parent.exists():
        return Result(KEY, "handarbeit", "Claude Desktop einmal starten. Bei der Store-Fassung den Konfigurationsordner in der App öffnen; der Standardordner fehlt.")
    if not shell.which("node") or not shell.which("npx"):
        return Result(KEY, "handarbeit", "Node.js installieren: https://nodejs.org/ und erneut starten.")
    current = read_json(path, {}).get("mcpServers", {})
    wanted = desired(ctx)["mcpServers"]
    # Serverbefehle und ihre Argumente sind eine Einheit, keine vereinigbaren Listen.
    additions = {key: value for key, value in wanted.items() if key not in current}
    conflicts = [key for key, value in wanted.items() if key in current and current[key] != value]
    merge_file(path, {"mcpServers": additions})
    if conflicts:
        return Result(KEY, "handarbeit", "Vorhandene Server unverändert erhalten: " + ", ".join(conflicts)
                      + ". Befehle und Vault-Pfade in der Desktop-Konfiguration prüfen; danach Desktop neu starten.")
    return Result(KEY, "erledigt", "Claude Desktop neu starten.")

from . import shell
from .config import merge_file, settings_path
from .fsutil import read_json
from .model import Context

TOKEN_PLUGIN = "token-optimizer@alexgreensh-token-optimizer"


def installed(plugin: str, ctx: Context) -> bool:
    if ctx.values.get(f"installed:{plugin}") == "1":
        return True
    data = read_json(ctx.home / ".claude/plugins/installed_plugins.json", {})
    entries = data.get("plugins", {}).get(plugin, [])
    return any(entry.get("scope") == "user" for entry in entries)


def install(source: str, plugin: str, ctx: Context) -> None:
    if installed(plugin, ctx):
        return
    marketplace = plugin.split("@", 1)[1]
    result = shell.run(["claude", "plugin", "marketplace", "add", source], ctx, check=False)
    if result.returncode:
        shell.run(["claude", "plugin", "marketplace", "update", marketplace], ctx)
    shell.run(["claude", "plugin", "install", plugin, "--scope", "user"], ctx)
    ctx.values[f"installed:{plugin}"] = "1"


def coordinate_compression(ctx: Context) -> None:
    if installed(TOKEN_PLUGIN, ctx) and shell.which("rtk"):
        merge_file(settings_path(ctx), {"env": {"TOKEN_OPTIMIZER_BASH_COMPRESS": "0"}})

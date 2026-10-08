from .. import plugins, shell, ui
from ..model import Context, Platform, Result, Support

KEY = "plugins-extern"
TITLE = "Weitere Plugins"
DESCRIPTION = "Superpowers, Token Optimizer und die Skills von Matt Pocock einzeln auswählen"
DEFAULT = True
PLUGINS = (
    ("obra/superpowers", "superpowers@superpowers-dev", "Superpowers"),
    ("alexgreensh/token-optimizer", plugins.TOKEN_PLUGIN, "Token Optimizer (PolyForm-Noncommercial)"),
    ("mattpocock/skills", "mattpocock-skills@mattpocock", "Skills von Matt Pocock"),
)


def supported(platform: Platform) -> Support:
    return Support("ja")


def prepare(ctx: Context) -> None:
    for source, plugin, title in PLUGINS:
        key = f"plugin:{plugin}"
        if key not in ctx.values:
            ctx.values[key] = "1" if ui.ask_yes_no(f"{title} installieren?", True, ctx) else "0"


def selected(ctx: Context):
    return [(source, plugin) for source, plugin, _ in PLUGINS if ctx.values.get(f"plugin:{plugin}") == "1"]


def is_done(ctx: Context) -> bool:
    return all(plugins.installed(plugin, ctx) for _, plugin in selected(ctx))


def plan(ctx: Context) -> list[str]:
    return [f"{plugin} aus {source} installieren." for source, plugin in selected(ctx)] or ["Keine weiteren Plugins gewählt."]


def apply(ctx: Context) -> Result:
    if not shell.which("claude"):
        return Result(KEY, "handarbeit", "Claude Code installieren und claude auth login ausführen.")
    errors = []
    for source, plugin in selected(ctx):
        try:
            plugins.install(source, plugin, ctx)
        except Exception as error:
            errors.append(f"{plugin}: {error}")
    plugins.coordinate_compression(ctx)
    return Result(KEY, "fehler" if errors else "erledigt", "; ".join(errors))

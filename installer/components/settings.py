from ..config import includes, merge_file, settings_path, template
from ..model import Context, Platform, Result, Support

KEY = "einstellungen"
TITLE = "Claude-Code-Einstellungen"
DESCRIPTION = "Rechte und einstündigen Prompt-Cache ergänzen"
DEFAULT = True


def supported(platform: Platform) -> Support:
    return Support("ja")


def is_done(ctx: Context) -> bool:
    return includes(settings_path(ctx), template("settings.json"))


def plan(ctx: Context) -> list[str]:
    return [f"{settings_path(ctx)} sichern und zusammenführen; vorhandene Werte behalten."]


def apply(ctx: Context) -> Result:
    merge_file(settings_path(ctx), template("settings.json"))
    return Result(KEY, "erledigt")

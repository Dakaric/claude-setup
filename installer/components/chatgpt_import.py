from pathlib import Path

from ..config import ROOT
from ..model import Context, Platform, Result, Support

KEY = "chatgpt-umzug"
TITLE = "Umzug von ChatGPT"
DESCRIPTION = "Nur wer bisher ChatGPT genutzt hat: Skill mit Prompt, der Erinnerungen und Projekte aus ChatGPT nach Claude holt"
DEFAULT = False
SOURCE = ROOT / "skills/chatgpt-umzug"
MARKER = ".claude-setup"


def supported(platform: Platform) -> Support:
    return Support("ja")


def skill_dir(ctx: Context) -> Path:
    return ctx.home / ".claude/skills/chatgpt-umzug"


def source_files() -> list[Path]:
    return sorted(path for path in SOURCE.iterdir() if path.is_file())


def is_done(ctx: Context) -> bool:
    destination = skill_dir(ctx)
    return (destination / MARKER).is_file() and all(
        (destination / source.name).is_file() and (destination / source.name).read_bytes() == source.read_bytes()
        for source in source_files())


def plan(ctx: Context) -> list[str]:
    return [f"Skill chatgpt-umzug nach {skill_dir(ctx)} kopieren."]


def apply(ctx: Context) -> Result:
    destination = skill_dir(ctx)
    if destination.is_symlink() or (destination.exists() and not (destination / MARKER).is_file()):
        return Result(KEY, "handarbeit", f"{destination} ist eine eigene Installation und bleibt unverändert.")
    destination.mkdir(parents=True, exist_ok=True)
    for source in source_files():
        (destination / source.name).write_bytes(source.read_bytes())
    (destination / MARKER).write_text("Von claude-setup installiert.\n", encoding="utf-8")
    return Result(KEY, "erledigt", "In Claude sagen: „Hol meine Daten aus ChatGPT“.")

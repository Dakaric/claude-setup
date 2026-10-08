from pathlib import Path

from .fsutil import backup, merge_json, read_json, write_json
from .model import Context

ROOT = Path(__file__).resolve().parents[1]


def template(name: str):
    return read_json(ROOT / "templates" / name, {})


def settings_path(ctx: Context) -> Path:
    return ctx.home / ".claude/settings.json"


def includes(path: Path, extra: dict) -> bool:
    if not path.exists():
        return False
    current = read_json(path, {})
    return merge_json(current, extra) == current


def merge_file(path: Path, extra: dict) -> None:
    current = read_json(path, {})
    merged = merge_json(current, extra)
    if not path.exists() or current != merged:
        backup(path)
        write_json(path, merged)

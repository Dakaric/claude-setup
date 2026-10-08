import copy
import json
import shutil
from datetime import datetime
from pathlib import Path

Json = dict | list


def backup_path(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = path.with_name(f"{path.name}.sicherung-{stamp}")
    counter = 1
    while target.exists():
        target = path.with_name(f"{path.name}.sicherung-{stamp}-{counter}")
        counter += 1
    return target


def backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    target = backup_path(path)
    if path.is_dir():
        shutil.copytree(path, target, symlinks=True)
    else:
        shutil.copy2(path, target)
    return target


def merge_json(base: Json, extra: Json) -> Json:
    result = copy.deepcopy(base)
    if isinstance(base, dict) and isinstance(extra, dict):
        for key, value in extra.items():
            result[key] = merge_json(base[key], value) if key in base else copy.deepcopy(value)
    elif isinstance(base, list) and isinstance(extra, list):
        for value in extra:
            if value not in result:
                result.append(copy.deepcopy(value))
    return result


def read_json(path: Path, empty: Json) -> Json:
    if not path.exists():
        return copy.deepcopy(empty)
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Json) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def safe_rmtree(path: Path, allowed_root: Path) -> None:
    resolved, root = path.resolve(), allowed_root.resolve()
    if resolved == root or not resolved.is_relative_to(root):
        raise ValueError("Rekursives Löschen ist nur unterhalb des Cache-Ordners erlaubt.")
    if path.is_symlink():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)

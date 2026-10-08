import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def component(key, apply=None, **overrides):
    from installer.model import Result, Support
    data = dict(KEY=key, TITLE=key, DESCRIPTION="Beschreibung", DEFAULT=True,
                supported=lambda platform: Support("ja"), is_done=lambda ctx: False,
                plan=lambda ctx: ["Plan"], apply=apply or (lambda ctx: Result(key, "erledigt")))
    data.update(overrides)
    return SimpleNamespace(**data)


def test_merge_keeps_user_entries():
    from installer.fsutil import merge_json
    base = {"own": 1, "nested": {"value": False, "list": ["mine"]}}
    extra = {"nested": {"value": True, "list": ["new"]}, "new": 2}
    assert merge_json(base, extra) == {"own": 1, "nested": {"value": False, "list": ["mine", "new"]}, "new": 2}
    assert base["nested"]["list"] == ["mine"]


@pytest.mark.parametrize("base,extra,expected", [
    ({"a": [1, 2]}, {"a": [2, 3]}, {"a": [1, 2, 3]}),
    (["a", "b"], ["b", "c"], ["a", "b", "c"]),
    ([{"a": 1}], [{"a": 1}, {"b": 2}], [{"a": 1}, {"b": 2}]),
])
def test_merge_lists_without_duplicates(base, extra, expected):
    from installer.fsutil import merge_json
    assert merge_json(base, extra) == expected


def test_merge_top_level_list():
    from installer.fsutil import merge_json
    assert merge_json(["a", "b"], ["b", "c"]) == ["a", "b", "c"]


def test_merge_list_of_dicts():
    from installer.fsutil import merge_json
    assert merge_json([{"x": 1}], [{"x": 1}]) == [{"x": 1}]


def test_backup_names_copy_with_timestamp(tmp_path):
    from installer.fsutil import backup
    path = tmp_path / "settings.json"
    assert backup(path) is None
    path.write_text("alt", encoding="utf-8")
    first, second = backup(path), backup(path)
    assert first != second
    assert first.name.startswith("settings.json.sicherung-")
    assert first.read_text(encoding="utf-8") == second.read_text(encoding="utf-8") == "alt"


def test_backup_directory(tmp_path):
    from installer.fsutil import backup
    folder = tmp_path / "Ordner"
    folder.mkdir()
    (folder / "Datei").write_text("Inhalt", encoding="utf-8")
    assert (backup(folder) / "Datei").read_text(encoding="utf-8") == "Inhalt"


@pytest.mark.parametrize("target", ["outside", "root"])
def test_safe_rmtree_refuses_outside_root(tmp_path, target):
    from installer.fsutil import safe_rmtree
    root = tmp_path / "cache"
    root.mkdir()
    with pytest.raises(ValueError):
        safe_rmtree(tmp_path if target == "outside" else root, root)
    assert root.exists()


def test_safe_rmtree_refuses_root_itself(tmp_path):
    from installer.fsutil import safe_rmtree
    with pytest.raises(ValueError):
        safe_rmtree(tmp_path, tmp_path)


def test_safe_rmtree_removes_cache_child(tmp_path):
    from tests_support import real_run

    target = tmp_path / "cache" / "download"
    target.mkdir(parents=True)
    (target / "artifact").write_text("download", encoding="utf-8")
    # Eigener Prozess hält lokale Python-Startanpassungen von der Testsperre getrennt.
    real_run(
        [sys.executable, "-c", "from pathlib import Path; import sys; "
         "from installer.fsutil import safe_rmtree; safe_rmtree(Path(sys.argv[1]), Path(sys.argv[2]))",
         str(target), str(tmp_path / "cache")],
        cwd=Path(__file__).resolve().parents[1], check=True,
    )
    assert not target.exists()
    assert target.parent.is_dir()


def test_safe_rmtree_refuses_symlink_escape(tmp_path):
    from installer.fsutil import safe_rmtree
    cache, outside = tmp_path / "cache", tmp_path / "outside"
    cache.mkdir()
    outside.mkdir()
    try:
        (cache / "link").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Symlinks benötigen auf diesem System zusätzliche Rechte")
    with pytest.raises(ValueError):
        safe_rmtree(cache / "link", cache)
    assert outside.exists()


@pytest.mark.parametrize("platform", ["macos", "linux", "windows"])
def test_cache_dir_per_platform(ctx, monkeypatch, platform):
    from installer.platform import cache_dir
    ctx.platform = platform
    monkeypatch.setenv("LOCALAPPDATA", str(ctx.home / "Local"))
    expected = ctx.home / "Local/app/cache" if platform == "windows" else ctx.home / ".cache/app"
    assert cache_dir("app", ctx) == expected


def test_no_tty_without_yes_exits_2(monkeypatch):
    from installer.cli import main
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    assert main([]) == 2


@pytest.mark.parametrize("phase", ["supported", "is_done", "plan", "apply"])
def test_failing_component_does_not_stop_others(ctx, phase):
    from installer.run import run_components
    def fail(*args):
        raise RuntimeError("Kaputt")
    results = run_components([component("bad", **{phase: fail}), component("good")], ctx, None)
    assert [result.status for result in results] == ["fehler", "erledigt"]


def test_dry_run_applies_nothing(ctx):
    from installer.run import run_components
    ctx.dry_run = True
    def fail(ctx):
        pytest.fail("Dry-Run darf keine externen Prüfungen oder Änderungen ausführen")
    results = run_components([component("test", apply=fail, is_done=fail)], ctx, None)
    assert results[0].status == "übersprungen"
    assert not ctx.home.exists()


def test_only_explicitly_selects_optional_component(ctx):
    from installer.run import run_components
    results = run_components([component("optional", DEFAULT=False), component("other")], ctx, {"optional"})
    assert [(result.key, result.status) for result in results] == [("optional", "erledigt")]


def test_unknown_component_exits_2(monkeypatch):
    from installer.cli import main
    assert main(["--yes", "--only", "typo"]) == 2


def test_cli_dry_run_does_not_touch_home(ctx, monkeypatch):
    from installer.cli import main
    monkeypatch.setattr(Path, "home", lambda: ctx.home)
    assert main(["--dry-run", "--yes", "--name", "Test"]) == 0
    assert not ctx.home.exists()


def test_utf8_json_roundtrip(tmp_path):
    from installer.fsutil import read_json, write_json
    path = tmp_path / "Änderung" / "config.json"
    write_json(path, {"vault": "Mein Vault/07 Anhänge"})
    assert "Anhänge" in path.read_text(encoding="utf-8")
    assert read_json(path, {}) == {"vault": "Mein Vault/07 Anhänge"}


def test_shell_dry_run(ctx):
    from installer.shell import run
    ctx.dry_run = True
    assert run(["unused", "Mein Vault/07 Anhänge"], ctx) is None

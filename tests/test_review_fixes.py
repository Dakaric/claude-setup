import ast
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_interactive_relative_vault_exits_two(ctx, monkeypatch, capsys):
    from installer import cli

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    answers = iter(["ja", "Mein Vault"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    monkeypatch.setattr(Path, "home", lambda: ctx.home)
    assert cli.main(["--only", "obsidian", "--dry-run"]) == 2
    assert "absolut" in capsys.readouterr().out
    assert not ctx.home.exists()


def test_private_executable_is_blocked(tmp_path):
    executable = tmp_path / ("rm-" + "waechter") / "runner"
    with pytest.raises(AssertionError, match="Externer Zugriff"):
        subprocess.run([str(executable)], check=True)


def test_project_does_not_set_uv_cache():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert "cache-dir" not in config.get("tool", {}).get("uv", {})


def test_local_uv_configuration_is_ignored():
    from test_guards import repository_files

    assert ROOT / "uv.toml" not in repository_files()
    assert "/uv.toml" in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()


def test_github_owner_has_one_definition():
    definitions = []
    for path in (ROOT / "installer").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if ("Daka" + "ric") in node.value:
                    definitions.append((path.relative_to(ROOT).as_posix(), node.value))
    assert definitions == [("installer/github.py", "Daka" + "ric")]

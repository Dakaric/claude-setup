import os
import subprocess
import shlex
import sys
from pathlib import Path

import pytest
import tests_support

ROOT = Path(__file__).resolve().parents[1]


def test_bash_launcher_from_other_directory(tmp_path, monkeypatch):
    import shutil
    bash = shutil.which("bash")
    if os.name == "nt" or not bash:
        pytest.skip("Bash-Starthilfe wird auf macOS und Linux ausgeführt")
    repo = tmp_path / "Repo mit Ä"
    repo.mkdir()
    (repo / "install.sh").write_bytes((ROOT / "install.sh").read_bytes())
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_uv = bin_dir / "uv"
    fake_uv.write_text('#!/bin/sh\nprintf "%s\\n" "$PYTHONPATH" "$@" > "$BOOTSTRAP_LOG"\nexit 7\n')
    fake_uv.chmod(0o755)
    logfile = tmp_path / "log"
    vault = str(tmp_path / "Mein Vault/07 Anhänge")
    # Hier läuft nur die eigene Starthilfe mit einer lokalen uv-Attrappe.
    import tests_support
    result = tests_support.real_run(
        [bash, str(repo / "install.sh"), "--vault", vault, "--yes"],
        cwd=tmp_path, env={**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"], "BOOTSTRAP_LOG": str(logfile)},
    )
    assert result.returncode == 7
    assert logfile.read_text().splitlines() == [str(repo), "run", "--directory", str(repo), "--no-project", "--python", "3.12", "python", "-m", "installer", "--vault", vault, "--yes"]


def test_powershell_launcher_from_other_directory(tmp_path):
    import json
    import shutil
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if not powershell:
        pytest.skip("PowerShell wird in der Windows-CI geprüft")
    repo = tmp_path / "Repo mit Ä"
    repo.mkdir()
    script = repo / "install.ps1"
    script.write_bytes((ROOT / "install.ps1").read_bytes())
    harness = tmp_path / "test.ps1"
    harness.write_text('''function global:uv {
    @($env:PYTHONPATH) + @($args) | ConvertTo-Json | Set-Content -Encoding UTF8 $env:BOOTSTRAP_LOG
    $global:LASTEXITCODE = 7
}
& $env:BOOTSTRAP_INSTALL --vault $env:BOOTSTRAP_VAULT --yes
exit $LASTEXITCODE
''', encoding="utf-8-sig")
    logfile = tmp_path / "log.json"
    vault = str(tmp_path / "Mein Vault/07 Anhänge")
    result = tests_support.real_run(
        [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(harness)],
        cwd=tmp_path, env={**os.environ, "BOOTSTRAP_INSTALL": str(script), "BOOTSTRAP_LOG": str(logfile), "BOOTSTRAP_VAULT": vault},
    )
    assert result.returncode == 7
    assert json.loads(logfile.read_text(encoding="utf-8-sig")) == [str(repo), "run", "--directory", str(repo), "--no-project", "--python", "3.12", "python", "-m", "installer", "--vault", vault, "--yes"]


def test_relative_vault_exits_two(tmp_path):
    result = tests_support.real_run(
        [sys.executable, "-m", "installer", "--dry-run", "--yes", "--vault", "Mein Vault/07 Anhänge"],
        cwd=tmp_path, env={**os.environ, "PYTHONPATH": str(ROOT), "PYTHONUTF8": "1"},
        capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == 2
    assert "absolut" in result.stdout
    assert not (tmp_path / "Mein Vault").exists()


def test_windows_documented_command_preserves_git_bash_arguments():
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    command = next(part for part in text.split("`") if part.startswith("powershell "))
    arguments = shlex.split(command)
    assert arguments[arguments.index("-File") + 1] == "./install.ps1"
    assert arguments[arguments.index("--only") + 1] == "regeln,einstellungen"

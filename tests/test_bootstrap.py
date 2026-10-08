import json
import os
import shlex
import shutil
import sys
from pathlib import Path

import pytest
import tests_support

ROOT = Path(__file__).resolve().parents[1]
POWERSHELLS = [path for name in ("pwsh", "powershell") if (path := shutil.which(name))]


def test_bash_launcher_from_other_directory(tmp_path):
    bash = shutil.which("bash")
    if os.name == "nt" or not bash:
        pytest.skip("Bash-Starthilfe wird auf macOS und Linux ausgeführt")
    repo = tmp_path / "Repo mit Ä"
    repo.mkdir()
    (repo / "install.sh").write_text((ROOT / "install.sh").read_text(encoding="utf-8"), encoding="utf-8")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_uv = bin_dir / "uv"
    fake_uv.write_text('#!/bin/sh\nprintf "%s\\n" "$PYTHONPATH" "$@" > "$BOOTSTRAP_LOG"\nexit 7\n', encoding="utf-8")
    fake_uv.chmod(0o755)
    logfile = tmp_path / "log"
    vault = str(tmp_path / "Mein Vault/07 Anhänge")
    # Hier läuft nur die eigene Starthilfe mit einer lokalen uv-Attrappe.
    result = tests_support.real_run(
        [bash, str(repo / "install.sh"), "--vault", vault, "--yes"],
        cwd=tmp_path, env={**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"], "BOOTSTRAP_LOG": str(logfile)},
        capture_output=True, encoding="utf-8",
    )
    assert result.returncode == 7, result.stderr
    assert logfile.read_text(encoding="utf-8").splitlines() == [str(repo), "run", "--directory", str(repo), "--no-project", "--python", "3.12", "python", "-m", "installer", "--vault", vault, "--yes"]


@pytest.fixture
def argument_recorder(tmp_path):
    script = tmp_path / "uv Attrappe Ä.py"
    script.write_text('''import json
import os
import sys
from pathlib import Path

arguments = [os.environ["PYTHONPATH"], *sys.argv[1:]]
Path(os.environ["NATIVE_LOG"]).write_text(json.dumps(arguments, ensure_ascii=False), encoding="utf-8")
sys.exit(7)
''', encoding="utf-8")
    return script


def test_argument_recorder_preserves_arguments(tmp_path, argument_recorder):
    arguments = ["3.12", "Mein Vault/07 Anhänge", "Jörg Müller", "regeln,einstellungen"]
    logfile = tmp_path / "native.json"
    result = tests_support.real_run(
        [sys.executable, str(argument_recorder), *arguments],
        env={**os.environ, "PYTHONPATH": str(tmp_path), "NATIVE_LOG": str(logfile)},
        capture_output=True, encoding="utf-8",
    )
    assert result.returncode == 7, result.stderr
    assert json.loads(logfile.read_text(encoding="utf-8")) == [str(tmp_path), *arguments]


@pytest.mark.parametrize("powershell", POWERSHELLS or [None])
def test_powershell_launcher_from_other_directory(tmp_path, argument_recorder, powershell):
    if not powershell:
        pytest.skip("PowerShell fehlt lokal; die CI prüft die Starthilfe auf allen drei Plattformen")
    repo = tmp_path / "Repo mit Ä"
    repo.mkdir()
    script = repo / "install.ps1"
    script.write_text((ROOT / "install.ps1").read_text(encoding="utf-8"), encoding="utf-8")
    harness = tmp_path / "test.ps1"
    harness.write_text('''function global:uv {
    $json = ConvertTo-Json -InputObject (@($env:PYTHONPATH) + @($args))
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($env:BOOTSTRAP_LOG, $json, $utf8)
    & $env:BOOTSTRAP_PYTHON $env:BOOTSTRAP_RECORDER @args
    $global:LASTEXITCODE = $LASTEXITCODE
}
& $env:BOOTSTRAP_INSTALL --vault $env:BOOTSTRAP_VAULT --name $env:BOOTSTRAP_NAME --only "regeln,einstellungen" --yes
exit $LASTEXITCODE
''', encoding="utf-8")
    logfile = tmp_path / "log.json"
    native_log = tmp_path / "native.json"
    vault = str(tmp_path / "Mein Vault/07 Anhänge")
    name = "Jörg Müller"
    result = tests_support.real_run(
        [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(harness)],
        cwd=tmp_path, env={
            **os.environ, "BOOTSTRAP_INSTALL": str(script), "BOOTSTRAP_LOG": str(logfile),
            "BOOTSTRAP_VAULT": vault, "BOOTSTRAP_NAME": name,
            "BOOTSTRAP_PYTHON": sys.executable, "BOOTSTRAP_RECORDER": str(argument_recorder),
            "NATIVE_LOG": str(native_log),
        },
        capture_output=True, encoding="utf-8",
    )
    assert result.returncode == 7, result.stderr
    expected = [str(repo), "run", "--directory", str(repo), "--no-project", "--python", "3.12",
                "python", "-m", "installer", "--vault", vault, "--name", name,
                "--only", "regeln,einstellungen", "--yes"]
    assert json.loads(logfile.read_text(encoding="utf-8")) == expected
    assert json.loads(native_log.read_text(encoding="utf-8")) == expected


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

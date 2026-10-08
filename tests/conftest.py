import socket
import subprocess
import urllib.request

import pytest


@pytest.fixture(autouse=True)
def forbid_external_io(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Externer Zugriff im Test muss gemockt werden")
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(urllib.request, "urlopen", blocked)
    original = subprocess.run

    def guarded(command, *args, **kwargs):
        if command[:2] == ["git", "ls-files"]:
            return original(command, *args, **kwargs)
        return blocked(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", guarded)


@pytest.fixture
def ctx(tmp_path):
    from installer.model import Context
    return Context("macos", tmp_path / "Zuhause", False, True, {"name": "Test", "anrede": "du", "language": "Deutsch"})


@pytest.fixture
def commands(monkeypatch):
    from installer import shell
    recorded = []

    def run(command, **kwargs):
        recorded.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(shell, "which", lambda name: name)
    return recorded

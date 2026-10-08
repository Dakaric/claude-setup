import os
import shutil
import subprocess

from .model import Context


def which(name: str) -> str | None:
    return shutil.which(name)


def run(cmd: list[str], ctx: Context, check: bool = True, *, capture: bool = False,
        env: dict[str, str] | None = None) -> subprocess.CompletedProcess | None:
    if ctx.dry_run:
        print("Geplant:", subprocess.list2cmdline(cmd))
        return None
    return subprocess.run(cmd, check=check, text=True, encoding="utf-8", errors="replace",
                          capture_output=capture, env=env)

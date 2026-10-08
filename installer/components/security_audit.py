import re
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath

from .. import downloads
from ..fsutil import backup_path, safe_rmtree
from ..model import Context, Platform, Result, Support
from ..platform import cache_dir

KEY = "security-audit"
TITLE = "Security-Audit-Skill"
DESCRIPTION = "Sicherheitsprüfung von Code nach der Methode von Cloudflare (MIT-Lizenz)"
DEFAULT = True
REPOSITORY = "cloudflare/security-audit-skill"
# Fester Stand statt main: Eine neue Fassung wird gelesen, bevor sie hier eingetragen wird.
REVISION = "c1c8a8c1471069fb0e188eeaff69b8e8db6564a8"
ARCHIVE_URL = f"https://github.com/{REPOSITORY}/archive/{REVISION}.zip"
SKILL_PREFIX = PurePosixPath(f"security-audit-skill-{REVISION}/skills/security-audit")
MARKER = ".claude-setup-revision"
MAX_SKILL_BYTES = 5_000_000
SAFE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


class UnsafeArchive(ValueError):
    pass


def supported(platform: Platform) -> Support:
    return Support("ja")


def skill_dir(ctx: Context) -> Path:
    return ctx.home / ".claude/skills/security-audit"


def installed_revision(ctx: Context) -> str | None:
    marker = skill_dir(ctx) / MARKER
    return marker.read_text(encoding="utf-8").strip() if marker.is_file() else None


def is_done(ctx: Context) -> bool:
    return installed_revision(ctx) == REVISION


def plan(ctx: Context) -> list[str]:
    return [f"Skill aus {REPOSITORY} auf Stand {REVISION[:7]} nach {skill_dir(ctx)} kopieren."]


def apply(ctx: Context) -> Result:
    destination = skill_dir(ctx)
    if destination.is_symlink() or (destination.exists() and installed_revision(ctx) is None):
        return Result(KEY, "handarbeit", f"{destination} ist eine eigene Installation und bleibt unverändert.")
    cache = cache_dir("claude-setup", ctx)
    staging = extract_skill(cache)
    install(staging, destination, cache)
    return Result(KEY, "erledigt", str(destination))


def extract_skill(cache: Path) -> Path:
    archive, staging = cache / "security-audit-skill.zip", cache / "security-audit"
    downloads.download(ARCHIVE_URL, archive)
    safe_rmtree(staging, cache)
    with zipfile.ZipFile(archive) as bundle:
        members = [(member, path) for member in bundle.infolist() if (path := skill_path(member))]
        if sum(member.file_size for member, _ in members) > MAX_SKILL_BYTES:
            raise UnsafeArchive("Das Archiv ist größer als erwartet und wird nicht entpackt.")
        for member, relative in members:
            target = staging.joinpath(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(bundle.read(member))
    if not (staging / "SKILL.md").is_file():
        raise UnsafeArchive("Das Archiv enthält keinen Skill unter skills/security-audit.")
    (staging / MARKER).write_text(REVISION + "\n", encoding="utf-8")
    return staging


def skill_path(member: zipfile.ZipInfo) -> PurePosixPath | None:
    path = PurePosixPath(member.filename)
    if member.is_dir() or not path.is_relative_to(SKILL_PREFIX):
        return None
    relative = path.relative_to(SKILL_PREFIX)
    is_link = stat.S_ISLNK(member.external_attr >> 16)
    if is_link or not relative.parts or not all(SAFE_NAME.fullmatch(part) for part in relative.parts):
        raise UnsafeArchive(f"Unsicherer Eintrag im Archiv: {member.filename}")
    return relative


def install(staging: Path, destination: Path, cache: Path) -> None:
    # Die Vorfassung wandert in den Cache: Unter ~/.claude/skills würde Claude sie als zweiten Skill laden.
    if destination.exists():
        shutil.move(destination, backup_path(cache / "security-audit-vorher"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(staging, destination)

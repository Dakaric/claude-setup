import hashlib
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
# Fester Stand statt main: Eine neue Fassung wird gelesen, bevor Stand und Prüfsumme hier eingetragen werden.
REVISION = "c1c8a8c1471069fb0e188eeaff69b8e8db6564a8"
CONTENT_SHA256 = "6f8f5e34e8831ea7532162c6e3c1b9e5bce913849f072bfa0ba5412947709266"
ARCHIVE_URL = f"https://github.com/{REPOSITORY}/archive/{REVISION}.zip"
ARCHIVE_ROOT = PurePosixPath(f"security-audit-skill-{REVISION}")
SKILL_PREFIX = ARCHIVE_ROOT / "skills/security-audit"
LICENSE_MEMBER = ARCHIVE_ROOT / "LICENSE"
MARKER = ".claude-setup-revision"
MAX_SKILL_BYTES = 5_000_000
SAFE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")

SkillFiles = dict[PurePosixPath, bytes]


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
    if is_foreign_installation(ctx, destination):
        return Result(KEY, "handarbeit", f"{destination} ist eine eigene Installation und bleibt unverändert.")
    cache = cache_dir("claude-setup", ctx)
    staging = extract_skill(cache)
    install(staging, destination, cache)
    return Result(KEY, "erledigt", str(destination))


def is_foreign_installation(ctx: Context, destination: Path) -> bool:
    if destination.is_symlink() or destination.is_junction():
        return True
    return destination.exists() and installed_revision(ctx) is None


def extract_skill(cache: Path) -> Path:
    archive, staging = cache / "security-audit-skill.zip", cache / "security-audit"
    downloads.download(ARCHIVE_URL, archive)
    files = read_skill_files(archive)
    # Geprüft wird vor dem ersten Schreibzugriff: Abweichender Inhalt landet gar nicht erst auf der Platte.
    if content_digest(files) != CONTENT_SHA256:
        raise UnsafeArchive("Der Inhalt weicht vom geprüften Stand ab und wird nicht installiert.")
    safe_rmtree(staging, cache)
    for relative, content in files.items():
        target = staging.joinpath(*relative.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    return staging


def read_skill_files(archive: Path) -> SkillFiles:
    try:
        with zipfile.ZipFile(archive) as bundle:
            members = [(member, path) for member in bundle.infolist() if (path := skill_path(member))]
            if sum(member.file_size for member, _ in members) > MAX_SKILL_BYTES:
                raise UnsafeArchive("Das Archiv ist größer als erwartet und wird nicht entpackt.")
            return {path: bundle.read(member) for member, path in members}
    except zipfile.BadZipFile as error:
        raise UnsafeArchive("Der Download ist kein gültiges Archiv. Bitte erneut starten.") from error


def skill_path(member: zipfile.ZipInfo) -> PurePosixPath | None:
    path = PurePosixPath(member.filename)
    if path == LICENSE_MEMBER:
        return PurePosixPath("LICENSE")
    if member.is_dir() or not path.is_relative_to(SKILL_PREFIX):
        return None
    relative = path.relative_to(SKILL_PREFIX)
    is_link = stat.S_ISLNK(member.external_attr >> 16)
    if is_link or not relative.parts or not all(SAFE_NAME.fullmatch(part) for part in relative.parts):
        raise UnsafeArchive(f"Unsicherer Eintrag im Archiv: {member.filename}")
    return relative


def content_digest(files: SkillFiles) -> str:
    digest = hashlib.sha256()
    for relative in sorted(files, key=PurePosixPath.as_posix):
        content = files[relative]
        digest.update(relative.as_posix().encode("utf-8") + b"\0")
        digest.update(len(content).to_bytes(8, "big") + content)
    return digest.hexdigest()


def install(staging: Path, destination: Path, cache: Path) -> None:
    # Die Vorfassung wandert in den Cache: Unter ~/.claude/skills würde Claude sie als zweiten Skill laden.
    if destination.exists():
        shutil.move(destination, backup_path(cache / "security-audit-vorher"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(staging, destination)
    # Erst nach vollständigem Kopieren: Ein abgebrochener Umzug soll nicht als fertig gelten.
    (destination / MARKER).write_text(REVISION + "\n", encoding="utf-8")

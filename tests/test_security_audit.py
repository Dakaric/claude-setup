import stat
import sys
import zipfile

import pytest

from installer import downloads
from installer.components import rules, security_audit
from installer.platform import cache_dir

PREFIX = security_audit.SKILL_PREFIX.as_posix()
SKILL_FILES = {f"{PREFIX}/SKILL.md": "---\nname: security-audit\n---\n", f"{PREFIX}/HUNTING.md": "Jagd"}


def fake_download(monkeypatch, entries, symlinks=()):
    def download(url, path):
        assert url == security_audit.ARCHIVE_URL
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w") as bundle:
            bundle.writestr("security-audit-skill-x/README.md", "außerhalb des Skills")
            for name, content in entries.items():
                bundle.writestr(name, content)
            for name in symlinks:
                link = zipfile.ZipInfo(name)
                link.external_attr = (stat.S_IFLNK | 0o777) << 16
                bundle.writestr(link, "/etc/passwd")
    monkeypatch.setattr(downloads, "download", download)


def test_installs_only_the_skill_folder_with_revision_marker(ctx, monkeypatch):
    fake_download(monkeypatch, SKILL_FILES)
    result = security_audit.apply(ctx)
    target = security_audit.skill_dir(ctx)
    assert result.status == "erledigt"
    assert sorted(path.name for path in target.iterdir()) == [".claude-setup-revision", "HUNTING.md", "SKILL.md"]
    assert security_audit.is_done(ctx)


def test_update_moves_previous_version_into_cache(ctx, monkeypatch):
    fake_download(monkeypatch, SKILL_FILES)
    target = security_audit.skill_dir(ctx)
    target.mkdir(parents=True)
    (target / security_audit.MARKER).write_text("alt\n", encoding="utf-8")
    security_audit.apply(ctx)
    assert security_audit.is_done(ctx)
    assert list(target.parent.iterdir()) == [target]
    assert list(cache_dir("claude-setup", ctx).glob("security-audit-vorher.sicherung-*"))


def test_own_installation_stays_untouched(ctx, monkeypatch):
    fake_download(monkeypatch, SKILL_FILES)
    target = security_audit.skill_dir(ctx)
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text("eigene Fassung", encoding="utf-8")
    result = security_audit.apply(ctx)
    assert result.status == "handarbeit"
    assert (target / "SKILL.md").read_text(encoding="utf-8") == "eigene Fassung"


@pytest.mark.skipif(sys.platform == "win32", reason="Symlinks brauchen unter Windows Sonderrechte")
def test_symlinked_installation_stays_untouched(ctx, monkeypatch, tmp_path):
    fake_download(monkeypatch, SKILL_FILES)
    own_clone = tmp_path / "klon"
    own_clone.mkdir()
    target = security_audit.skill_dir(ctx)
    target.parent.mkdir(parents=True)
    target.symlink_to(own_clone, target_is_directory=True)
    assert security_audit.apply(ctx).status == "handarbeit"
    assert target.is_symlink()


@pytest.mark.parametrize("name", [f"{PREFIX}/../../boese.md", f"{PREFIX}/C:boese.md", f"{PREFIX}/a\\..\\boese.md"])
def test_unsafe_archive_paths_are_rejected(ctx, monkeypatch, name):
    fake_download(monkeypatch, {**SKILL_FILES, name: "x"})
    with pytest.raises(security_audit.UnsafeArchive):
        security_audit.apply(ctx)
    assert not security_audit.skill_dir(ctx).exists()


def test_symlink_in_archive_is_rejected(ctx, monkeypatch):
    fake_download(monkeypatch, SKILL_FILES, symlinks=(f"{PREFIX}/link.md",))
    with pytest.raises(security_audit.UnsafeArchive):
        security_audit.apply(ctx)


def test_oversized_archive_is_rejected(ctx, monkeypatch):
    oversized = "x" * (security_audit.MAX_SKILL_BYTES + 1)
    fake_download(monkeypatch, {**SKILL_FILES, f"{PREFIX}/gross.md": oversized})
    with pytest.raises(security_audit.UnsafeArchive):
        security_audit.apply(ctx)


def test_archive_without_skill_is_rejected(ctx, monkeypatch):
    fake_download(monkeypatch, {})
    with pytest.raises(security_audit.UnsafeArchive):
        security_audit.apply(ctx)
    assert not security_audit.skill_dir(ctx).exists()


def test_rules_mention_the_skill_only_when_selected(ctx):
    assert "security-audit" not in rules.render(ctx)
    ctx.values["selected:security-audit"] = "1"
    assert "security-audit" in rules.render(ctx)

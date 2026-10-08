import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugins/toolkit/skills"
EXPECTED = {
    "email-entwurf", "github-aufgaben", "obsidian-notiz", "projekt-start",
    "social-media-post", "website-aenderung", "website-texte-seo",
    "handoff-pause", "vermenschlichen",
}


def skill_files():
    files = list(SKILLS.glob("*/SKILL.md"))
    assert {path.parent.name for path in files} == EXPECTED
    return files


def test_every_skill_has_name_and_description():
    for path in skill_files():
        text = path.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        frontmatter = text.split("---", 2)[1]
        for key in ("name", "description"):
            assert re.search(rf"^{key}:\s*\S.+$", frontmatter, re.M)


def test_skill_names_match_folders():
    for path in skill_files():
        name = re.search(r"^name: (.+)$", path.read_text(encoding="utf-8"), re.M)
        assert name.group(1) == path.parent.name


def test_marketplace_points_to_toolkit():
    data = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    plugin = ROOT / data["plugins"][0]["source"]
    metadata = json.loads((plugin / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    assert data["name"] == "claude-setup"
    assert metadata["name"] == "toolkit"
    assert metadata["version"] == "2.0.0"
    servers = json.loads((plugin / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]
    assert set(servers) == {"context7", "playwright"}


def test_marketplace_and_plugin_use_owner_name():
    owner = "Daka" + "ric"
    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    plugin = json.loads((ROOT / "plugins/toolkit/.claude-plugin/plugin.json").read_text(encoding="utf-8"))
    assert marketplace["owner"] == {"name": owner}
    assert plugin["author"] == {"name": owner}


def test_skill_paths_resolve():
    for path in skill_files():
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if "://" not in target and not target.startswith("#"):
                assert (path.parent / target.split("#")[0]).is_file(), target
        for target in re.findall(r"`(\./[^`]+)`", text):
            assert (path.parent / target).exists(), target
    assert (SKILLS / "projekt-start/vorlage-CLAUDE.md").is_file()


def test_skill_descriptions_are_valid_yaml_string_values():
    for path in skill_files():
        text = path.read_text(encoding="utf-8")
        description = re.search(r"^description: (.+)$", text, re.M).group(1)
        if description.startswith('"'):
            assert isinstance(json.loads(description), str)
        else:
            assert ": " not in description and " #" not in description, path

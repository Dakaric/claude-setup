import ast
import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PERSONAL_TERMS = (
    "chri" "stian", "lan" "ger", "dan" "iel", "har" "ry", "chris" "_brain",
    "chris" "-brain", "koe" "mpf", "kö" "mpf", "ae" "nd", "æ" "nd",
    "/us" "ers/", "jar" "vis", "daka" "ric",
)
DASH_ASIDE = re.compile(r"\u2014|\s\u2013\s|\D\u2013|\u2013\D")
# Diese eine Quelldatei erklärt das unerwünschte Muster anhand wörtlicher Beispiele.
DASH_ALLOWLIST = {"plugins/toolkit/skills/vermenschlichen/SKILL.md"}
PUBLIC_REPOSITORIES = "(?:claude-setup|obsidian-setup|vault-search-mcp|claude-code-statusline)"
OWNER = "Daka" + "ric"
REFERENCE_START = r"(?<![\w./:@-])"
REFERENCE_DELIMITER = r"$|[\s\"'`<>),;\]]"


def repository_files():
    output = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT, check=True, capture_output=True, encoding="utf-8",
    ).stdout
    files = [ROOT / name for name in output.split("\0") if name and name != "uv.lock"]
    assert files
    return files


def test_text_files_use_explicit_utf8():
    for folder in ("installer", "tests"):
        for path in (ROOT / folder).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue
                if node.func.attr not in {"read_text", "write_text"}:
                    continue
                encoding = next((keyword.value for keyword in node.keywords if keyword.arg == "encoding"), None)
                assert isinstance(encoding, ast.Constant) and encoding.value == "utf-8", f"{path}:{node.lineno}"


def without_owner_metadata(text, relative):
    field = {
        ".claude-plugin/marketplace.json": "owner",
        "plugins/toolkit/.claude-plugin/plugin.json": "author",
    }.get(relative)
    if field:
        metadata = json.loads(text)
        if metadata.get(field, {}).get("name") == OWNER:
            metadata[field]["name"] = "owner"
        return json.dumps(metadata, ensure_ascii=False)
    return text


def without_public_owner(text, relative):
    text = without_owner_metadata(text, relative)
    repository = re.escape(OWNER) + "/" + PUBLIC_REPOSITORIES
    url = REFERENCE_START + r"https://github\.com/" + repository + rf"(?:\.git)?(?=/|{REFERENCE_DELIMITER})"
    text = re.sub(url, "public-repository", text)
    text = re.sub(REFERENCE_START + repository + rf"(?={REFERENCE_DELIMITER})", "public-repository", text)
    if relative == "LICENSE":
        text = re.sub(r"^Copyright \(c\) \d{4} " + OWNER + r"$", "", text, flags=re.M)
    if relative == "pyproject.toml":
        text = re.sub(r'^authors = \[\{name = "' + OWNER + r'"\}\]$', "", text, flags=re.M)
    if relative == "installer/github.py":
        text = re.sub(r'^GITHUB_OWNER = "' + OWNER + r'"$', "", text, flags=re.M)
    return text


def personal_terms(text, relative):
    text = without_public_owner(text, relative)
    matches = []
    for term in PERSONAL_TERMS:
        pattern = re.escape(term)
        # Die kurzen Markenbegriffe dürfen normale deutsche Wörter nicht treffen.
        if term in {"ae" "nd", "æ" "nd"}:
            pattern = r"(?<!\w)" + pattern + r"(?!\w)"
        if re.search(pattern, text.casefold()):
            matches.append(term)
    return matches


def dash_violation(text, relative):
    return relative not in DASH_ALLOWLIST and bool(DASH_ASIDE.search(text))


def test_no_personal_terms():
    assert personal_terms("Beispiel " + "CHRI" + "STIAN", "example.md")
    assert personal_terms("Daka" + "ric", "example.md")
    assert not personal_terms("https://github.com/Dakaric/claude-setup", "example.md")
    for path in repository_files():
        assert not personal_terms(path.read_text(encoding="utf-8"), path.relative_to(ROOT).as_posix()), path


def test_no_dash_as_aside():
    assert dash_violation("Text \u2014 Einschub", "example.md")
    assert dash_violation("Text \u2013 Einschub", "other/SKILL.md")
    assert not dash_violation("Text \u2013 Einschub", next(iter(DASH_ALLOWLIST)))
    assert not dash_violation("3\u20135", "example.md")
    for path in repository_files():
        if path.suffix in {".md", ".py", ".json"}:
            assert not dash_violation(path.read_text(encoding="utf-8"), path.relative_to(ROOT).as_posix()), path


def test_personal_terms_in_urls_are_not_generally_exempt():
    assert personal_terms("https://github.com/" + "dan" + "iel/project", "example.md")
    assert personal_terms("https://github.com/" + OWNER + "/har" + "ry", "example.md")


@pytest.mark.parametrize("repo", ["claude-setup", "obsidian-setup", "vault-search-mcp", "claude-code-statusline"])
@pytest.mark.parametrize("prefix,suffix", [("", ""), ("https://github.com/", ""), ("https://github.com/", ".git"), ("https://github.com/", "/releases/latest")])
def test_owner_guard_allows_only_public_repositories(repo, prefix, suffix):
    assert not personal_terms(prefix + "Daka" + "ric/" + repo + suffix, "example.md")


@pytest.mark.parametrize("value", [
    "https://github.com/{owner}", "https://github.com/{owner}/private-repo",
    "https://github.com/{owner}/claude-setup-evil",
    "https://github.com/{owner}/claude-setup.git.evil",
    "https://example.com/{owner}/claude-setup", "{owner}/private-repo",
])
def test_owner_guard_rejects_other_references(value):
    assert personal_terms(value.format(owner="Daka" + "ric"), "example.md")


@pytest.mark.parametrize("relative,field", [
    (".claude-plugin/marketplace.json", "owner"),
    ("plugins/toolkit/.claude-plugin/plugin.json", "author"),
])
def test_owner_guard_allows_metadata_name_only(relative, field):
    name = "Daka" + "ric"
    metadata = {field: {"name": name}}
    assert not personal_terms(json.dumps(metadata), relative)
    assert personal_terms(json.dumps(metadata), "example.json")
    metadata["description"] = name
    assert personal_terms(json.dumps(metadata), relative)


def test_metadata_guard_preserves_other_personal_terms():
    metadata = {"owner": {"name": OWNER}, "description": "kö" + "mpf"}
    assert personal_terms(json.dumps(metadata, ensure_ascii=False), ".claude-plugin/marketplace.json")

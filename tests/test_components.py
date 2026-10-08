import json
import subprocess
from pathlib import Path

import pytest


def test_existing_claude_md_is_not_overwritten(ctx):
    from installer.components import rules
    path = ctx.home / ".claude/CLAUDE.md"
    path.parent.mkdir(parents=True)
    path.write_text("Eigene Regeln", encoding="utf-8")
    result = rules.apply(ctx)
    assert result.status == "handarbeit"
    assert path.read_text() == "Eigene Regeln"
    assert "Test" in path.with_name("CLAUDE.md.neu").read_text()
    assert rules.is_done(ctx)


def test_rules_include_only_selected_features(ctx):
    from installer.components import rules
    plain = rules.render(ctx)
    assert all(word not in plain for word in ("brainstorming", "grill-with-docs", "ctxQ", "Vault"))
    ctx.values.update({"plugin:superpowers@superpowers-dev": "1",
                       "plugin:mattpocock-skills@mattpocock": "1", "selected:statuszeile": "1",
                       "vault": str(ctx.home / "Mein Vault")})
    enriched = rules.render(ctx)
    assert all(word in enriched for word in ("brainstorming", "grill-with-docs", "ctxQ", "Mein Vault"))


def test_rules_collect_name_address_language(ctx, monkeypatch):
    from installer.components import rules
    ctx.assume_yes = False
    ctx.values.clear()
    answers = iter(["Alex", "sie", "Französisch"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    rules.prepare(ctx)
    text = rules.render(ctx)
    assert all(word in text for word in ("Alex", "Sie", "Französisch"))


def test_settings_merge_keeps_user_permissions(ctx):
    from installer.components import settings
    from installer.fsutil import read_json, write_json
    path = ctx.home / ".claude/settings.json"
    write_json(path, {"permissions": {"allow": ["Custom"]}, "env": {"OWN": "yes"}, "hooks": {"Stop": []}})
    settings.apply(ctx)
    settings.apply(ctx)
    data = read_json(path, {})
    assert data["permissions"]["allow"].count("Custom") == 1
    assert "Bash(git status:*)" in data["permissions"]["allow"]
    assert data["env"] == {"OWN": "yes", "ENABLE_PROMPT_CACHING_1H": "1"}
    assert data["hooks"] == {"Stop": []}
    assert list(path.parent.glob("settings.json.sicherung-*"))


@pytest.mark.parametrize("platform,relative", [
    ("macos", "Library/Application Support/Claude/claude_desktop_config.json"),
    ("windows", "Roaming/Claude/claude_desktop_config.json"),
])
def test_desktop_config_path_per_platform(ctx, monkeypatch, platform, relative):
    from installer.components import claude_desktop
    ctx.platform = platform
    monkeypatch.setenv("APPDATA", str(ctx.home / "Roaming"))
    assert claude_desktop.config_path(ctx) == ctx.home / relative


def test_desktop_without_vault_only_adds_context7(ctx, commands):
    from installer.components import claude_desktop
    from installer.fsutil import read_json, write_json
    path = claude_desktop.config_path(ctx)
    write_json(path, {"mcpServers": {"own": {"command": "mine"}}})
    claude_desktop.apply(ctx)
    claude_desktop.apply(ctx)
    assert set(read_json(path, {})["mcpServers"]) == {"own", "context7"}


def test_desktop_windows_store_is_manual(ctx, monkeypatch, commands):
    from installer.components import claude_desktop
    ctx.platform = "windows"
    monkeypatch.setenv("APPDATA", str(ctx.home / "Roaming"))
    result = claude_desktop.apply(ctx)
    assert result.status == "handarbeit"
    assert "Store" in result.detail
    assert not claude_desktop.config_path(ctx).exists()


def test_statusline_unsupported_on_windows():
    from installer.components import statusline
    assert statusline.supported("windows").state == "nein"


def test_statusline_needs_jq(ctx, monkeypatch):
    from installer.components import statusline
    monkeypatch.setattr("installer.shell.which", lambda name: None if name == "jq" else name)
    result = statusline.apply(ctx)
    assert result.status == "handarbeit"
    assert "jq" in result.detail and "https://" in result.detail


def test_statusline_download_and_yes_argument(ctx, commands, monkeypatch):
    from installer.components import statusline
    from installer import downloads
    def download(url, path):
        assert url == "https://github.com/Dakaric/claude-code-statusline/releases/latest/download/install.sh"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("exit 0")
    monkeypatch.setattr(downloads, "download", download)
    result = statusline.apply(ctx)
    assert result.status == "erledigt"
    assert any(cmd[0] == "bash" and cmd[-1] == "--yes" for cmd, _ in commands)


def test_missing_prerequisite_is_manual_step(ctx, monkeypatch):
    from installer.components import toolkit
    monkeypatch.setattr("installer.shell.which", lambda name: None if name in {"node", "npx"} else name)
    result = toolkit.apply(ctx)
    assert result.status == "handarbeit"
    assert "Node.js" in result.detail


def test_toolkit_installs_official_marketplace(ctx, commands):
    from installer.components import toolkit
    assert toolkit.apply(ctx).status == "erledigt"
    calls = [cmd for cmd, _ in commands]
    assert ["claude", "plugin", "marketplace", "add", "Dakaric/claude-setup"] in calls
    assert ["claude", "plugin", "install", "toolkit@claude-setup", "--scope", "user"] in calls


def test_toolkit_second_run_recognizes_install(ctx):
    from installer.components import toolkit
    from installer.fsutil import write_json
    write_json(ctx.home / ".claude/plugins/installed_plugins.json", {
        "version": 2, "plugins": {"toolkit@claude-setup": [{"scope": "user", "installPath": "plugin"}]}})
    assert toolkit.is_done(ctx)


def test_external_plugins_ask_individually(ctx, commands, monkeypatch):
    from installer.components import external_plugins
    ctx.assume_yes = False
    answers = iter(["j", "n", "j"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    external_plugins.prepare(ctx)
    result = external_plugins.apply(ctx)
    assert result.status == "erledigt"
    installed = [cmd[3] for cmd, _ in commands if cmd[:3] == ["claude", "plugin", "install"]]
    assert installed == ["superpowers@superpowers-dev", "mattpocock-skills@mattpocock"]


def test_external_plugin_failure_continues(ctx, commands, monkeypatch):
    from installer.components import external_plugins
    def run(cmd, **kwargs):
        commands.append((cmd, kwargs))
        if "superpowers@superpowers-dev" in cmd:
            raise subprocess.CalledProcessError(1, cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")
    monkeypatch.setattr(subprocess, "run", run)
    external_plugins.prepare(ctx)
    assert external_plugins.apply(ctx).status == "fehler"
    assert any("mattpocock-skills@mattpocock" in cmd for cmd, _ in commands)


def test_claude_code_windows_no_git_is_success(ctx, commands, monkeypatch):
    from installer.components import claude_code
    ctx.platform = "windows"
    monkeypatch.setattr("installer.shell.which", lambda name: None if name == "git" else name)
    result = claude_code.apply(ctx)
    assert result.status == "erledigt"
    assert "Git" in result.detail
    assert any(cmd[0] == "powershell" for cmd, _ in commands)


def test_tools_offer_git_on_windows(ctx, commands, monkeypatch):
    from installer.components import tools
    ctx.platform = "windows"
    monkeypatch.setattr("installer.shell.which", lambda name: None if name == "git" else name)
    result = tools.apply(ctx)
    assert result.status == "handarbeit"
    assert any("Git.Git" in cmd and "--accept-package-agreements" in cmd for cmd, _ in commands)


def test_tools_linux_provides_links(ctx, monkeypatch):
    from installer.components import tools
    ctx.platform = "linux"
    monkeypatch.setattr("installer.shell.which", lambda _: None)
    result = tools.apply(ctx)
    assert result.status == "handarbeit"
    assert "nodejs.org" in result.detail and "git-scm.com" in result.detail


def test_vault_search_needs_vault(ctx, commands):
    from installer.components import vault_search
    result = vault_search.apply(ctx)
    assert result.status == "handarbeit"
    assert "--vault" in result.detail
    assert commands == []


def test_vault_search_done_uses_list(ctx, commands, monkeypatch):
    from installer.components import vault_search
    def run(cmd, **kwargs):
        commands.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, "vault-search: verbunden", "")
    monkeypatch.setattr(subprocess, "run", run)
    assert vault_search.is_done(ctx)
    assert [cmd for cmd, _ in commands] == [["claude", "mcp", "list"]]


def test_paths_with_spaces_and_umlauts(ctx, commands):
    from installer.components import vault_search, claude_desktop
    from installer.fsutil import read_json
    vault = ctx.home / "Mein Vault/07 Anhänge"
    vault.mkdir(parents=True)
    ctx.values["vault"] = str(vault)
    assert vault_search.apply(ctx).status == "erledigt"
    cmd, options = next((cmd, options) for cmd, options in commands if "--vault" in cmd)
    assert cmd[cmd.index("--vault") + 1] == str(vault)
    assert "--yes" in cmd
    assert "--project" in cmd
    assert "PYTHONPATH" in options["env"]
    assert options["capture_output"] is False
    claude_desktop.apply(ctx)
    args = read_json(claude_desktop.config_path(ctx), {})["mcpServers"]["filesystem"]["args"]
    assert str(vault) in args


def test_child_interactive_preserves_stdio(ctx, commands):
    from installer.components import obsidian
    ctx.assume_yes = False
    ctx.values["vault"] = str(ctx.home / "Neuer Vault")
    assert obsidian.apply(ctx).status == "erledigt"
    cmd, options = next((cmd, options) for cmd, options in commands if "--vault" in cmd)
    assert "--yes" not in cmd
    assert "stdin" not in options and options["capture_output"] is False
    assert "--no-project" in cmd


def test_child_updates_existing_checkout(ctx, commands):
    from installer.components import obsidian
    from installer.platform import cache_dir
    checkout = cache_dir("claude-setup", ctx) / "obsidian-setup"
    (checkout / ".git").mkdir(parents=True)
    ctx.values["vault"] = str(ctx.home / "Vault")
    obsidian.apply(ctx)
    assert ["git", "-C", str(checkout), "pull", "--ff-only"] in [cmd for cmd, _ in commands]


def test_download_failure_is_reported(ctx, monkeypatch):
    from installer.components import claude_code, settings
    from installer.run import run_components
    from urllib.error import URLError
    monkeypatch.setattr("installer.shell.which", lambda name: name if name == "bash" else None)
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: (_ for _ in ()).throw(URLError("offline")))
    results = run_components([claude_code, settings], ctx, None)
    assert [result.status for result in results] == ["fehler", "erledigt"]
    assert "Download" in results[0].detail


def test_github_token_and_rate_limit(tmp_path, monkeypatch):
    from installer.downloads import download, DownloadError
    from urllib.error import HTTPError
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    def denied(request, **kwargs):
        assert request.get_header("Authorization") == "Bearer test-token"
        raise HTTPError(request.full_url, 403, "Forbidden", {"X-RateLimit-Remaining": "0"}, None)
    monkeypatch.setattr("urllib.request.urlopen", denied)
    with pytest.raises(DownloadError, match="Rate-Limit"):
        download("https://api.github.com/repos/example/repo/releases/latest", tmp_path / "out")


def test_rtk_hook_preserves_user_hooks_and_excludes_diff(ctx, commands, monkeypatch):
    from installer.components import rtk
    from installer.fsutil import read_json, write_json
    config = ctx.home / "RTK/config.toml"
    config.parent.mkdir(parents=True)
    config.write_text('[hooks]\nexclude_commands = ["git status"]\n\n[other]\nenabled = true\n')
    def run(cmd, **kwargs):
        commands.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, "Config: " + str(config) if cmd[1:] == ["config"] else "", "")
    monkeypatch.setattr(subprocess, "run", run)
    settings = ctx.home / ".claude/settings.json"
    write_json(settings, {"hooks": {"Stop": [{"hooks": []}]}})
    assert rtk.apply(ctx).status == "erledigt"
    rtk.apply(ctx)
    data = read_json(settings, {})
    assert "Stop" in data["hooks"]
    assert len(data["hooks"]["PreToolUse"]) == 1
    import tomllib
    parsed = tomllib.loads(config.read_text())
    assert parsed["hooks"]["exclude_commands"] == ["git status", "git diff"]
    assert parsed["other"]["enabled"] is True
    assert "TOKEN_OPTIMIZER_BASH_COMPRESS" not in data.get("env", {})


def test_compression_disabled_only_when_both_installed(ctx, commands):
    from installer.components import rtk
    from installer.fsutil import read_json, write_json
    write_json(ctx.home / ".claude/plugins/installed_plugins.json", {"version": 2, "plugins": {
        "token-optimizer@alexgreensh-token-optimizer": [{"scope": "user"}]}})
    rtk.apply(ctx)
    assert read_json(ctx.home / ".claude/settings.json", {})["env"]["TOKEN_OPTIMIZER_BASH_COMPRESS"] == "0"


def test_no_unfilled_placeholders(ctx, commands):
    from installer.components import rules, settings, claude_desktop
    ctx.values["vault"] = str(ctx.home / "Mein Vault")
    for module in (rules, settings, claude_desktop):
        module.apply(ctx)
    for path in ctx.home.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            for placeholder in ("__NAME__", "__VAULT__", "__HOME__", "{name}"):
                assert placeholder not in text


@pytest.mark.parametrize("fail", [False, True])
def test_statusline_preserves_user_settings_after_external_installer(ctx, commands, monkeypatch, fail):
    from installer.components import statusline
    from installer import downloads
    from installer.fsutil import read_json, write_json
    path = ctx.home / ".claude/settings.json"
    original = {"statusLine": {"type": "command", "command": "my-status"},
                "permissions": {"allow": ["Own"]}, "env": {"OWN": "yes"}}
    write_json(path, original)
    monkeypatch.setattr(downloads, "download", lambda *args: None)
    def external(cmd, **kwargs):
        write_json(path, {"statusLine": {"type": "command", "command": "new-status"}, "new": True})
        if fail:
            raise subprocess.CalledProcessError(1, cmd)
        return subprocess.CompletedProcess(cmd, 0)
    monkeypatch.setattr(subprocess, "run", external)
    if fail:
        with pytest.raises(subprocess.CalledProcessError):
            statusline.apply(ctx)
    else:
        statusline.apply(ctx)
    actual = read_json(path, {})
    assert actual["statusLine"]["command"] == "my-status"
    assert actual["permissions"] == original["permissions"]
    assert actual["env"] == original["env"]
    assert actual["new"] is True


def test_cli_returns_one_for_failed_component(ctx, monkeypatch):
    from installer import cli
    from test_core import component
    monkeypatch.setattr(Path, "home", lambda: ctx.home)
    def fail(ctx):
        raise OSError("offline")
    monkeypatch.setattr(cli, "COMPONENTS", (component("failed", apply=fail),))
    assert cli.main(["--yes"]) == 1


def test_rate_limit_does_not_stop_other_components(ctx, monkeypatch):
    from installer.components import statusline, settings
    from installer.run import run_components
    from urllib.error import HTTPError
    monkeypatch.setattr("installer.shell.which", lambda name: name)
    def denied(*args, **kwargs):
        raise HTTPError("https://github.com/example", 403, "Forbidden", {"X-RateLimit-Remaining": "0"}, None)
    monkeypatch.setattr("urllib.request.urlopen", denied)
    results = run_components([statusline, settings], ctx, None)
    assert [result.status for result in results] == ["fehler", "erledigt"]
    assert "Rate-Limit" in results[0].detail


def test_only_rules_do_not_add_external_references(ctx, monkeypatch):
    from installer.cli import main
    monkeypatch.setattr(Path, "home", lambda: ctx.home)
    assert main(["--yes", "--only", "regeln", "--name", "Alex"]) == 0
    text = (ctx.home / ".claude/CLAUDE.md").read_text()
    assert all(word not in text for word in ("brainstorming", "grill-with-docs", "ctxQ", "Vault"))


def test_desktop_keeps_existing_server_command_and_arguments(ctx, commands):
    from installer.components import claude_desktop
    from installer.fsutil import read_json, write_json
    ctx.values["vault"] = str(ctx.home / "Neuer Vault")
    path = claude_desktop.config_path(ctx)
    server = {"command": "node", "args": ["/opt/server/dist/index.js", "/alter/vault"], "env": {"OWN": "1"}}
    write_json(path, {"mcpServers": {"filesystem": server}})
    result = claude_desktop.apply(ctx)
    assert read_json(path, {})["mcpServers"]["filesystem"] == server
    assert "context7" in read_json(path, {})["mcpServers"]
    assert result.status == "handarbeit"
    assert "filesystem" in result.detail


def test_desktop_existing_vault_change_is_reported(ctx, commands):
    from installer.components import claude_desktop
    from installer.fsutil import read_json
    ctx.values["vault"] = str(ctx.home / "Alter Vault")
    claude_desktop.apply(ctx)
    ctx.values["vault"] = str(ctx.home / "Neuer Vault")
    assert not claude_desktop.is_done(ctx)
    result = claude_desktop.apply(ctx)
    args = read_json(claude_desktop.config_path(ctx), {})["mcpServers"]["filesystem"]["args"]
    assert args == ["-y", "@modelcontextprotocol/server-filesystem", str(ctx.home / "Alter Vault")]
    assert result.status == "handarbeit"


def test_explicit_vault_is_always_checked_by_child(ctx, commands, monkeypatch):
    from installer.components import vault_search
    ctx.values["vault"] = str(ctx.home / "Anderer Vault")
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 0, "vault-search: verbunden", ""))
    assert not vault_search.is_done(ctx)


def test_rtk_unusual_valid_config_is_manual(ctx, commands, monkeypatch):
    from installer.components import rtk
    config = ctx.home / "rtk.toml"
    config.parent.mkdir(parents=True)
    original = 'hooks = { exclude_commands = [] }\n'
    config.write_text(original)
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 0, "Config: " + str(config), ""))
    result = rtk.apply(ctx)
    assert result.status == "handarbeit"
    assert "git diff" in result.detail
    assert config.read_text() == original


def test_statusline_restores_settings_after_corrupt_external_output(ctx, commands, monkeypatch):
    from installer.components import statusline
    from installer.fsutil import read_json, write_json
    path = ctx.home / ".claude/settings.json"
    write_json(path, {"own": "behalten"})
    monkeypatch.setattr("installer.downloads.download", lambda *args: None)
    def external(cmd, **kwargs):
        path.write_text('{"broken":')
        return subprocess.CompletedProcess(cmd, 0)
    monkeypatch.setattr(subprocess, "run", external)
    with pytest.raises(json.JSONDecodeError):
        statusline.apply(ctx)
    assert read_json(path, {}) == {"own": "behalten"}

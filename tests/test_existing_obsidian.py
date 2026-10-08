import json

import pytest


@pytest.fixture
def obsidian(monkeypatch):
    from installer import shell
    from installer.components import obsidian
    monkeypatch.setattr(obsidian, "app_paths", lambda ctx: [])
    monkeypatch.setattr(shell, "which", lambda name: None)
    return obsidian


def write_vault_list(ctx, *vaults):
    config = ctx.home / "Library/Application Support/obsidian/obsidian.json"
    config.parent.mkdir(parents=True)
    records = {f"id{index}": {"path": str(vault)} for index, vault in enumerate(vaults)}
    config.write_text(json.dumps({"vaults": records}), encoding="utf-8")


def test_missing_obsidian_launches_child(ctx, obsidian, commands, monkeypatch):
    from installer import shell
    monkeypatch.setattr(shell, "which", lambda name: None if name == "obsidian" else name)
    ctx.values["vault"] = str(ctx.home / "Neuer Vault")
    obsidian.prepare(ctx)
    assert obsidian.apply(ctx).status == "erledigt"
    assert any("--vault" in cmd for cmd, _ in commands)


def test_existing_obsidian_only_takes_vault_path(ctx, obsidian, monkeypatch):
    vault = ctx.home / "Mein Vault"
    vault.mkdir(parents=True)
    write_vault_list(ctx, vault)
    launched = []
    monkeypatch.setattr(obsidian.children, "launch", lambda *args: launched.append(args))
    ctx.values["vault"] = str(vault)
    obsidian.prepare(ctx)
    result = obsidian.apply(ctx)
    assert result.status == "übersprungen"
    assert str(vault) in result.detail
    assert launched == []
    assert "entfällt" in obsidian.plan(ctx)[0]


def test_existing_obsidian_asks_only_for_path(ctx, obsidian, monkeypatch):
    vault = ctx.home / "Mein Vault"
    vault.mkdir(parents=True)
    write_vault_list(ctx, vault)
    questions = []
    ctx.assume_yes = False
    monkeypatch.setattr("builtins.input", lambda question: questions.append(question) or "")
    obsidian.prepare(ctx)
    assert questions == [f"Pfad zu deinem Vault? [{vault}] "]
    assert ctx.values["vault"] == str(vault.resolve())


def test_several_known_vaults_have_no_default(ctx, obsidian, monkeypatch):
    write_vault_list(ctx, ctx.home / "Erster", ctx.home / "Zweiter")
    ctx.assume_yes = False
    questions = []
    monkeypatch.setattr("builtins.input", lambda question: questions.append(question) or "")
    obsidian.prepare(ctx)
    assert questions == ["Pfad zu deinem Vault? [] "]
    assert "vault" not in ctx.values


def test_existing_obsidian_needs_existing_vault(ctx, obsidian):
    write_vault_list(ctx)
    ctx.values["vault"] = str(ctx.home / "Gibt es nicht")
    obsidian.prepare(ctx)
    result = obsidian.apply(ctx)
    assert result.status == "handarbeit"
    assert "existiert nicht" in result.detail


def test_app_without_vault_list_counts_as_installed(ctx, obsidian, monkeypatch):
    app = ctx.home / "Applications/Obsidian.app"
    app.mkdir(parents=True)
    monkeypatch.setattr(obsidian, "app_paths", lambda ctx: [app])
    assert obsidian.is_installed(ctx)
    app.rmdir()
    assert not obsidian.is_installed(ctx)


def test_status_lists_only_existing_vaults(ctx, obsidian, monkeypatch, capsys):
    from installer import cli
    vault = ctx.home / "Mein Vault"
    vault.mkdir(parents=True)
    write_vault_list(ctx, vault, ctx.home / "Gelöscht")
    monkeypatch.setattr(cli.Path, "home", lambda: ctx.home)
    monkeypatch.setattr(cli.platform, "detect", lambda: "macos")
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: False)
    assert cli.main(["--obsidian-status"]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status == {"installiert": True, "vaults": [str(vault)]}

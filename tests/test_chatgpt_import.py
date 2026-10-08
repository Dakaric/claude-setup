import re

from installer.components import chatgpt_import, rules


def test_skill_is_copied_with_prompt(ctx):
    result = chatgpt_import.apply(ctx)
    destination = chatgpt_import.skill_dir(ctx)
    assert result.status == "erledigt"
    assert (destination / "SKILL.md").is_file()
    assert (destination / "prompt-fuer-chatgpt.md").is_file()
    assert chatgpt_import.is_done(ctx)


def test_changed_copy_is_not_done(ctx):
    chatgpt_import.apply(ctx)
    (chatgpt_import.skill_dir(ctx) / "SKILL.md").write_text("alt", encoding="utf-8")
    assert not chatgpt_import.is_done(ctx)
    chatgpt_import.apply(ctx)
    assert chatgpt_import.is_done(ctx)


def test_foreign_skill_stays_untouched(ctx):
    destination = chatgpt_import.skill_dir(ctx)
    destination.mkdir(parents=True)
    (destination / "SKILL.md").write_text("eigener Skill", encoding="utf-8")
    assert chatgpt_import.apply(ctx).status == "handarbeit"
    assert (destination / "SKILL.md").read_text(encoding="utf-8") == "eigener Skill"


def test_skill_name_and_prompt_link():
    text = (chatgpt_import.SOURCE / "SKILL.md").read_text(encoding="utf-8")
    assert re.search(r"^name: chatgpt-umzug$", text, re.M)
    for target in re.findall(r"\]\(([^)]+)\)", text):
        assert (chatgpt_import.SOURCE / target).is_file()


def test_prompt_never_asks_for_secrets():
    prompt = (chatgpt_import.SOURCE / "prompt-fuer-chatgpt.md").read_text(encoding="utf-8")
    assert "keine Passwörter" in prompt
    assert "(unsicher)" in prompt
    assert "## Gespeicherte Erinnerungen (wörtlich)" in prompt


def test_rules_offer_import_only_when_selected(ctx):
    assert "chatgpt-umzug" not in rules.render(ctx)
    ctx.values["selected:chatgpt-umzug"] = "1"
    assert "chatgpt-umzug" in rules.render(ctx)

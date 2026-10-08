from .. import ui
from ..config import ROOT
from ..fsutil import backup
from ..model import Context, Platform, Result, Support

KEY = "regeln"
TITLE = "Grundregeln"
DESCRIPTION = "Name, Anrede, Sprache und gemeinsame Arbeitsregeln"
DEFAULT = True


def supported(platform: Platform) -> Support:
    return Support("ja")


def prepare(ctx: Context) -> None:
    for key, question, default in (("name", "Wie heißt du?", "Nutzer"),
                                   ("anrede", "Welche Anrede: du oder sie?", "du"),
                                   ("language", "In welcher Sprache antworten?", "Deutsch")):
        if not ctx.values.get(key):
            ctx.values[key] = ui.ask_text(question, default, ctx)
    if ctx.values["anrede"].lower() not in {"du", "sie"}:
        raise ValueError("Die Anrede muss du oder sie sein.")


def render(ctx: Context) -> str:
    content = (ROOT / "templates/CLAUDE.md").read_text(encoding="utf-8").format(
        name=ctx.values.get("name", "Nutzer"), language=ctx.values.get("language", "Deutsch"),
        address="Sie" if ctx.values.get("anrede", "du").lower() == "sie" else "du")
    extras = []
    if ctx.values.get("vault"):
        extras.append(f"Notizen liegen im Obsidian-Vault unter `{ctx.values['vault']}`. Lies dort zuerst die CLAUDE.md.")
    if ctx.values.get("plugin:superpowers@superpowers-dev") == "1":
        extras.append("Kläre größere Vorhaben mit dem Skill brainstorming und schreibe dann einen Plan.")
    if ctx.values.get("plugin:mattpocock-skills@mattpocock") == "1":
        extras.append("Prüfe größere Pläne mit dem Skill grill-with-docs vor der Umsetzung.")
    if ctx.values.get("selected:security-audit") == "1":
        extras.append("Prüfe Änderungen an Anmeldung, Rechten, Zugangsdaten oder Eingaben von außen vor dem Abschluss "
                      "mit dem Skill security-audit. Den vollständigen Audit nur auf ausdrückliche Bitte, er startet viele Agents.")
    if ctx.values.get("selected:chatgpt-umzug") == "1":
        extras.append("Biete an, das Wissen aus ChatGPT mit dem Skill chatgpt-umzug zu übernehmen. "
                      "Nach erfolgreicher Übernahme entfernt der Skill diese Zeile.")
    if ctx.values.get("selected:statuszeile") == "1":
        extras.append("Zeigt ctxQ unter 90, biete nach dem nächsten abgeschlossenen Schritt eine Übergabe und /clear an.")
    return content + "".join(f"- {line}\n" for line in extras)


def is_done(ctx: Context) -> bool:
    desired = render(ctx)
    path = ctx.home / ".claude/CLAUDE.md"
    return any(candidate.exists() and candidate.read_text(encoding="utf-8") == desired
               for candidate in (path, path.with_name("CLAUDE.md.neu")))


def plan(ctx: Context) -> list[str]:
    return [f"Grundregeln nach {ctx.home / '.claude/CLAUDE.md'} schreiben; bestehende Regeln erhalten eine separate .neu-Datei."]


def apply(ctx: Context) -> Result:
    path = ctx.home / ".claude/CLAUDE.md"
    existing = path.exists()
    if existing:
        path = path.with_name("CLAUDE.md.neu")
    path.parent.mkdir(parents=True, exist_ok=True)
    backup(path)
    path.write_text(render(ctx), encoding="utf-8")
    return Result(KEY, "handarbeit" if existing else "erledigt",
                  f"{path} mit den vorhandenen Regeln vergleichen." if existing else str(path))

---
name: obsidian-notiz
description: "Arbeitet mit dem Obsidian-Vault (Zweites Gehirn): Notizen anlegen, Inbox einsortieren, verknüpfen, suchen, zusammenfassen, Daily Note führen, Kontext-Profil pflegen. Verwenden, sobald es um Notizen, den Vault, Obsidian, „schreib das auf\" oder „was weiß ich über …\" geht."
---

# Obsidian-Vault

Der Vault-Pfad steht in `~/.claude/CLAUDE.md`. Lies zuerst die `CLAUDE.md` im Vault: sie ist maßgeblich für Ordner und Regeln. Für Obsidian-Syntax, `.base`- und `.canvas`-Dateien die Skills in `<Vault>/.claude/skills/` nutzen.

## Wohin gehört was

Lies die Ordnerzuordnung und Regeln für private Bereiche aus der `CLAUDE.md` im Vault. Wenn sie fehlen, frage nach dem Zielordner.

## Notiz anlegen

1. Erst suchen (`grep -ril`), vorhandene Notiz ergänzen statt Dopplung.
2. Dateiname: `Beschreibender Name.md`, mit Leerzeichen, ohne `/ \ : * ? " < > |`.
3. Frontmatter: `tags`, `date`, bei Projekten `status`.
4. Mit `[[Wikilinks]]` verknüpfen; nur auf vorhandene Notizen oder die fehlende gleich anlegen.
5. Kurz sagen, wo die Notiz liegt und warum dort.

## Texte, Mails, Angebote

Vorher `00 Kontext/` lesen (Über mich, Angebot, ICP, Schreibstil, Branding). Sind die Dateien leer: anbieten, sie per kurzem Interview zu füllen.

## Suchen und beantworten

Aus dem Vault antworten und Quellen als `[[Verweis]]` nennen. Was nicht im Vault steht, klar als Allgemeinwissen kennzeichnen. Private Bereiche nur auf ausdrückliche Nachfrage öffnen.

## Inbox einsortieren

Je Notiz Zielordner vorschlagen, erst nach Zustimmung mit `git mv` verschieben. Nie löschen, kürzen oder archivieren ohne ausdrückliche Bitte.

## Sichern

Prüfe, ob und wie die Sicherung im Vault eingerichtet ist. Push nach GitHub gemäß Skill `github-aufgaben`.

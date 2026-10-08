---
name: projekt-start
description: "Richtet ein neues oder bestehendes Projekt für die Arbeit mit Claude ein (CLAUDE.md, Git, .gitignore). Verwenden, wenn der Nutzer ein neues Projekt beginnt oder Claude einen Projektordner zum ersten Mal sieht."
---

# Projekt einrichten

1. Sieh dir den Ordner an: Welche Technik, wie startet man die Vorschau, wie wird veröffentlicht? Lies `README`, `package.json` und Konfigurationsdateien.
2. Frage nur nach, was sich daraus nicht ergibt: Zweck des Projekts, Zielgruppe, Tonfall, wo es live läuft.
3. Lege `CLAUDE.md` im Projektordner an. Nutze als Gerüst die Vorlage [vorlage-CLAUDE.md](./vorlage-CLAUDE.md) im eigenen Skill-Ordner und fülle sie mit echten Angaben. Unbekanntes weglassen statt raten.
4. Falls noch kein Git: `git init`, sinnvolle `.gitignore` (mindestens `.env*`, `node_modules/`, `.DS_Store`, Build-Ordner), erster Commit.
5. Prüfe, dass keine Passwörter oder Schlüssel im Code stehen. Falls doch: den Nutzer darauf hinweisen, nicht committen.
6. Kurze Zusammenfassung in einfacher Sprache: was das Projekt ist, wie man es startet, was als Nächstes sinnvoll wäre.

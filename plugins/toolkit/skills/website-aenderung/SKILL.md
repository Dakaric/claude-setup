---
name: website-aenderung
description: "Sicherer Ablauf für Änderungen am Code der Webseite (Texte, Bilder, Seiten, Design, Fehler). Verwenden, sobald an der Webseite etwas geändert, ergänzt oder repariert werden soll."
---

# Änderung an der Webseite

Erkläre in einfacher Sprache, wenn der Nutzer nicht programmiert. Nenne Dateien nur, wenn es zum Verständnis beiträgt.

## Ablauf

1. **Verstehen**: Lies `CLAUDE.md` im Projekt und finde die betroffene Stelle. Ist unklar, welche Seite oder welcher Abschnitt gemeint ist, frage einmal kurz nach.
2. **Sichern**: Prüfe mit `git status`, ob ungespeicherte Änderungen vorliegen. Lege für die Änderung einen eigenen Branch an (`git switch -c aenderung/<kurzname>`).
3. **Ändern**: Nimm nur die gewünschte Änderung vor. Kein Umbau nebenbei, keine neuen Abhängigkeiten ohne Rückfrage.
4. **Prüfen**: Starte die lokale Vorschau (Befehl steht in `CLAUDE.md` oder `package.json`) und sieh dir die Seite mit dem Playwright-Browser an, auch in Handy-Breite. Führe vorhandene Prüfungen aus (Build, Lint).
5. **Zeigen**: Fasse in zwei, drei Sätzen zusammen, was sich geändert hat, und nenne die Vorschau-Adresse.
6. **Speichern**: Committe mit einer verständlichen deutschen Nachricht.
7. **Veröffentlichen**: Nur nach ausdrücklichem „Ja" vom Nutzer pushen, mergen oder live stellen.

## Nie ohne Rückfrage

- Dateien oder Seiten löschen
- Passwörter, Schlüssel oder `.env`-Dateien anfassen
- Direkt auf `main` pushen oder live stellen
- `git push --force`, `git reset --hard`

---
name: handoff-pause
description: "Beendet eine lange Sitzung sauber: wartet laufende Arbeit ab, schreibt einen Übergabezettel und sagt, wie es nach /clear weitergeht. Verwenden bei „handoff\", „Pause\", „Übergabe\", „neu anfangen\" oder wenn die Statuszeile ctxQ unter 90 zeigt."
argument-hint: "Woran soll die nächste Sitzung weiterarbeiten? (optional)"
---

# Handoff-Pause

Ziel: Die Sitzung kann danach mit `/clear` geleert werden, und die nächste Sitzung findet alles in einer Datei. `/clear` tippt immer der Nutzer selbst.

## Wann anbieten

Zeigt die Statuszeile `ctxQ` unter 90, wird das Gespräch zu lang, und Claude arbeitet spürbar ungenauer. Dann einmal anbieten, eine Handoff-Pause zu machen. Nicht bei jeder Antwort nachhaken. Der richtige Moment ist nach einem abgeschlossenen Schritt, nicht mitten in einer Änderung.

## 1. Laufende Arbeit abwarten

Laufen noch Subagents oder Befehle im Hintergrund: dem Nutzer in einer Zeile sagen, worauf du wartest, und die Ergebnisse abwarten. Nichts abbrechen, nichts Neues starten. Einen angefangenen Schritt erst sauber zu Ende bringen.

## 2. Übergabezettel schreiben

Schreibe diese vier Angaben direkt in die Übergabe:

- Stand: erledigte Arbeit, Prüfungen und aktueller Branch; endet mit „bereit für /clear“.
- Offene Entscheidungen: nächste Aufgaben und noch nötige Antworten.
- Fallen: relevante Risiken, fehlgeschlagene Ansätze und Voraussetzungen.
- Startzeile: genauer Satz für die nächste Sitzung, etwa „Lies `<Pfad>` und arbeite dort weiter.“

Ablage: `docs/handoffs/JJJJ-MM-TT-handoff-<stichwort>.md` im aktuellen Projekt. Lege den Ordner bei Bedarf an.

## 3. Melden

Genau diese zwei Zeilen an den Nutzer, danach nichts mehr tun:

```text
Übergabe steht: <vollständiger Pfad>
Jetzt /clear eintippen, danach: <Startzeile>
```

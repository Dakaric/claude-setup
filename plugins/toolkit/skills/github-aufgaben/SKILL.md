---
name: github-aufgaben
description: "Erledigt GitHub-Aufgaben direkt im Terminal mit git und gh: Repo anlegen, klonen, sichern/pushen, Stand holen, Pull Requests, Issues. Verwenden bei allem, was GitHub, Repo, Sicherung, Backup, Push oder Pull betrifft."
---

# GitHub per Befehl

Alles läuft über `git` und `gh` im Terminal. Nicht den Browser, nicht die GitHub-App, kein MCP-Server. Bitte den Nutzer nicht, etwas auf github.com anzuklicken, wenn es einen Befehl dafür gibt.

## Vor der ersten Aufgabe

```bash
gh auth status
```

Nicht angemeldet → den Nutzer bitten, im Terminal `gh auth login` auszuführen (GitHub.com → HTTPS → „Login with a web browser"). Das ist der einzige Schritt, den er selbst machen muss. Danach `gh auth setup-git`.

## Häufige Aufgaben

| Aufgabe | Befehl |
|---|---|
| Ordner als neues privates Repo sichern | `gh repo create <name> --private --source=. --push` |
| Repo holen | `gh repo clone <besitzer>/<name>` |
| Stand sichern | `git add -A && git commit -m "…" && git push` |
| Neuesten Stand holen | `git pull --rebase` |
| Änderung vorschlagen | `git switch -c <branch>` … `gh pr create --fill` |
| Pull Request ansehen / übernehmen | `gh pr view`, `gh pr merge --squash` |
| Aufgabe notieren | `gh issue create --title "…" --body "…"` |

## Regeln

- Neue Repos immer **privat**, außer es wird ausdrücklich „öffentlich" gesagt.
- Vor `push`, `merge`, `repo create` kurz sagen, was passiert, und Zustimmung abwarten.
- Vor jedem Commit `git status` prüfen: keine `.env`, Schlüssel oder Passwörter.
- Nie `git push --force`, `git reset --hard` oder `gh repo delete` ohne ausdrückliche Bitte.
- Bei Konflikten nicht raten: erklären, was kollidiert, und fragen, welche Fassung gilt.

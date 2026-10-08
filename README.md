# Claude einrichten

Dieses Repo richtet Claude Code mit Grundregeln, Einstellungen, Skills und optionalen Erweiterungen ein. Du wählst die Bausteine im Terminal. Vorhandene Einstellungen bleiben erhalten. Obsidian und die semantische Vault-Suche haben eigene Installer, die du von hier aus starten kannst.

Du brauchst eine Internetverbindung für Downloads und einen passenden Claude-Zugang. Der Installer meldet dich nicht automatisch an. Nach der Installation: `claude auth login`.

## Installation

Lade dieses Repo als ZIP von [GitHub](https://github.com/Dakaric/claude-setup) herunter und entpacke es. Alternativ: `git clone https://github.com/Dakaric/claude-setup.git`. Öffne ein Terminal im Repo-Ordner und starte einen Befehl.

macOS oder Linux:

```bash
bash ./install.sh
```

Windows, in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Die Starthilfe installiert [uv](https://docs.astral.sh/uv/), wenn es fehlt. uv stellt Python 3.12 bereit. Unter Windows ergänzt die Starthilfe den PATH für die laufende Sitzung. Programme, die winget installiert, sind unter Umständen erst in einem neuen Terminal verfügbar.

Wenn Claude Code schon läuft: Öffne Claude im Repo-Ordner und sage **„Führe die Einrichtung aus“**. Die CLAUDE.md erklärt Claude, welche Angaben nötig sind und wie es die gewählten Bausteine ohne Terminaldialog startet.

## Bausteine

| Schlüssel | Zweck | macOS | Linux | Windows | Standard |
|---|---|---|---|---|---|
| `werkzeuge` | Git, Node.js, gh, jq | Homebrew oder Links | Links | winget oder Links | ja |
| `claude-code` | Offizieller Claude-Code-Installer | ja | ja | ja | ja |
| `regeln` | Name, Anrede, Sprache und Arbeitsregeln | ja | ja | ja | ja |
| `einstellungen` | Berechtigungen und einstündiger Prompt-Cache | ja | ja | ja | ja |
| `toolkit` | Neun Skills, Context7, Playwright | ja | ja | ja | ja |
| `plugins-extern` | Drei weitere Plugins, einzeln wählbar | ja | ja | ja | ja |
| `security-audit` | Skill für Sicherheitsprüfungen von Cloudflare, fester Stand | ja | ja | ja | ja |
| `statuszeile` | Kontextanzeige | ja | ja | nein, benötigt bash und jq | ja |
| `rtk` | Kürzere Terminal-Ausgaben | Homebrew oder Link | vorhandenes RTK, Homebrew oder Link | nein | ja |
| `claude-desktop` | MCP-Server für die Desktop-App | ja | nein, keine offizielle App | ja, Standard-Konfigurationsordner | nein |
| `obsidian` | Eigenen Obsidian-Installer starten | ja | ja | ja | nein |
| `vault-suche` | Eigenen Installer für die Vault-Suche starten | ja | ja | ja | nein |

„Ja“ bezeichnet die vorgesehene Unterstützung. Die CI prüft die Logik mit ersetzten Downloads und Prozessen auf allen drei Systemen. Eine echte Installation der Fremdprogramme wird dort nicht ausgeführt.

Das Toolkit und die Desktop-MCP-Server brauchen Node.js mit `npx`. Claude Code selbst braucht unter Windows kein Git für die Installation; Git für Windows wird für das Bash-Werkzeug empfohlen. Die Statuszeile braucht außerdem `curl`. Ohne Homebrew unter macOS oder winget unter Windows nennt der Installer Links für fehlende Werkzeuge.

## Auswahl und Probelauf

Nur den Plan anzeigen, ohne Programme zu starten, Dateien zu schreiben oder Downloads auszuführen:

```bash
bash ./install.sh --dry-run --yes --name "Alex"
```

Die Starthilfe selbst kann dabei uv und Python bereitstellen, falls sie noch fehlen. Ist uv bereits eingerichtet, geht der reine Offline-Probelauf direkt:

```bash
uv run --offline --python 3.12 python -m installer --dry-run --yes --name "Alex"
```

Nur Grundregeln und Einstellungen:

```bash
bash ./install.sh --yes --only regeln,einstellungen --name "Alex" --anrede sie --language Deutsch
```

Obsidian und Suche für einen gemeinsamen Vault:

```bash
bash ./install.sh --only obsidian,vault-suche --vault "$HOME/Dokumente/Mein Vault"
```

Unter Windows dieselben Schalter über `powershell -ExecutionPolicy Bypass -File ./install.ps1` übergeben, zum Beispiel `--only regeln,einstellungen --vault "D:\Notizen\Mein Vault"`. Der Aufruf mit `-File` übergibt die Kommaliste korrekt als einzelnes Argument. Er funktioniert auch in Git Bash, das Claude Code unter Windows nutzt. Die Pfade werden als einzelne Argumente weitergereicht; Leerzeichen und Umlaute bleiben erhalten.

`--yes` verwendet Standardantworten. Zusammen mit `--only` sind die genannten Bausteine ausdrücklich gewählt, auch wenn sie sonst standardmäßig abgewählt sind. Bei `plugins-extern` wählt `--yes` alle drei Plugins. Für eine Einzelauswahl diesen Baustein interaktiv starten. Ohne TTY ist `--yes` erforderlich. `--language` hat den Alias `--sprache`. Der Vault-Pfad muss absolut sein; relative Pfade werden mit Exit-Code 2 abgelehnt. Ein führendes `~` wird zum Benutzerordner aufgelöst.

## Vorhandene Einrichtung

Vor einer Änderung erstellt der Installer eine Sicherung mit dem Zusatz `.sicherung-JJJJMMTT-HHMMSS`. Bei mehreren Sicherungen in derselben Sekunde kommt eine Nummer hinzu. JSON-Objekte werden zusammengeführt, Listen ohne zusätzliche Duplikate ergänzt. Bei widersprüchlichen Einzelwerten gewinnt deine bisherige Einstellung.

Eine vorhandene globale `~/.claude/CLAUDE.md` bleibt bestehen. Der Vorschlag landet daneben als `CLAUDE.md.neu`; vergleiche beide Dateien selbst. Zusatzregeln für brainstorming, grill-with-docs und die Kontextanzeige erscheinen nur, wenn du den jeweiligen Baustein gewählt hast. Die Vault-Zeile erscheint nur mit bekanntem Pfad.

Der RTK-Hook ergänzt `PreToolUse` für Bash. Der Installer fragt RTK selbst nach seinem Konfigurationspfad und nimmt `git diff` von der Kürzung aus. Ist das Format unbekannt, nennt er die nötige Handarbeit. Die Bash-Komprimierung von Token Optimizer wird nur deaktiviert, wenn RTK und Token Optimizer vorhanden sind; ein ausdrücklich vorhandener Nutzerwert bleibt erhalten.

Desktop erhält Context7 und mit Vault-Pfad zusätzlich den Filesystem-Server für genau diesen Ordner. Eigene Server bleiben erhalten. Weicht ein bereits vorhandener gleichnamiger Server ab, bleibt seine vollständige Definition erhalten und der Installer meldet Handarbeit; Befehlsargumente werden nicht vermischt. Unter Windows wird `%APPDATA%\Claude` verwendet. Fehlt der Ordner, gibt es einen Hinweis auf die Store-Fassung und die Konfiguration in der App. Danach Desktop neu starten.

Die anderen Repos werden in `~/.cache/claude-setup` abgelegt, unter Windows in `%LOCALAPPDATA%\claude-setup\cache`. Vorhandene Klone werden mit `git pull --ff-only` aktualisiert. Die Unterinstaller übernehmen das Terminal und erhalten bei Bedarf `--yes`. Beachte auch ihre Zusammenfassung, insbesondere Hinweise auf nötige Handarbeit. Die Vault-Suche prüft eine vorhandene Registrierung mit `claude mcp list`. Mit ausdrücklich bekanntem Vault wird der Unterinstaller erneut gestartet, damit er die Zuordnung zu diesem Vault prüfen kann.

Bei einem Fehler läuft der nächste Baustein weiter. Exit-Code 0 bedeutet: keine technischen Fehler; Handarbeit kann noch offen sein. Exit 1 meldet mindestens einen fehlgeschlagenen Baustein, Exit 2 einen ungültigen Aufruf. Bei GitHub-Rate-Limits kannst du später erneut starten oder `GITHUB_TOKEN` setzen. Der Installer gibt diesen Token nicht aus.

## Herkunft

Der Installer lädt Fremdcode während der Einrichtung. Die jeweiligen Lizenzen gelten zusätzlich zur MIT-Lizenz dieses Repos.

| Erweiterung | Quelle | Hinweis |
|---|---|---|
| Toolkit | dieses Repo | eigene Skills und MCP-Konfiguration |
| Superpowers | [obra/superpowers](https://github.com/obra/superpowers) | Arbeitsabläufe für Entwicklung |
| Token Optimizer | [alexgreensh/token-optimizer](https://github.com/alexgreensh/token-optimizer) | **PolyForm-Noncommercial**, für kommerzielle Nutzung Lizenz prüfen |
| Skills von Matt Pocock | [mattpocock/skills](https://github.com/mattpocock/skills) | Plugin `mattpocock-skills@mattpocock` |
| Context7 | [upstash/context7](https://github.com/upstash/context7) | Dokumentation über MCP |
| Playwright | [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | Browser über MCP |
| Filesystem | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | Dateizugriff für Desktop |
| Statuszeile | [claude-code-statusline](https://github.com/Dakaric/claude-code-statusline) | Kontextanzeige |
| RTK | [rtk-ai/rtk](https://github.com/rtk-ai/rtk) | kürzt Terminal-Ausgaben |
| Obsidian-Setup | [obsidian-setup](https://github.com/Dakaric/obsidian-setup) | separater Einrichtungsassistent |
| Vault-Suche | [vault-search-mcp](https://github.com/Dakaric/vault-search-mcp) | separater MCP-Server mit Installer |

## Skills in Claude Desktop

Das Toolkit enthält `email-entwurf`, `github-aufgaben`, `obsidian-notiz`, `projekt-start`, `social-media-post`, `website-aenderung`, `website-texte-seo`, `handoff-pause` und `vermenschlichen`.

Für den manuellen Upload packst du den gewünschten Ordner aus `plugins/toolkit/skills/` als ZIP. Das Archiv enthält den Skill-Ordner mit seiner `SKILL.md` und allen Begleitdateien. Bei `projekt-start` gehört `vorlage-CLAUDE.md` dazu. Öffne die Skills-Verwaltung in Claude Desktop und lade das ZIP als eigenen Skill hoch, sofern dein Konto diese Funktion anbietet. Das Repo liefert keine fertigen ZIP-Dateien. Ein Skill-Upload richtet keine MCP-Server ein.

## Entwicklung und Tests

```bash
uv run --offline --python 3.12 pytest -q
uv run --offline --python 3.12 python -m installer --dry-run --yes --name Test
```

Für den ersten Testlauf müssen die Entwicklungspakete im uv-Cache liegen; bei erlaubtem Netz einmal `uv sync` ausführen. Python-Installer-Code verwendet nur die Standardbibliothek. Tests sperren Netzaufrufe und ersetzen Installationsprozesse.

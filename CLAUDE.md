# Einrichtungsassistent

Wenn der Nutzer „Führe die Einrichtung aus“ sagt:

1. Lies README.md und zeige die verfügbaren Bausteine samt Plattformgrenzen. Frage, welche eingerichtet werden sollen. Bei `plugins-extern` erkläre die drei Plugins und die nichtkommerzielle Lizenz des Token Optimizers. Der nichtinteraktive Aufruf wählt innerhalb dieses Bausteins alle drei Plugins. Bei `security-audit` erkläre, dass der Skill von Cloudflare stammt (MIT-Lizenz). Zusammen mit `regeln` prüft Claude damit vor dem Abschluss geänderten Code an Anmeldung, Rechten, Zugangsdaten und Eingaben von außen; den vollständigen Audit mit vielen Agents startet der Skill nur auf ausdrückliche Bitte.
   Frage, ob der Nutzer bisher mit ChatGPT gearbeitet hat. Wenn ja, wähle `chatgpt-umzug`: Der Skill gibt einen Prompt für ChatGPT aus und übernimmt dessen Antwort nach Rückfrage in Claude.
2. Frage nach Name, Anrede (`du` oder `sie`) und Antwortsprache. Für Obsidian und die Vault-Suche brauchst du einen absoluten Vault-Pfad. Frag nicht danach, sondern lies ihn selbst aus: `bash ./install.sh --obsidian-status`, unter Windows `powershell -ExecutionPolicy Bypass -File ./install.ps1 --obsidian-status`. Die Ausgabe ist JSON mit `installiert` und `vaults`.
   - Ein Vault: übernimm ihn und nenne dem Nutzer den Pfad.
   - Mehrere Vaults: lass den Nutzer einen davon wählen.
   - Keiner: frage nach einem Pfad für einen neuen Vault. Die Suche braucht einen vorhandenen Vault, Obsidian kann einen neuen anlegen.
   Ist `installiert` wahr, entfällt die Obsidian-Einrichtung: Der Baustein `obsidian` übernimmt dann nur den Pfad. Wähle ihn trotzdem, wenn der Nutzer Obsidian nutzen will, und übergib den Pfad mit `--vault`.
3. Rufe im Repo die Starthilfe mit `--yes`, `--only` und genau den gewählten Schlüsseln auf. Übergib auch `--name`, `--anrede`, `--language` und, falls bekannt, `--vault`. Claudes Shell hat kein TTY. Verwende eine Argumentliste, wenn die Umgebung sie unterstützt; sonst zitiere Werte passend zur Shell.
4. Unter macOS/Linux: `bash ./install.sh --yes --only regeln,einstellungen --name "Alex" --anrede du --language Deutsch`. Claude Code nutzt unter Windows Git Bash: `powershell -ExecutionPolicy Bypass -File ./install.ps1 --yes --only regeln,einstellungen --name "Alex" --anrede du --language Deutsch`. Ersetze die Beispielauswahl durch die tatsächliche Auswahl.
5. Fasse Ergebnisse und noch nötige Handarbeit zusammen. Für einen vorher gewünschten Probelauf ergänze `--dry-run`.

## Entwicklung

Der Installer benötigt nur die Python-Standardbibliothek, mindestens Python 3.12. Tests: `uv run --offline --python 3.12 pytest -q`. Netz und Installationsprozesse müssen in Tests ersetzt werden. Erhalte bestehende Nutzerkonfigurationen und sichere Dateien vor Änderungen. Unterprozesse als Argumentlisten, kein `shell=True`. Rekursiv löschen ausschließlich mit `installer.fsutil.safe_rmtree` unterhalb des Installer-Caches.

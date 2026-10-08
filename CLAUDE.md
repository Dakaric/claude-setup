# Einrichtungsassistent

Wenn der Nutzer „Führe die Einrichtung aus“ sagt:

1. Lies README.md und zeige die verfügbaren Bausteine samt Plattformgrenzen. Frage, welche eingerichtet werden sollen. Bei `plugins-extern` erkläre die drei Plugins und die nichtkommerzielle Lizenz des Token Optimizers. Der nichtinteraktive Aufruf wählt innerhalb dieses Bausteins alle drei Plugins.
2. Frage nach Name, Anrede (`du` oder `sie`) und Antwortsprache. Für Obsidian und die Vault-Suche frage nach einem absoluten Vault-Pfad. Die Suche braucht einen vorhandenen Vault, Obsidian kann einen neuen anlegen.
3. Rufe im Repo die Starthilfe mit `--yes`, `--only` und genau den gewählten Schlüsseln auf. Übergib auch `--name`, `--anrede`, `--language` und, falls bekannt, `--vault`. Claudes Shell hat kein TTY. Verwende eine Argumentliste, wenn die Umgebung sie unterstützt; sonst zitiere Werte passend zur Shell.
4. Unter macOS/Linux: `bash ./install.sh --yes --only regeln,einstellungen --name "Alex" --anrede du --language Deutsch`. Claude Code nutzt unter Windows Git Bash: `powershell -ExecutionPolicy Bypass -File ./install.ps1 --yes --only regeln,einstellungen --name "Alex" --anrede du --language Deutsch`. Ersetze die Beispielauswahl durch die tatsächliche Auswahl.
5. Fasse Ergebnisse und noch nötige Handarbeit zusammen. Für einen vorher gewünschten Probelauf ergänze `--dry-run`.

## Entwicklung

Der Installer benötigt nur die Python-Standardbibliothek, mindestens Python 3.12. Tests: `uv run --offline --python 3.12 pytest -q`. Netz und Installationsprozesse müssen in Tests ersetzt werden. Erhalte bestehende Nutzerkonfigurationen und sichere Dateien vor Änderungen. Unterprozesse als Argumentlisten, kein `shell=True`. Rekursiv löschen ausschließlich mit `installer.fsutil.safe_rmtree` unterhalb des Installer-Caches.

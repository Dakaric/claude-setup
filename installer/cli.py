import argparse
import sys
from pathlib import Path

from . import platform, ui
from .components import COMPONENTS
from .model import Context
from .paths import absolute_vault_path
from .run import run_components


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Claude und lokale Werkzeuge einrichten")
    result.add_argument("--yes", action="store_true", help="Standardantworten verwenden")
    result.add_argument("--only", help="Nur diese Bausteine, durch Kommas getrennt")
    result.add_argument("--dry-run", action="store_true", help="Nur den Plan anzeigen")
    result.add_argument("--name", help="Name für die Grundregeln")
    result.add_argument("--anrede", choices=("du", "sie"), help="Anrede, Standard: du")
    result.add_argument("--language", "--sprache", dest="language", help="Antwortsprache, Standard: Deutsch")
    result.add_argument("--vault", help="Absoluter Pfad zum Obsidian-Vault")
    return result


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    if not sys.stdin.isatty() and not args.yes:
        print("Ohne Terminal bitte --yes und bei Bedarf --only verwenden.")
        return 2
    only = {key.strip() for key in args.only.split(",")} if args.only is not None else None
    if only is not None and (unknown := only - {component.KEY for component in COMPONENTS}):
        print("Unbekannte Bausteine: " + ", ".join(sorted(unknown)))
        return 2
    try:
        ctx = Context(platform.detect(), Path.home(), args.dry_run, args.yes, {})
        for key in ("name", "anrede", "language"):
            if value := getattr(args, key):
                ctx.values[key] = value
        if args.vault is not None:
            ctx.values["vault"] = absolute_vault_path(args.vault)
        results = run_components(COMPONENTS, ctx, only)
    except (ValueError, OSError, EOFError) as error:
        print(f"Einrichtung abgebrochen: {error}")
        return 2
    ui.print_summary(results)
    return 1 if any(result.status == "fehler" for result in results) else 0

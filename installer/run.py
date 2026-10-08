from . import ui
from .model import Context, Result
from .paths import InvalidVaultPath


def select_components(components, ctx: Context, only: set[str] | None):
    selected, results = [], {}
    for component in components:
        if only is not None and component.KEY not in only:
            continue
        try:
            support = component.supported(ctx.platform)
            print(f"\n{component.TITLE}: {component.DESCRIPTION} ({support.state})")
            if support.reason:
                print(support.reason)
            if support.state == "nein":
                results[component.KEY] = Result(component.KEY, "nicht unterstützt", support.reason)
                continue
            if not ui.ask_yes_no("Einrichten?", True if only is not None else component.DEFAULT, ctx):
                results[component.KEY] = Result(component.KEY, "übersprungen", "nicht gewählt")
                continue
            selected.append(component)
            ctx.values[f"selected:{component.KEY}"] = "1"
            if hasattr(component, "prepare"):
                component.prepare(ctx)
        except InvalidVaultPath:
            raise
        except Exception as error:
            results[component.KEY] = Result(component.KEY, "fehler", str(error))
    return selected, results


def execute_component(component, ctx: Context) -> Result:
    if not ctx.dry_run and component.is_done(ctx):
        return Result(component.KEY, "übersprungen", "schon eingerichtet")
    steps = component.plan(ctx)
    for step in steps:
        print(f"  {step}")
    if ctx.dry_run:
        return Result(component.KEY, "übersprungen", "Nur Plan: " + "; ".join(steps))
    return component.apply(ctx)


def run_components(components, ctx: Context, only: set[str] | None) -> list[Result]:
    components = tuple(components)
    selected, results = select_components(components, ctx, only)
    for component in selected:
        if component.KEY in results:
            continue
        try:
            results[component.KEY] = execute_component(component, ctx)
        except Exception as error:
            results[component.KEY] = Result(component.KEY, "fehler", str(error))
    return [results[component.KEY] for component in components if component.KEY in results]

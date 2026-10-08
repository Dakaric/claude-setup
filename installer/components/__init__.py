from types import ModuleType

from . import (
    tools, claude_code, rules, settings, toolkit, external_plugins,
    statusline, rtk, claude_desktop, obsidian, vault_search,
)

COMPONENTS: tuple[ModuleType, ...] = (
    tools, claude_code, rules, settings, toolkit, external_plugins,
    statusline, rtk, claude_desktop, obsidian, vault_search,
)

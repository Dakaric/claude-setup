from types import ModuleType

from . import (
    tools, claude_code, rules, settings, toolkit, external_plugins,
    security_audit, statusline, rtk, claude_desktop, obsidian, vault_search, chatgpt_import,
)

COMPONENTS: tuple[ModuleType, ...] = (
    tools, claude_code, rules, settings, toolkit, external_plugins,
    security_audit, statusline, rtk, claude_desktop, obsidian, vault_search, chatgpt_import,
)

from pathlib import Path


class InvalidVaultPath(ValueError):
    pass


def absolute_vault_path(value: str) -> str:
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise InvalidVaultPath("Bitte einen absoluten Vault-Pfad angeben (--vault PFAD).")
    return str(path.resolve())

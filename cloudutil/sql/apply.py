"""Apply PostgreSQL configuration (shared by CLI and Ansible)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cloudutil.sql.modules.postgres import PostgreSQLBuilder


def apply_postgres_config(
    *,
    config: dict[str, Any] | None = None,
    config_path: str | Path | None = None,
) -> tuple[bool, list[dict[str, Any]]]:
    """
    Apply CloudUtil PostgreSQL YAML config.

    Provide exactly one of ``config`` or ``config_path``.

    Returns:
        Tuple of (changed, serialized change reports).
    """
    if (config is None) == (config_path is None):
        raise ValueError("Provide exactly one of config or config_path")

    if config_path is not None:
        path = Path(config_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Config file not found: {path}")
        provider = PostgreSQLBuilder().from_yaml(path).build()
    else:
        provider = PostgreSQLBuilder().from_dict(config).build()

    with provider:
        provider.execute()

    changed = any(
        c.operation in ("create", "update", "execute") for c in provider.changes
    )
    serialized = [c.model_dump() for c in provider.changes]
    return changed, serialized


def validate_postgres_config(
    *,
    config: dict[str, Any] | None = None,
    config_path: str | Path | None = None,
) -> None:
    """
    Parse and validate config without connecting to the database.

    Provide exactly one of ``config`` or ``config_path``.
    """
    if (config is None) == (config_path is None):
        raise ValueError("Provide exactly one of config or config_path")

    if config_path is not None:
        path = Path(config_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Config file not found: {path}")
        PostgreSQLBuilder().from_yaml(path).build()
    else:
        PostgreSQLBuilder().from_dict(config).build()

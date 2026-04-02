"""Apply PostgreSQL configuration — used by the CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from cloudutil.sql.modules.base import SQLConfig
from cloudutil.sql.modules.postgres import PostgreSQLBuilder


def _resolve_path(config_path: str | Path) -> Path:
    path = Path(config_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")
    return path


def apply_postgres_config(config_path: str | Path) -> tuple[bool, list[dict[str, Any]]]:
    """
    Apply a PostgreSQL YAML config file.

    Returns:
        Tuple of (changed, serialized change reports).
    """
    provider = PostgreSQLBuilder().from_yaml(_resolve_path(config_path)).build()
    with provider:
        provider.execute()

    changed = any(
        c.operation in ("create", "update", "execute") for c in provider.changes
    )
    return changed, [c.model_dump() for c in provider.changes]


def validate_postgres_config(config_path: str | Path) -> None:
    """Parse and validate a config file without connecting to the database."""
    path = _resolve_path(config_path)
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"YAML file is empty or not a mapping: {path}")
    SQLConfig(**data)

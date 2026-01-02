from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass
from contextlib import contextmanager

import psycopg2
from psycopg2 import sql
import yaml

from cloudutil.utils import logger
from .base import (
    BaseSQLProvider,
    SQLConfig,
    DatabaseConfig,
    ExtensionConfig,
    UserConfig,
    PrivilegeConfig,
)


@dataclass
class ChangeReport:
    """Tracks what changed during execution"""

    operation: str  # 'create', 'update', 'skip'
    resource_type: str
    resource_name: str
    details: Dict = None

    def __str__(self) -> str:
        if self.operation == "create":
            return f"[CREATE] {self.resource_type}: {self.resource_name}"
        if self.operation == "skip":
            return f"[SKIP] {self.resource_type}: {self.resource_name}"
        if self.operation == "update":
            changes = ", ".join(
                [
                    f"{k}: {v['old']} → {v['new']}"
                    for k, v in (self.details or {}).items()
                ]
            )
            return f"[UPDATE] {self.resource_type}: {self.resource_name} ({changes})"
        return f"[{self.operation.upper()}] {self.resource_type}: {self.resource_name}"


class PostgreSQLProvider(BaseSQLProvider):
    """PostgreSQL provider with check-first pattern"""

    def __init__(self, config: SQLConfig):
        super().__init__(config)
        self._conn = None
        self.conn_params = None
        self.changes: List[ChangeReport] = []

    def connect(self) -> None:
        """Connect to PostgreSQL"""
        self.conn_params = {
            "host": self.config.provider.host,
            "port": self.config.provider.port,
            "user": self.config.provider.username,
            "password": self.config.provider.password,
        }
        if self.config.provider.cert:
            self.conn_params["sslmode"] = "verify-full"
            self.conn_params["sslrootcert"] = self.config.provider.cert

        self._conn = psycopg2.connect(**self.conn_params, database="postgres")
        self._conn.autocommit = True
        logger.info(
            f"Connected to {self.config.provider.host}:{self.config.provider.port}"
        )

    def disconnect(self) -> None:
        """Disconnect from PostgreSQL"""
        if self._conn:
            self._conn.close()
            self._conn = None

    @contextmanager
    def _db_conn(self, db_name: str):
        """Temporary connection to specific database"""
        conn = psycopg2.connect(**self.conn_params, database=db_name)
        conn.autocommit = True
        try:
            yield conn
        finally:
            conn.close()

    def _log(
        self,
        operation: str,
        resource_type: str,
        resource_name: str,
        details: Dict = None,
    ):
        """Track and log a change"""
        change = ChangeReport(operation, resource_type, resource_name, details)
        self.changes.append(change)
        logger.info(str(change))

    # =========================================================================
    # DATABASE
    # =========================================================================

    def create_database(self, db_config: DatabaseConfig) -> None:
        """Create or update database"""
        if not db_config.create:
            return

        cursor = self._conn.cursor()

        # Check if exists
        cursor.execute(
            "SELECT rolname FROM pg_roles WHERE oid = (SELECT datdba FROM pg_database WHERE datname = %s)",
            (db_config.name,),
        )
        result = cursor.fetchone()

        if result:
            # Database exists
            current_owner = result[0]
            expected_owner = self.config.provider.username

            if current_owner != expected_owner:
                cursor.execute(
                    sql.SQL("ALTER DATABASE {} OWNER TO {}").format(
                        sql.Identifier(db_config.name), sql.Identifier(expected_owner)
                    )
                )
                self._log(
                    "update",
                    "database",
                    db_config.name,
                    {"owner": {"old": current_owner, "new": expected_owner}},
                )
            else:
                self._log("skip", "database", db_config.name)
        else:
            # Create database
            cursor.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(db_config.name),
                    sql.Identifier(self.config.provider.username),
                )
            )
            self._log("create", "database", db_config.name)

        cursor.close()

    # =========================================================================
    # EXTENSIONS
    # =========================================================================

    def install_extensions(
        self, db_name: str, extensions: List[ExtensionConfig]
    ) -> None:
        """Install or update extensions"""
        if not extensions:
            return

        with self._db_conn(db_name) as conn:
            for ext in extensions:
                cursor = conn.cursor()

                # Check if exists
                cursor.execute(
                    "SELECT 1 FROM pg_extension WHERE extname = %s", (ext.name,)
                )
                exists = cursor.fetchone() is not None

                if exists:
                    try:
                        cursor.execute(
                            sql.SQL("ALTER EXTENSION {} UPDATE").format(
                                sql.Identifier(ext.name)
                            )
                        )
                        self._log("update", "extension", f"{db_name}.{ext.name}")
                    except Exception:
                        self._log("skip", "extension", f"{db_name}.{ext.name}")
                else:
                    cursor.execute(
                        sql.SQL("CREATE EXTENSION {}").format(sql.Identifier(ext.name))
                    )
                    self._log("create", "extension", f"{db_name}.{ext.name}")

                cursor.close()

    # =========================================================================
    # USERS
    # =========================================================================

    def create_user(self, user_config: UserConfig) -> None:
        """Create or update user"""
        cursor = self._conn.cursor()

        # Check if exists
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (user_config.name,))
        exists = cursor.fetchone() is not None

        if exists:
            cursor.execute(
                sql.SQL("ALTER USER {} WITH PASSWORD %s").format(
                    sql.Identifier(user_config.name)
                ),
                (user_config.password,),
            )
            self._log(
                "update",
                "user",
                user_config.name,
                {"password": {"old": "***", "new": "***"}},
            )
        else:
            cursor.execute(
                sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
                    sql.Identifier(user_config.name)
                ),
                (user_config.password,),
            )
            self._log("create", "user", user_config.name)

        cursor.close()

    # =========================================================================
    # PRIVILEGES
    # =========================================================================

    def grant_privileges(self, user_name: str, privilege: PrivilegeConfig) -> None:
        """Grant privileges to user"""
        with self._db_conn(privilege.db) as conn:
            cursor = conn.cursor()

            # Database and schema access
            cursor.execute(
                sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                    sql.Identifier(privilege.db), sql.Identifier(user_name)
                )
            )
            cursor.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                    sql.Identifier(privilege.db_schema), sql.Identifier(user_name)
                )
            )

            if privilege.readwrite:
                cursor.execute(
                    sql.SQL("GRANT CREATE ON SCHEMA {} TO {}").format(
                        sql.Identifier(privilege.db_schema), sql.Identifier(user_name)
                    )
                )

            # Table privileges
            schema = sql.Identifier(privilege.db_schema)
            user = sql.Identifier(user_name)

            if privilege.tables and "ALL" in privilege.tables:
                if privilege.readwrite:
                    cursor.execute(
                        sql.SQL(
                            "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {} TO {}"
                        ).format(schema, user)
                    )
                    cursor.execute(
                        sql.SQL(
                            "ALTER DEFAULT PRIVILEGES IN SCHEMA {} GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {}"
                        ).format(schema, user)
                    )
                    access = "READ/WRITE (ALL)"
                elif privilege.readonly:
                    cursor.execute(
                        sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA {} TO {}").format(
                            schema, user
                        )
                    )
                    cursor.execute(
                        sql.SQL(
                            "ALTER DEFAULT PRIVILEGES IN SCHEMA {} GRANT SELECT ON TABLES TO {}"
                        ).format(schema, user)
                    )
                    access = "READ-ONLY (ALL)"
            else:
                for table in privilege.tables:
                    if privilege.readwrite:
                        cursor.execute(
                            sql.SQL(
                                "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {}.{} TO {}"
                            ).format(schema, sql.Identifier(table), user)
                        )
                    elif privilege.readonly:
                        cursor.execute(
                            sql.SQL("GRANT SELECT ON TABLE {}.{} TO {}").format(
                                schema, sql.Identifier(table), user
                            )
                        )
                access = f"{'READ/WRITE' if privilege.readwrite else 'READ-ONLY'} ({len(privilege.tables)} tables)"

            cursor.close()
            self._log(
                "create",
                "privilege",
                f"{user_name}@{privilege.db}.{privilege.db_schema}",
                {"access": access},
            )

    # =========================================================================
    # EXECUTE
    # =========================================================================

    def execute(self) -> None:
        """Execute all configurations"""
        self.changes = []
        logger.info("Starting PostgreSQL Configuration\n")

        # Databases
        logger.info("=" * 60)
        logger.info("Databases")
        logger.info("=" * 60)
        for db in self.config.database.values():
            self.create_database(db)

        # Extensions
        logger.info("\n" + "=" * 60)
        logger.info("Extensions")
        logger.info("=" * 60)
        for db in self.config.database.values():
            if db.extensions:
                self.install_extensions(db.name, db.extensions)

        # Users
        logger.info("\n" + "=" * 60)
        logger.info("Users")
        logger.info("=" * 60)
        for user in self.config.users:
            self.create_user(user)

        # Privileges
        logger.info("\n" + "=" * 60)
        logger.info("Privileges")
        logger.info("=" * 60)
        for user in self.config.users:
            for priv in user.privileges:
                self.grant_privileges(user.name, priv)

        # Summary
        creates = sum(1 for c in self.changes if c.operation == "create")
        updates = sum(1 for c in self.changes if c.operation == "update")
        skips = sum(1 for c in self.changes if c.operation == "skip")

        logger.info("\n" + "=" * 60)
        logger.info("Summary")
        logger.info("=" * 60)
        logger.info(
            f"Total: {len(self.changes)} | Created: {creates} | Updated: {updates} | Skipped: {skips}"
        )
        logger.info("Complete")


# =============================================================================
# BUILDER
# =============================================================================


class PostgreSQLBuilder:
    """Builder for PostgreSQL provider"""

    def __init__(self):
        self._config: Optional[SQLConfig] = None

    def from_dict(self, config_dict: dict) -> "PostgreSQLBuilder":
        self._config = SQLConfig(**config_dict)
        return self

    def from_yaml(self, yaml_path: str | Path) -> "PostgreSQLBuilder":
        path = Path(yaml_path)
        if not path.exists():
            raise FileNotFoundError(f"YAML file not found: {yaml_path}")

        with open(path, "r") as f:
            config_dict = yaml.safe_load(f)

        return self.from_dict(config_dict)

    def from_yaml_string(self, yaml_string: str) -> "PostgreSQLBuilder":
        config_dict = yaml.safe_load(yaml_string)
        return self.from_dict(config_dict)

    def build(self) -> PostgreSQLProvider:
        if self._config is None:
            raise ValueError("Configuration not set")
        return PostgreSQLProvider(self._config)

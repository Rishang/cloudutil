from pathlib import Path
from typing import Optional, List

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


class PostgreSQLProvider(BaseSQLProvider):
    """PostgreSQL provider implementation"""

    def __init__(self, config: SQLConfig):
        super().__init__(config)
        self._master_connection = None
        self._db_connection = None
        self.conn_params = None

    def connect(self) -> None:
        """Establish connection to PostgreSQL server"""
        try:
            self.conn_params = {
                "host": self.config.provider.host,
                "port": self.config.provider.port,
                "user": self.config.provider.username,
                "password": self.config.provider.password,
            }

            # Add SSL cert if provided
            if self.config.provider.cert:
                self.conn_params["sslmode"] = "verify-full"
                self.conn_params["sslrootcert"] = self.config.provider.cert

            # Connect to default 'postgres' database for admin operations
            self._master_connection = psycopg2.connect(
                **self.conn_params, database="postgres"
            )
            self._master_connection.autocommit = True

            logger.info(
                f"Connected to PostgreSQL at {self.config.provider.host}:{self.config.provider.port}"
            )
        except ImportError:
            raise ImportError(
                "psycopg2-binary is required for PostgreSQL. Install it with: pip install psycopg2-binary"
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")

    def disconnect(self) -> None:
        """Close PostgreSQL connections"""
        if self._db_connection:
            self._db_connection.close()
            self._db_connection = None

        if self._master_connection:
            self._master_connection.close()
            self._master_connection = None
            logger.info("Disconnected from PostgreSQL")

    def create_database(self, db_config: DatabaseConfig) -> None:
        """Create a PostgreSQL database if not exists, alter if exists"""
        if not db_config.create:
            logger.info(
                f"Skipping database creation for '{db_config.name}' (create=false)"
            )
            return

        try:
            cursor = self._master_connection.cursor()

            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s", (db_config.name,)
            )

            if cursor.fetchone():
                logger.info(f"Database '{db_config.name}' already exists")

                # Alter database settings if needed
                cursor.execute(
                    sql.SQL("ALTER DATABASE {} OWNER TO {}").format(
                        sql.Identifier(db_config.name),
                        sql.Identifier(self.config.provider.username),
                    )
                )
                logger.debug(
                    f"Altered database '{db_config.name}' owner to '{self.config.provider.username}'"
                )
            else:
                # Create database
                cursor.execute(
                    sql.SQL("CREATE DATABASE {} OWNER {}").format(
                        sql.Identifier(db_config.name),
                        sql.Identifier(self.config.provider.username),
                    )
                )
                logger.info(f"Created database '{db_config.name}'")

            cursor.close()
        except Exception as e:
            raise RuntimeError(
                f"Failed to create/alter database '{db_config.name}': {e}"
            )

    def install_extensions(
        self, db_name: str, extensions: List[ExtensionConfig]
    ) -> None:
        """Install PostgreSQL extensions if not exists"""
        if not extensions:
            return

        try:
            # Connect to the specific database
            db_conn = psycopg2.connect(**self.conn_params, database=db_name)
            db_conn.autocommit = True
            cursor = db_conn.cursor()

            for ext in extensions:
                try:
                    # Check if extension exists
                    cursor.execute(
                        "SELECT 1 FROM pg_extension WHERE extname = %s", (ext.name,)
                    )

                    if cursor.fetchone():
                        logger.info(
                            f"Extension '{ext.name}' already exists in database '{db_name}'"
                        )
                        # Optionally update extension to latest version
                        cursor.execute(
                            sql.SQL("ALTER EXTENSION {} UPDATE").format(
                                sql.Identifier(ext.name)
                            )
                        )
                        logger.debug(
                            f"Updated extension '{ext.name}' to latest version"
                        )
                    else:
                        cursor.execute(
                            sql.SQL("CREATE EXTENSION IF NOT EXISTS {}").format(
                                sql.Identifier(ext.name)
                            )
                        )
                        logger.info(
                            f"Installed extension '{ext.name}' in database '{db_name}'"
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to install/update extension '{ext.name}': {e}"
                    )

            cursor.close()
            db_conn.close()
        except Exception as e:
            raise RuntimeError(f"Failed to manage extensions in '{db_name}': {e}")

    def create_user(self, user_config: UserConfig) -> None:
        """Create a PostgreSQL user if not exists, alter password if exists"""
        try:
            cursor = self._master_connection.cursor()

            # Check if user exists
            cursor.execute(
                "SELECT 1 FROM pg_roles WHERE rolname = %s", (user_config.name,)
            )

            if cursor.fetchone():
                logger.info(f"User '{user_config.name}' already exists")

                # Alter user password
                cursor.execute(
                    sql.SQL("ALTER USER {} WITH PASSWORD %s").format(
                        sql.Identifier(user_config.name)
                    ),
                    (user_config.password,),
                )
                logger.debug(f"Updated password for user '{user_config.name}'")
            else:
                # Create user with password
                cursor.execute(
                    sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
                        sql.Identifier(user_config.name)
                    ),
                    (user_config.password,),
                )
                logger.info(f"Created user '{user_config.name}'")

            cursor.close()
        except Exception as e:
            raise RuntimeError(f"Failed to create/alter user '{user_config.name}': {e}")

    def grant_privileges(self, user_name: str, privilege: PrivilegeConfig) -> None:
        """Grant privileges to a PostgreSQL user"""
        try:
            # Connect to the specific database
            db_conn = psycopg2.connect(**self.conn_params, database=privilege.db)
            db_conn.autocommit = True
            cursor = db_conn.cursor()

            # Grant database connection privilege
            cursor.execute(
                sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                    sql.Identifier(privilege.db), sql.Identifier(user_name)
                )
            )
            logger.debug(
                f"Granted CONNECT on database '{privilege.db}' to '{user_name}'"
            )

            # Grant schema usage and create privileges
            cursor.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                    sql.Identifier(privilege.db_schema), sql.Identifier(user_name)
                )
            )
            logger.debug(
                f"Granted USAGE on schema '{privilege.db_schema}' to '{user_name}'"
            )

            # Grant CREATE privilege on schema if user has readwrite access
            if privilege.readwrite:
                cursor.execute(
                    sql.SQL("GRANT CREATE ON SCHEMA {} TO {}").format(
                        sql.Identifier(privilege.db_schema), sql.Identifier(user_name)
                    )
                )
                logger.debug(
                    f"Granted CREATE on schema '{privilege.db_schema}' to '{user_name}'"
                )

            # Handle table privileges
            if privilege.tables and "ALL" in privilege.tables:
                # Grant on all tables
                if privilege.readwrite:
                    cursor.execute(
                        sql.SQL(
                            "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {} TO {}"
                        ).format(
                            sql.Identifier(privilege.db_schema),
                            sql.Identifier(user_name),
                        )
                    )
                    cursor.execute(
                        sql.SQL(
                            "ALTER DEFAULT PRIVILEGES IN SCHEMA {} GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {}"
                        ).format(
                            sql.Identifier(privilege.db_schema),
                            sql.Identifier(user_name),
                        )
                    )
                    logger.info(
                        f"Granted READ/WRITE on all tables in {privilege.db}.{privilege.db_schema} to '{user_name}'"
                    )
                elif privilege.readonly:
                    cursor.execute(
                        sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA {} TO {}").format(
                            sql.Identifier(privilege.db_schema),
                            sql.Identifier(user_name),
                        )
                    )
                    cursor.execute(
                        sql.SQL(
                            "ALTER DEFAULT PRIVILEGES IN SCHEMA {} GRANT SELECT ON TABLES TO {}"
                        ).format(
                            sql.Identifier(privilege.db_schema),
                            sql.Identifier(user_name),
                        )
                    )
                    logger.info(
                        f"Granted READ-ONLY on all tables in {privilege.db}.{privilege.db_schema} to '{user_name}'"
                    )
            else:
                # Grant on specific tables
                for table in privilege.tables:
                    if privilege.readwrite:
                        cursor.execute(
                            sql.SQL(
                                "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {}.{} TO {}"
                            ).format(
                                sql.Identifier(privilege.db_schema),
                                sql.Identifier(table),
                                sql.Identifier(user_name),
                            )
                        )
                        logger.info(
                            f"Granted READ/WRITE on {privilege.db}.{privilege.db_schema}.{table} to '{user_name}'"
                        )

                    elif privilege.readonly:
                        cursor.execute(
                            sql.SQL("GRANT SELECT ON TABLE {}.{} TO {}").format(
                                sql.Identifier(privilege.db_schema),
                                sql.Identifier(table),
                                sql.Identifier(user_name),
                            )
                        )
                        logger.info(
                            f"Granted READ-ONLY on {privilege.db}.{privilege.db_schema}.{table} to '{user_name}'"
                        )

            cursor.close()
            db_conn.close()
        except Exception as e:
            raise RuntimeError(
                f"Failed to grant privileges to '{user_name}' on '{privilege.db}': {e}"
            )

    def execute(self) -> None:
        """Execute all PostgreSQL configurations"""
        logger.info("Starting PostgreSQL Configuration")

        # Step 1: Create databases
        logger.info("Creating/Altering Databases")
        for db_name, db_config in self.config.database.items():
            self.create_database(db_config)

        # Step 2: Install extensions
        logger.info("Installing/Updating Extensions")
        for db_name, db_config in self.config.database.items():
            if db_config.extensions:
                self.install_extensions(db_config.name, db_config.extensions)

        # Step 3: Create users
        logger.info("Creating/Updating Users")
        for user in self.config.users:
            self.create_user(user)

        # Step 4: Grant privileges
        logger.info("Granting Privileges")
        for user in self.config.users:
            for privilege in user.privileges:
                self.grant_privileges(user.name, privilege)

        logger.info("PostgreSQL Configuration Complete")


class PostgreSQLBuilder:
    """Builder pattern for PostgreSQL provider"""

    def __init__(self):
        self._config: Optional[SQLConfig] = None

    def from_dict(self, config_dict: dict) -> "PostgreSQLBuilder":
        """Build from dictionary"""
        self._config = SQLConfig(**config_dict)
        return self

    def from_yaml(self, yaml_path: str | Path) -> "PostgreSQLBuilder":
        """Build from YAML file"""
        path = Path(yaml_path)

        if not path.exists():
            raise FileNotFoundError(f"YAML file not found: {yaml_path}")

        with open(path, "r") as f:
            config_dict = yaml.safe_load(f)

        return self.from_dict(config_dict)

    def from_yaml_string(self, yaml_string: str) -> "PostgreSQLBuilder":
        """Build from YAML string"""
        config_dict = yaml.safe_load(yaml_string)
        return self.from_dict(config_dict)

    def build(self) -> PostgreSQLProvider:
        """Build the PostgreSQL provider"""
        if self._config is None:
            raise ValueError(
                "Configuration not set. Use from_dict(), from_yaml(), or from_yaml_string() first."
            )

        return PostgreSQLProvider(self._config)

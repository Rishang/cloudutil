import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List, Optional

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, Field, field_validator, model_validator

from cloudutil.utils import resolve_env_variable


class ProviderConfig(BaseModel):
    """Base provider configuration"""

    name: str
    version: str | int
    host: str
    port: int
    username: str
    password: str
    cert: Optional[str] = None

    @field_validator("username", mode="before")
    @classmethod
    def resolve_username(cls, v: str) -> str:
        """Resolve username from environment variable if specified as ${VAR_NAME}"""
        return resolve_env_variable(v, "provider.username")

    @field_validator("password", mode="before")
    @classmethod
    def resolve_password(cls, v: str) -> str:
        """Resolve password from environment variable if specified as ${VAR_NAME}"""
        return resolve_env_variable(v, "provider.password")


class ExtensionConfig(BaseModel):
    """Database extension configuration"""

    name: str


class DatabaseConfig(BaseModel):
    """Database configuration"""

    name: str
    create: bool = True
    extensions: List[ExtensionConfig] = Field(default_factory=list)


class PrivilegeConfig(BaseModel):
    """User privilege configuration"""

    db: str
    db_schema: str = "public"
    readwrite: bool = False
    readonly: bool = False
    tables: List[str] = Field(default_factory=list)


class UserConfig(BaseModel):
    """User configuration"""

    name: str
    password: str
    privileges: List[PrivilegeConfig] = Field(default_factory=list)

    @field_validator("password", mode="before")
    @classmethod
    def resolve_password(cls, v: str) -> str:
        """Resolve password from environment variable if specified as ${VAR_NAME}"""
        return resolve_env_variable(v, "user.password")


class CustomSQLQuery(BaseModel):
    """Arbitrary SQL executed after databases, extensions, users, and privileges."""

    query: str = Field(
        ...,
        description="Jinja template source string from YAML (not the rendered SQL).",
    )
    query_raw: str = Field(
        default="",
        description="Rendered SQL used for execution and automation tasks (set in model_post_init).",
    )
    template_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Extra keyword arguments passed to render() (in addition to env globals).",
    )
    loader_path: str | list[str] = Field(
        default=".",
        description="Root path(s) for FileSystemLoader (e.g. {% include 'fragment.sql' %}).",
    )
    inject_env: bool = Field(
        default=True,
        description="If true, set env.globals['env'] = os.environ (use {{ env.VAR }} in templates).",
    )
    database: str = "postgres"
    params: List[Any] = Field(default_factory=list)
    name: Optional[str] = None

    @field_validator("query", mode="before")
    @classmethod
    def query_must_be_nonblank(cls, v: Any) -> str:
        if isinstance(v, str) and v.strip():
            return v.strip()
        raise ValueError("custom_sql.query must be a non-empty string")

    def model_post_init(self, __context: Any) -> None:
        """Compile ``query`` with a filesystem-backed Jinja Environment; set ``query_raw``."""
        searchpaths = self._resolve_loader_paths()
        jinja_env = Environment(
            loader=FileSystemLoader(searchpaths),
            autoescape=False,
        )
        if self.inject_env:
            jinja_env.globals["env"] = os.environ
        tmpl = jinja_env.from_string(self.query)
        object.__setattr__(self, "query_raw", tmpl.render(**self.template_context))

    def _resolve_loader_paths(self) -> List[str]:
        raw = self.loader_path
        paths = [raw] if isinstance(raw, str) else list(raw)
        resolved: List[str] = []
        for p in paths:
            path = Path(p).expanduser().resolve()
            if not path.is_dir():
                raise ValueError(
                    f"custom_sql.loader_path must be an existing directory: {path}"
                )
            resolved.append(str(path))
        return resolved

    @field_validator("database")
    @classmethod
    def database_not_blank(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("custom_sql.database must be a non-empty string")
        return v.strip()


class SQLConfig(BaseModel):
    """Complete SQL configuration schema"""

    provider: ProviderConfig
    database: List[DatabaseConfig] = Field(default_factory=list)
    users: List[UserConfig] = Field(default_factory=list)
    custom_sql: List[CustomSQLQuery] = Field(default_factory=list)

    @model_validator(mode="after")
    def normalize_database(self) -> "SQLConfig":
        """Convert database list to dict for internal use"""
        self.database = {db.name: db for db in self.database}
        return self


class BaseSQLProvider(ABC):
    """Abstract base class for SQL providers"""

    def __init__(self, config: SQLConfig):
        self.config = config
        self._connection = None

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the database"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection"""
        pass

    @abstractmethod
    def create_database(self, db_config: DatabaseConfig) -> None:
        """Create a database"""
        pass

    @abstractmethod
    def install_extensions(
        self, db_name: str, extensions: List[ExtensionConfig]
    ) -> None:
        """Install database extensions"""
        pass

    @abstractmethod
    def create_user(self, user_config: UserConfig) -> None:
        """Create a database user"""
        pass

    @abstractmethod
    def grant_privileges(self, user_name: str, privilege: PrivilegeConfig) -> None:
        """Grant privileges to a user"""
        pass

    @abstractmethod
    def execute(self) -> None:
        """Execute all configurations"""
        pass

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

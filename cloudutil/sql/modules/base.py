from abc import ABC, abstractmethod
from typing import Optional, List

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


class SQLConfig(BaseModel):
    """Complete SQL configuration schema"""

    provider: ProviderConfig
    database: List[DatabaseConfig] = Field(default_factory=list)
    users: List[UserConfig] = Field(default_factory=list)

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

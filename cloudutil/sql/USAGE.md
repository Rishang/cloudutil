# SQL Module Usage Guide

## Overview

The SQL module provides a flexible, type-safe way to manage database configurations using Pydantic schemas and the Builder pattern. It currently supports PostgreSQL with an extensible architecture for other database providers.

## Architecture

### Base Schema (`base.py`)

The base module defines abstract Pydantic models for SQL configurations:

- **`ProviderConfig`**: Database provider connection details
- **`DatabaseConfig`**: Database creation and extension configuration
- **`UserConfig`**: User creation and authentication
- **`PrivilegeConfig`**: User privilege management
- **`SQLConfig`**: Root configuration combining all components
- **`BaseSQLProvider`**: Abstract base class for SQL providers

### PostgreSQL Implementation (`postgres.py`)

Concrete implementation for PostgreSQL including:

- **`PostgreSQLProvider`**: Implements all database operations
- **`PostgreSQLBuilder`**: Builder pattern for flexible configuration loading

## Quick Start

### 1. Create a YAML Configuration File

#### Basic Configuration

```yaml
provider: 
  name: postgres
  version: 17
  host: localhost
  port: 5432
  cert: null  # Optional SSL certificate path
  username: postgres
  password: mysecretpassword

database:
  myapp:
    name: myapp
    create: true
    extensions:
    - name: uuid-ossp
    - name: pgcrypto

users:
- name: app_readwrite
  password: app_rw_pass
  privileges:
  - db: myapp
    db_schema: public
    readwrite: true
    readonly: false
    tables:
    - ALL
- name: app_readonly
  password: app_ro_pass
  privileges:
  - db: myapp
    db_schema: public
    readwrite: false
    readonly: true
    tables:
    - user_activity
    - users
```

#### Using Environment Variables

For sensitive data like passwords, you can use environment variables with the `${VAR_NAME}` syntax:

```yaml
provider: 
  name: postgres
  version: 17
  host: ${DB_HOST}
  port: 5432
  cert: null
  username: ${POSTGRES_MASTER_USER}
  password: ${POSTGRES_MASTER_PASSWORD}

database:
  myapp:
    name: myapp
    create: true
    extensions:
    - name: uuid-ossp

users:
- name: app_user
  password: ${APP_USER_PASSWORD}
  privileges:
  - db: myapp
    db_schema: public
    readwrite: true
    readonly: false
    tables:
    - ALL
```

Set environment variables before running:
```bash
export DB_HOST=localhost
export POSTGRES_MASTER_USER=postgres
export POSTGRES_MASTER_PASSWORD=mysecretpass
export APP_USER_PASSWORD=appuserpass
```

### 2. Use the Builder Pattern

```python
from cloudutil.sql.modules import PostgreSQLBuilder

# From YAML file
provider = (
    PostgreSQLBuilder()
    .from_yaml("config.yaml")
    .build()
)

# From dictionary
config_dict = {...}
provider = (
    PostgreSQLBuilder()
    .from_dict(config_dict)
    .build()
)

# From YAML string
yaml_string = "..."
provider = (
    PostgreSQLBuilder()
    .from_yaml_string(yaml_string)
    .build()
)

# Execute configuration with context manager
with provider:
    provider.execute()
```

## Features

### Database Operations

- **Create databases**: Automatically creates databases if they don't exist, alters owner if exists
- **Install extensions**: Supports PostgreSQL extensions (uuid-ossp, pgcrypto, etc.), updates to latest version if exists
- **Idempotent**: Safely handles existing databases, users, and extensions with ALTER statements
- **Logging**: Uses Rich logging for better visibility of operations
- **Environment variables**: Support for `${VAR_NAME}` syntax to read sensitive data from environment

### User Management

- **Create users**: Creates database users with passwords, alters password if user exists
- **Grant privileges**: Flexible privilege system supporting:
  - Read-write access (SELECT, INSERT, UPDATE, DELETE + CREATE on schema)
  - Read-only access (SELECT only)
  - Specific tables or ALL tables
  - Schema-level permissions (USAGE, CREATE)


## Usage 

In k8s you can have a one-shot job with configmap and secret and execute the sql configuration.

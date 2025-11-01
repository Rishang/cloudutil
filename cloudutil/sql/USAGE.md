# SQL Module Usage Guide

## Overview

Simple, type-safe database configuration management for PostgreSQL.

## Quick Start

### 1. Create Configuration File

```yaml
provider: 
  name: postgres
  version: 17
  host: localhost
  port: 5432
  username: postgres
  password: ${POSTGRES_PASSWORD}

database:
  - name: myapp
    create: true
    extensions:
      - name: uuid-ossp

users:
  - name: app_user
    password: ${APP_PASSWORD}
    privileges:
      - db: myapp
        db_schema: public
        readwrite: true
        tables:
          - ALL
```

### 2. Execute Configuration

```python
from cloudutil.sql.modules import PostgreSQLBuilder

provider = PostgreSQLBuilder().from_yaml("config.yaml").build()
with provider:
    provider.execute()
```

Or via CLI:
```bash
export POSTGRES_PASSWORD=secret
export APP_PASSWORD=apppass
cu sql execute --config-file config.yaml
```

## Features

- **Check-first pattern**: Verifies current state before making changes
- **Change tracking**: Reports CREATE/UPDATE/SKIP for each operation
- **Idempotent**: Safe to run multiple times
- **Environment variables**: Use `${VAR_NAME}` for sensitive data
- **Extensible**: Easy to add MySQL, MariaDB, etc.

## Configuration

### Provider
```yaml
provider:
  name: postgres
  version: 17
  host: localhost
  port: 5432
  username: postgres
  password: ${POSTGRES_PASSWORD}
  cert: null  # Optional SSL certificate path
```

### Databases
```yaml
database:
  - name: myapp
    create: true
    extensions:
      - name: uuid-ossp
      - name: pgcrypto
```

### Users & Privileges
```yaml
users:
  - name: app_user
    password: ${APP_PASSWORD}
    privileges:
      - db: myapp
        db_schema: public
        readwrite: true    # or readonly: true
        tables:
          - ALL            # or specific tables
```

## CLI Commands

```bash
# Validate configuration
cu sql validate config.yaml

# Execute configuration
cu sql execute --config-file config.yaml

# Generate sample configuration
cu sql init
```

## Kubernetes

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: sql-setup
spec:
  template:
    spec:
      containers:
      - name: sql-setup
        image: cloudutil:latest
        command: ["cu", "sql", "execute", "--config-file", "/config/config.yaml"]
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: sql-secrets
              key: password
        volumeMounts:
        - name: config
          mountPath: /config
      volumes:
      - name: config
        configMap:
          name: sql-config
      restartPolicy: Never
```

## Example Output

```
Databases
============================================================
[CREATE] database: myapp
[SKIP] database: analytics
[UPDATE] database: legacy (owner: admin → postgres)

Users
============================================================
[CREATE] user: app_user
[UPDATE] user: admin (password: *** → ***)

Summary
============================================================
Total: 5 | Created: 2 | Updated: 2 | Skipped: 1
Complete
```

## See Also

- `example.yaml` - Comprehensive configuration example
- `base.py` - Schema definitions
- `postgres.py` - PostgreSQL provider implementation (302 lines)

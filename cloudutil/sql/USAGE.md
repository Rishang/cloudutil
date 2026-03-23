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
- **Custom SQL**: Optional parameterized statements after standard provisioning
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

## Ansible

Install `cloudutil` into the Python environment used by Ansible, then use the **`cloudutil_postgres`** module (see `cloudutil/sql/ansible/cloudutil_postgres.py`).

```yaml
- name: Apply SQL config from file
  cloudutil_postgres:
    config_path: /opt/app/sql/config.yaml
  environment:
    POSTGRES_PASSWORD: "{{ vault_postgres_password }}"
  delegate_to: localhost
  connection: local
```

- **`state: present`** (default) — connect and apply (same as `cu sql execute`).
- **`state: validated`** — parse and validate only (no DB connection).

See **`ansible/README.md`** at the repository root for `library` / `ansible.cfg` setup.

## Custom SQL

Optional arbitrary SQL runs **after** databases, extensions, users, and privileges (useful for seeds, extra schema, or one-off DDL).

Each entry’s **`query`** is a **Jinja2** template string. It is rendered with **`jinja2.Environment(loader=FileSystemLoader(loader_path))`** so you can use **`{% include 'file.sql' %}`** relative to **`loader_path`** (default **`"."`**).

When **`inject_env: true`** (default), the environment sets **`env.globals["env"] = os.environ`**, so templates use **`{{ env.DB_HOST }}`**, **`{{ env.AWS_REGION }}`**, **`{{ env.HOME }}`**, etc. Extra variables come from **`template_context`** (passed to **`render(**template_context)`**). The result is stored in **`query_raw`** for execution.

```yaml
custom_sql:
  - name: ensure_public_schema
    database: myapp
    query: |
      CREATE TABLE IF NOT EXISTS public._schema_migrations (
        id SERIAL PRIMARY KEY,
        applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
      );
  - name: seed_with_params
    database: myapp
    query: INSERT INTO public.app_settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING
    params:
      - maintenance_mode
      - "false"
  - name: jinja_table_name
    database: myapp
    query: "CREATE INDEX IF NOT EXISTS idx_{{ table }} ON public.{{ table }} (id);"
    template_context:
      table: users
  - name: from_env_and_include
    database: myapp
    loader_path: "./sql/fragments"
    query: |
      {% include 'header.sql' %}
      INSERT INTO public.meta (k, v) VALUES ('env', '{{ env.MY_ENV_VAR }}');
```

- **`query`** — Jinja template source string; `query_raw` is set to the rendered SQL in `model_post_init`.
- **`query_raw`** — computed from `query` + `template_context`; do not set in YAML (it is overwritten when the model is built).
- **`loader_path`** — directory (or list of directories) for `FileSystemLoader` (`"."` by default). Used for `{% include %}` / `{% import %}` from files on disk.
- **`inject_env`** — if `true` (default), **`env.globals["env"] = os.environ`** so use **`{{ env.VAR_NAME }}`** in templates.
- **`template_context`** — keyword arguments passed to **`render()`** (e.g. `table: users` for `{{ table }}`).
- **`database`** — connect to this database (must exist or be created earlier in `database:`).
- **`params`** — optional bound parameters for `%s` placeholders (use with untrusted input only via parameters, not string interpolation).
- **`name`** — optional label for logs and change reports.

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

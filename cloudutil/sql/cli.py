"""CLI interface for SQL operations."""

from pathlib import Path

import typer
from pydantic import ValidationError
from rich import print

from cloudutil.sql.apply import apply_postgres_config, validate_postgres_config
from cloudutil.utils import logger

app = typer.Typer(
    pretty_exceptions_enable=False,
    help="SQL database management commands",
)

SUPPORTED_PROVIDERS = ("postgres",)


def _require_postgres(provider: str) -> None:
    if provider.lower() not in SUPPORTED_PROVIDERS:
        print(
            f"[bold red]Error:[/bold red] Unsupported provider '{provider}'. "
            f"Supported: {', '.join(SUPPORTED_PROVIDERS)}"
        )
        raise typer.Exit(1)


@app.command("execute")
def execute_config(
    config_file: Path = typer.Option(
        ...,
        "--config-file",
        "-c",
        help="Path to YAML configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
):
    """
    Execute database configuration from a YAML file.

    Example:
        cu sql execute -c config.yaml
    """
    try:
        print(f"[bold blue]Loading configuration from:[/bold blue] {config_file}")

        changed, changes = apply_postgres_config(config_path=config_file)

        creates = sum(1 for c in changes if c["operation"] == "create")
        updates = sum(1 for c in changes if c["operation"] == "update")
        skips = sum(1 for c in changes if c["operation"] == "skip")
        executes = sum(1 for c in changes if c["operation"] == "execute")

        print("[bold green]✓ Configuration executed successfully![/bold green]")
        print(
            f"  Total: {len(changes)} | Created: {creates} | Updated: {updates} | "
            f"Skipped: {skips} | Executed: {executes}"
        )
        if not changed:
            print("[dim]  No changes — resources already in desired state.[/dim]")

    except FileNotFoundError as e:
        print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
    except (ValueError, ValidationError) as e:
        print(f"[bold red]Configuration Error:[/bold red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        print(f"[bold red]Error:[/bold red] {e}")
        logger.exception("Failed to execute configuration")
        raise typer.Exit(1)


@app.command("validate")
def validate_config(
    config_file: Path = typer.Argument(
        ...,
        help="Path to YAML configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
):
    """
    Validate a YAML configuration file without connecting to the database.

    Example:
        cu sql validate config.yaml
    """
    try:
        print(f"[bold blue]Validating:[/bold blue] {config_file}")
        validate_postgres_config(config_path=config_file)

        # Re-build for display only (no connection made)
        from cloudutil.sql.modules.postgres import PostgreSQLBuilder

        cfg = PostgreSQLBuilder().from_yaml(config_file).build().config

        print("[bold green]✓ Configuration is valid![/bold green]\n")

        print("[bold]Provider:[/bold]")
        p = cfg.provider
        ssl_info = ""
        if p.ssl_mode:
            ssl_info = f"  ssl_mode={p.ssl_mode}"
        if p.cert:
            ssl_info += f"  cert={p.cert}"
        print(
            f"  • {p.name} v{p.version}  {p.host}:{p.port}  user={p.username}{ssl_info}"
        )

        print("\n[bold]Databases:[/bold]")
        for db in cfg.database.values():
            exts = ", ".join(e.name for e in db.extensions) or "none"
            print(f"  • {db.name}  create={db.create}  extensions=[{exts}]")

        print(f"\n[bold]Users:[/bold] ({len(cfg.users)} total)")
        for user in cfg.users:
            print(f"  • {user.name}")
            for priv in user.privileges:
                match priv:
                    case _ if priv.readwrite:
                        access = "READ/WRITE"
                    case _ if priv.readonly:
                        access = "READ-ONLY"
                    case _:
                        access = "NONE"
                tables = "ALL" if "ALL" in priv.tables else f"{len(priv.tables)} tables"
                print(f"    - {priv.db}.{priv.db_schema}: {access} on {tables}")

    except (FileNotFoundError, ValueError, ValidationError) as e:
        print(f"[bold red]Validation Error:[/bold red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command("init")
def init_config(
    output: Path = typer.Option(
        "config.yaml",
        "--output",
        "-o",
        help="Output path for the configuration template",
    ),
):
    """
    Generate a sample configuration file.

    Example:
        cu sql init
        cu sql init -o my-config.yaml
    """
    if output.exists():
        if not typer.confirm(f"File '{output}' already exists. Overwrite?"):
            print("[yellow]Operation cancelled[/yellow]")
            raise typer.Exit(0)

    output.write_text("""\
# SQL Database Configuration
# Use ${ENV_VAR} syntax for sensitive values

provider:
  name: postgres
  version: 17
  host: localhost          # or ${DB_HOST}
  port: 5432
  username: postgres       # or ${POSTGRES_USER}
  password: changeme       # or ${POSTGRES_PASSWORD}
  cert: null               # optional: path to SSL root cert
  ssl_mode: null           # optional: disable|allow|prefer|require|verify-ca|verify-full

database:
  - name: myapp
    create: true
    extensions:
      - name: uuid-ossp
      - name: pgcrypto

users:
  - name: app_readwrite
    password: ${APP_RW_PASSWORD}
    privileges:
      - db: myapp
        db_schema: public
        readwrite: true
        tables: [ALL]

  - name: app_readonly
    password: ${APP_RO_PASSWORD}
    privileges:
      - db: myapp
        db_schema: public
        readonly: true
        tables:
          - users
          - sessions

# custom_sql:
#   - name: seed
#     database: myapp
#     query: "INSERT INTO settings (key, value) VALUES ('init', 'true') ON CONFLICT DO NOTHING"
""")

    print(f"[bold green]✓ Created:[/bold green] {output}")
    print(f"\n  1. Edit {output}")
    print("  2. Export env vars for passwords")
    print(f"  3. cu sql validate {output}")
    print(f"  4. cu sql execute -c {output}")


if __name__ == "__main__":
    app()

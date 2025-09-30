"""CLI interface for SQL operations."""

from pathlib import Path

import typer
from rich import print
import yaml
from cloudutil.sql.modules.postgres import PostgreSQLBuilder
from cloudutil.utils import logger

app = typer.Typer(
    pretty_exceptions_enable=False,
    help="SQL database management commands",
)


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

    Supports creating databases, installing extensions, creating users,
    and granting privileges based on the configuration.

    Example:
        cu sql execute config.yaml
        cu sql execute config.yaml --dry-run
    """
    try:
        print(f"[bold blue]Loading configuration from:[/bold blue] {config_file}")
        data = yaml.safe_load(config_file.read_text())

        provider_name = data["provider"]["name"]

        # Build provider based on type
        if provider_name == "postgres":
            builder = PostgreSQLBuilder().from_yaml(str(config_file)).build()
        else:
            print(f"[bold red]Error:[/bold red] Unsupported provider '{provider_name}'")
            print("Currently supported providers: postgres")
            raise typer.Exit(1)

        # Execute configuration
        with builder:
            builder.execute()

        print("[bold green]✓ Configuration executed successfully![/bold green]")

    except FileNotFoundError as e:
        print(f"[bold red]Error:[/bold red] Configuration file not found: {e}")
        raise typer.Exit(1)
    except ValueError as e:
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
    provider: str = typer.Option(
        "postgres",
        "--provider",
        "-p",
        help="Database provider",
    ),
):
    """
    Validate a YAML configuration file without executing.

    Checks for syntax errors, required fields, and environment variables.

    Example:
        cu sql validate config.yaml
    """
    try:
        print(f"[bold blue]Validating:[/bold blue] {config_file}")

        if provider.lower() == "postgres":
            sql_provider = PostgreSQLBuilder().from_yaml(str(config_file)).build()
        else:
            print(f"[bold red]Error:[/bold red] Unsupported provider '{provider}'")
            raise typer.Exit(1)

        # Display configuration summary
        print("[bold green]✓ Configuration is valid![/bold green]\n")

        print("[bold]Provider Configuration:[/bold]")
        print(f"  • Name: {sql_provider.config.provider.name}")
        print(f"  • Version: {sql_provider.config.provider.version}")
        print(f"  • Host: {sql_provider.config.provider.host}")
        print(f"  • Port: {sql_provider.config.provider.port}")
        print(f"  • Username: {sql_provider.config.provider.username}")
        print(f"  • SSL Cert: {sql_provider.config.provider.cert or 'None'}\n")

        print("[bold]Databases:[/bold]")
        for db_name, db_config in sql_provider.config.database.items():
            print(f"  • {db_config.name} (create: {db_config.create})")
            if db_config.extensions:
                for ext in db_config.extensions:
                    print(f"    - Extension: {ext.name}")

        print(f"\n[bold]Users:[/bold] ({len(sql_provider.config.users)} total)")
        for user in sql_provider.config.users:
            print(f"  • {user.name}")
            for priv in user.privileges:
                access_type = (
                    "READ/WRITE"
                    if priv.readwrite
                    else "READ-ONLY"
                    if priv.readonly
                    else "NONE"
                )
                tables = (
                    "ALL"
                    if priv.tables and "ALL" in priv.tables
                    else f"{len(priv.tables)} tables"
                )
                print(f"    - {priv.db}.{priv.db_schema}: {access_type} on {tables}")

    except FileNotFoundError as e:
        print(f"[bold red]Error:[/bold red] File not found: {e}")
        raise typer.Exit(1)
    except ValueError as e:
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
        help="Output file path for the configuration template",
    ),
    provider: str = typer.Option(
        "postgres",
        "--provider",
        "-p",
        help="Database provider",
    ),
):
    """
    Generate a sample configuration file.

    Creates a template YAML configuration file with examples
    and comments to help you get started.

    Example:
        cu sql init
        cu sql init -o my-config.yaml
    """
    if output.exists():
        overwrite = typer.confirm(f"File '{output}' already exists. Overwrite?")
        if not overwrite:
            print("[yellow]Operation cancelled[/yellow]")
            raise typer.Exit(0)

    template = """# SQL Database Configuration
# Use ${ENV_VAR} syntax to reference environment variables

provider: 
  name: postgres
  version: 17
  host: localhost  # or ${DB_HOST}
  port: 5432
  username: postgres  # or ${POSTGRES_USER}
  password: changeme  # or ${POSTGRES_PASSWORD}
  cert: null  # optional SSL certificate path

database:
  # Database key can be any name
  myapp:
    name: myapp
    create: true
    extensions:
    - name: uuid-ossp
    - name: pgcrypto
  
  # Add more databases as needed
  # another_db:
  #   name: another_db
  #   create: true
  #   extensions: []

users:
- name: app_readwrite
  password: app_rw_password  # or ${APP_RW_PASSWORD}
  privileges:
  - db: myapp
    db_schema: public
    readwrite: true
    readonly: false
    tables:
    - ALL  # Grant access to all tables

- name: app_readonly
  password: app_ro_password  # or ${APP_RO_PASSWORD}
  privileges:
  - db: myapp
    db_schema: public
    readwrite: false
    readonly: true
    tables:
    - users  # Specific tables
    - sessions
    - logs

# To use environment variables, set them before running:
# export DB_HOST=localhost
# export POSTGRES_USER=postgres
# export POSTGRES_PASSWORD=secretpass
# export APP_RW_PASSWORD=rwpass
# export APP_RO_PASSWORD=ropass
"""

    output.write_text(template)
    print(f"[bold green]✓ Created configuration template:[/bold green] {output}")
    print("\n[bold]Next steps:[/bold]")
    print(f"  1. Edit {output} with your database details")
    print("  2. Set environment variables for sensitive data (optional)")
    print(f"  3. Validate: cu sql validate {output}")
    print(f"  4. Execute: cu sql execute {output}")


if __name__ == "__main__":
    app()

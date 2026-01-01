"""Azure CLI interface."""

import json
from typing import Optional

import typer
from rich.console import Console

from .secrets import search_secrets_with_fzf

app = typer.Typer(
    pretty_exceptions_enable=False,
)

console = Console()


@app.command()
def secrets(
    vault: str = typer.Option(
        ..., "--vault", "-v", help="Name of the Azure Key Vault"
    ),
    name_filter: Optional[str] = typer.Option(
        None, "--filter", help="Filter secrets by name prefix"
    ),
):
    """
    Search Key Vault secrets interactively using fzf for selection.
    """
    try:
        secrets = search_secrets_with_fzf(
            vault_name=vault,
            name_filter=name_filter,
        )

        if not secrets:
            raise typer.Exit(code=1)

        for secret in secrets:
            try:
                # Try to parse as JSON if it looks like JSON
                parsed_value = json.loads(secret.value)
                console.print(f"Name: '{secret.name}'")
                if secret.description:
                    console.print(f"Content Type: '{secret.description}'")
                console.print(f"ID: '{secret.id}'")
                console.print("Value (JSON):")
                console.print(json.dumps(parsed_value, indent=2))
                console.print("-" * 80)
                console.print()
            except json.JSONDecodeError:
                console.print(
                    f"[yellow][!] Warning: Could not parse secret '{secret.name}' as JSON, showing raw value[/yellow]"
                )
                # If not JSON, just show the secret model dump or value
                console.print(f"Name: '{secret.name}'")
                if secret.description:
                    console.print(f"Content Type: '{secret.description}'")
                console.print(f"ID: '{secret.id}'")
                console.print("Value:")
                console.print(secret.value)
                console.print("-" * 80)
                console.print()

    except Exception as e:
        console.print(f"[bold red][!] ERROR: {e}[/bold red]")
        raise typer.Exit(code=1)

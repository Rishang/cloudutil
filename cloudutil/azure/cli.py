"""Azure CLI interface."""

import json
from typing import Optional

import typer
from ..utils import pprint

from ..helper import fzf_select
from .secrets import get_secret, list_secrets

app = typer.Typer(
    pretty_exceptions_enable=False,
)


@app.command()
def secrets(
    vault: str = typer.Option(..., "--vault", "-v", help="Name of the Azure Key Vault"),
    name_filter: Optional[str] = typer.Option(
        None, "--filter", help="Filter secrets by name prefix"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text/json)"
    ),
):
    """
    Search Key Vault secrets interactively using fzf for selection.
    """
    try:
        if output.lower() != "json":
            pprint(
                f"[*] Listing secrets from vault [bold cyan]{vault}[/bold cyan]"
                + (
                    f" with filter: [bold cyan]{name_filter}[/bold cyan]"
                    if name_filter
                    else ""
                )
            )

        secret_names = list_secrets(vault, name_filter)

        if not secret_names:
            if output.lower() != "json":
                pprint("[yellow][!] No secrets found.[/yellow]")
            raise typer.Exit(code=1)

        if output.lower() != "json":
            pprint(
                f"[*] Found {len(secret_names)} secrets. Opening fzf for selection..."
            )

        selected_names = fzf_select(
            secret_names, "secret", quiet=(output.lower() == "json")
        )

        if not selected_names:
            raise typer.Exit(code=1)

        if output.lower() != "json":
            pprint(f"[*] Retrieving {len(selected_names)} selected secrets...")

        secrets = []
        for name in selected_names:
            try:
                secrets.append(get_secret(vault, name))
            except Exception as e:
                pprint(
                    f"[bold red][!] ERROR: Failed to retrieve secret {name}: {e}[/bold red]"
                )

        pprint(json.dumps([s.dict() for s in secrets], indent=2, default=str))

        pprint("[green][+][/green] Secrets retrieved successfully.")

    except Exception as e:
        pprint(f"[bold red][!] ERROR: {e}[/bold red]")
        raise typer.Exit(code=1)

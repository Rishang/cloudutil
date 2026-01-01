"""Azure Key Vault secrets utilities."""

import json
from typing import List, Optional

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from pydantic import BaseModel
from rich.console import Console

from ..helper import fzf_select

console = Console()


class Secret(BaseModel):
    """Secret model."""

    name: str
    value: str
    id: Optional[str] = None
    description: Optional[str] = None


def get_secret_client(vault_name: str) -> SecretClient:
    """Get Key Vault client."""
    vault_url = f"https://{vault_name}.vault.azure.net/"
    credential = DefaultAzureCredential()
    return SecretClient(vault_url=vault_url, credential=credential)


def list_secrets(vault_name: str, name_filter: Optional[str] = None) -> List[str]:
    """
    List Key Vault secrets.

    Args:
        vault_name: Name of the Key Vault
        name_filter: Filter secrets by name prefix (not directly supported by KV list, so we filter locally)

    Returns:
        List of secret names
    """
    client = get_secret_client(vault_name)
    secrets = []

    # Azure SDK returns an iterator
    properties = client.list_properties_of_secrets()

    for secret_prop in properties:
        if name_filter and not secret_prop.name.startswith(name_filter):
            continue
        secrets.append(secret_prop.name)

    return secrets


def get_secret(vault_name: str, name: str) -> Secret:
    """
    Get a specific secret by name.

    Args:
        vault_name: Name of the Key Vault
        name: Secret name

    Returns:
        Secret object
    """
    client = get_secret_client(vault_name)

    secret_bundle = client.get_secret(name)

    return Secret(
        name=secret_bundle.name,
        value=secret_bundle.value,
        id=secret_bundle.id,
        # Azure defines content_type, not description usually, but we can map if needed or leave empty
        description=secret_bundle.content_type,
    )


def search_secrets_with_fzf(
    vault_name: str,
    name_filter: Optional[str] = None,
) -> List[Secret]:
    """
    Search secrets using fzf for interactive selection.

    Args:
        vault_name: Name of the Key Vault
        name_filter: Filter secrets by name prefix

    Returns:
        List of selected Secret objects
    """
    console.print(
        f"[*] Listing secrets from vault [bold cyan]{vault_name}[/bold cyan]"
        + (f" with filter: [bold cyan]{name_filter}[/bold cyan]" if name_filter else "")
    )

    try:
        secrets = list_secrets(vault_name, name_filter)
    except Exception as e:
        console.print(f"[bold red][!] ERROR: Failed to list secrets: {e}[/bold red]")
        return []

    if not secrets:
        console.print("[yellow][!] No secrets found.[/yellow]")
        return []

    console.print(f"[*] Found {len(secrets)} secrets. Opening fzf for selection...")

    selected = fzf_select(secrets, "secret")
    if not selected:
        return []

    console.print(f"[*] Retrieving {len(selected)} selected secrets...")
    secret_objects = []

    for name in selected:
        try:
            secret_objects.append(get_secret(vault_name, name))
        except Exception as e:
            console.print(
                f"[bold red][!] ERROR: Failed to retrieve secret {name}: {e}[/bold red]"
            )

    console.print("[green][+][/green] Secrets retrieved successfully.")

    return secret_objects

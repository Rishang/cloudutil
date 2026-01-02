"""Azure Key Vault secrets utilities."""

from typing import List, Optional

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from pydantic import BaseModel


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
        description=secret_bundle.properties.content_type,
    )

"""AWS Secrets Manager utilities."""

import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from rich.console import Console
from .common import get_aws_client
from ..helper import fzf_select

console = Console()


class Secret(BaseModel):
    """Secret model."""

    name: str
    value: str
    arn: Optional[str] = None
    description: Optional[str] = None


def get_secrets_client(
    profile_name: Optional[str] = None, region_name: Optional[str] = None
):
    """Get Secrets Manager client with optional profile and region."""
    return get_aws_client("secretsmanager", profile_name, region_name)


def list_secrets(
    name_filter: Optional[str] = None,
    profile_name: Optional[str] = None,
    region_name: Optional[str] = None,
) -> List[str]:
    """
    List Secrets Manager secrets.

    Args:
        name_filter: Filter secrets by name prefix
        profile_name: AWS profile to use
        region_name: AWS region to use

    Returns:
        List of secret names
    """
    secrets_client = get_secrets_client(profile_name, region_name)
    secrets = []
    next_token = None

    while True:
        kwargs = {
            "MaxResults": 100,
        }
        if name_filter is not None:
            kwargs["Filters"] = [{"Key": "name", "Values": [name_filter]}]
        if next_token:
            kwargs["NextToken"] = next_token

        response = secrets_client.list_secrets(**kwargs)
        for secret in response["SecretList"]:
            secrets.append(secret["Name"])
        next_token = response.get("NextToken")
        if not next_token:
            break

    return secrets


def get_secret(
    name: str, profile_name: Optional[str] = None, region_name: Optional[str] = None
) -> Secret:
    """
    Get a specific secret by name.

    Args:
        name: Secret name or ARN
        profile_name: AWS profile to use
        region_name: AWS region to use

    Returns:
        Secret object
    """
    secrets_client = get_secrets_client(profile_name, region_name)

    # Get secret metadata
    describe_response = secrets_client.describe_secret(SecretId=name)

    # Get secret value
    value_response = secrets_client.get_secret_value(SecretId=name)

    secret_value = value_response["SecretString"]

    return Secret(
        name=describe_response["Name"],
        value=secret_value,
        arn=describe_response["ARN"],
        description=describe_response.get("Description"),
    )


def get_secret_json(
    name: str, profile_name: Optional[str] = None, region_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get a secret value and parse it as JSON.

    Args:
        name: Secret name or ARN
        profile_name: AWS profile to use
        region_name: AWS region to use

    Returns:
        Parsed JSON dictionary
    """
    secret = get_secret(name, profile_name, region_name)
    try:
        return json.loads(secret.value)
    except json.JSONDecodeError as e:
        console.print(
            f"[bold red][!] ERROR: Failed to parse secret as JSON: {e}[/bold red]"
        )
        raise


def search_secrets_with_fzf(
    name_filter: Optional[str] = None,
    profile_name: Optional[str] = None,
    region_name: Optional[str] = None,
) -> List[Secret]:
    """
    Search secrets using fzf for interactive selection.

    Args:
        name_filter: Filter secrets by name prefix
        profile_name: AWS profile to use
        region_name: AWS region to use

    Returns:
        List of selected Secret objects
    """
    console.print(
        "[*] Listing secrets"
        + (f" with filter: [bold cyan]{name_filter}[/bold cyan]" if name_filter else "")
    )

    secrets = list_secrets(name_filter, profile_name, region_name)
    if not secrets:
        console.print("[yellow][!] No secrets found.[/yellow]")
        return []

    console.print(f"[*] Found {len(secrets)} secrets. Opening fzf for selection...")

    # Use fzf for fuzzy selection
    selected = fzf_select(secrets, "secret")
    if not selected:
        return []

    console.print(f"[*] Retrieving {len(selected)} selected secrets...")
    secret_objects = [get_secret(name, profile_name, region_name) for name in selected]
    console.print("[green][+][/green] Secrets retrieved successfully.")

    return secret_objects

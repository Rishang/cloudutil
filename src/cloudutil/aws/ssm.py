"""AWS SSM (Systems Manager) Parameter Store utilities."""

import subprocess
import boto3
from typing import List, Optional
from pydantic import BaseModel

from rich.console import Console

console = Console()


class SSMParameter(BaseModel):
    """SSM Parameter model."""

    name: str
    value: str


def get_ssm_client(
    profile_name: Optional[str] = None, region_name: Optional[str] = None
):
    """Get SSM client with optional profile and region."""
    session_kwargs = {}
    if profile_name:
        session_kwargs["profile_name"] = profile_name
    if region_name:
        session_kwargs["region_name"] = region_name

    session = boto3.Session(**session_kwargs)
    return session.client("ssm")


def list_parameters(
    prefix: str = "/",
    profile_name: Optional[str] = None,
    region_name: Optional[str] = None,
) -> List[str]:
    """
    List SSM parameters by path prefix.

    Args:
        prefix: SSM path prefix to search
        profile_name: AWS profile to use
        region_name: AWS region to use

    Returns:
        List of parameter names
    """
    ssm_client = get_ssm_client(profile_name, region_name)
    parameters = []
    next_token = None

    while True:
        kwargs = {
            "Path": prefix,
            "Recursive": True,
            "WithDecryption": True,
            "MaxResults": 10,
        }
        if next_token:
            kwargs["NextToken"] = next_token

        response = ssm_client.get_parameters_by_path(**kwargs)
        for param in response["Parameters"]:
            parameters.append(param["Name"])
        next_token = response.get("NextToken")
        if not next_token:
            break

    return parameters


def get_parameter(
    name: str, profile_name: Optional[str] = None, region_name: Optional[str] = None
) -> SSMParameter:
    """
    Get a specific SSM parameter by name.

    Args:
        name: Parameter name
        profile_name: AWS profile to use
        region_name: AWS region to use

    Returns:
        SSMParameter object
    """
    ssm_client = get_ssm_client(profile_name, region_name)
    response = ssm_client.get_parameter(Name=name, WithDecryption=True)
    param = response["Parameter"]
    return SSMParameter(name=param["Name"], value=param["Value"])


def search_parameters_with_fzf(
    prefix: str = "/",
    profile_name: Optional[str] = None,
    region_name: Optional[str] = None,
) -> List[SSMParameter]:
    """
    Search SSM parameters using fzf for interactive selection.

    Args:
        prefix: SSM path prefix to search
        profile_name: AWS profile to use
        region_name: AWS region to use

    Returns:
        List of selected SSMParameter objects
    """
    console.print(
        f"[*] Listing SSM parameters with prefix: [bold cyan]{prefix}[/bold cyan]"
    )

    parameters = list_parameters(prefix, profile_name, region_name)
    if not parameters:
        console.print("[yellow][!] No parameters found.[/yellow]")
        return []

    console.print(
        f"[*] Found {len(parameters)} parameters. Opening fzf for selection..."
    )

    # Use fzf for fuzzy selection
    try:
        fzf = subprocess.run(
            ["fzf", "-m", "-e"],
            input="\n".join(parameters),
            text=True,
            capture_output=True,
        )
        selected = fzf.stdout.strip().splitlines()

        if not selected or len(selected) == 0:
            console.print("[yellow][!] No selection made.[/yellow]")
            return []

        console.print(f"[*] Retrieving {len(selected)} selected parameters...")
        params = [get_parameter(name, profile_name, region_name) for name in selected]
        console.print("[green][+][/green] Parameters retrieved successfully.")

        return params

    except FileNotFoundError:
        console.print(
            "[bold red][!] ERROR: fzf not found. Please install fzf for interactive parameter selection.[/bold red]"
        )
        return []
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red][!] ERROR: fzf selection failed: {e}[/bold red]")
        return []

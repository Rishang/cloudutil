"""AWS SSM (Systems Manager) Parameter Store utilities."""

from typing import List, Optional
from pydantic import BaseModel

from rich.console import Console
from cloudutil.aws.common import get_aws_client
from cloudutil.helper import fzf_select

console = Console()


class SSMParameter(BaseModel):
    """SSM Parameter model."""

    name: str
    value: str


def get_ssm_client(
    profile_name: Optional[str] = None, region_name: Optional[str] = None
):
    """Get SSM client with optional profile and region."""
    return get_aws_client("ssm", profile_name, region_name)


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
    selected = fzf_select(parameters, "parameter")
    if not selected:
        return []

    console.print(f"[*] Retrieving {len(selected)} selected parameters...")
    params = [get_parameter(name, profile_name, region_name) for name in selected]
    console.print("[green][+][/green] Parameters retrieved successfully.")

    return params

"""AWS SSM (Systems Manager) Parameter Store utilities."""

import os
from pydantic import BaseModel
from typing import List, Optional

from rich.console import Console
from .common import get_aws_client
from ..helper import fzf_select

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


def ssm_instance(
    instance_id: str,
    tunnel: bool = False,
    document_name: str = "AWS-StartPortForwardingSessionToRemoteHost",
    remote_host: str = "",
    remote_port: int = 0,
    local_port: int = 0,
):
    if tunnel:
        if remote_host == "" or remote_port == 0 or local_port == 0:
            console.print(
                "[bold red][!] ERROR: Remote host, remote port, and local port are required for tunneling.[/bold red]"
            )
            return

        os.system(f"""aws ssm start-session --target {instance_id} \
                --document-name {document_name} \
                --parameters '{{'host': ['{remote_host}'], 'portNumber': ['{remote_port}'], 'localPortNumber': ['{local_port}']}}'""")

    else:
        os.system(f"aws ssm start-session --target {instance_id}")


def list_ssm_instances() -> List[dict[str, str]]:
    ec2 = get_aws_client("ec2")
    response = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": ["*"]},
        ]
    )
    instances = []
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            # Only include instances with IAM roles
            if "IamInstanceProfile" not in instance:
                continue

            name = ""
            for tag in instance["Tags"]:
                if tag["Key"] == "Name":
                    name = tag["Value"]
                    break
            instances.append({"instance_id": instance["InstanceId"], "name": name})
    return instances

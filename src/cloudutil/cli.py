"""CLI interface for cloudutil."""

import json
import webbrowser
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from cloudutil.aws.login import generate_federated_console_url
from cloudutil.aws.ssm import (
    search_parameters_with_fzf,
    list_ssm_instances,
    ssm_instance,
)
from cloudutil.aws.secrets import search_secrets_with_fzf
from cloudutil.helper import fzf_select

app = typer.Typer(
    pretty_exceptions_enable=False,
)

console = Console()


@app.command()
def aws_login(
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="AWS CLI profile name to use."
    ),
    region: Optional[str] = typer.Option(
        "us-east-1",
        "--region",
        "-r",
        help="AWS region for STS client (e.g., us-east-1). STS is global, but client can be regional.",
    ),
    duration: int = typer.Option(
        7200,
        "--duration",
        "-d",
        min=900,
        max=43200,
        help="Duration for temporary credentials in seconds (900-43200).",
    ),
    policy_file: Optional[Path] = typer.Option(
        None,
        "--policy-file",
        "-f",
        help="Path to a JSON file containing an IAM policy to scope down permissions.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
    ),
    no_open: bool = typer.Option(
        False,
        "--no-open",
        help="Do not automatically open the URL in the browser, just print it.",
    ),
):
    """
    Generates an AWS console login URL using STS GetFederationToken and opens it.
    """
    policy_doc = None
    destination = f"https://{region}.console.aws.amazon.com/"

    if policy_file:
        try:
            with policy_file.open("r") as f:
                policy_doc = json.load(f)
            console.print(
                f"[*] Using policy from file: [bold cyan]{policy_file}[/bold cyan]"
            )
        except Exception as e:
            console.print(
                f"[bold red][!] ERROR: Could not read or parse policy file '{policy_file}': {e}[/bold red]"
            )
            raise typer.Exit(code=1)

    console_url = generate_federated_console_url(
        profile_name=profile,
        region_name=region,
        duration_seconds=duration,
        policy_document=policy_doc,
        destination_url=destination,
    )

    if console_url:
        if no_open:
            console.print("\n[bold yellow]Generated Console Login URL:[/bold yellow]")
            console.print(console_url)
            console.print(
                "\n[italic]Copy and paste the above URL into your browser.[/italic]"
            )
        else:
            console.print(
                f"[*] Opening URL in your default web browser ([italic]{webbrowser.get()}[/italic])..."
            )
            try:
                opened = webbrowser.open_new_tab(console_url)
                if opened:
                    console.print("[green][+][/green] Done. Check your browser.")
                else:
                    console.print(
                        "[yellow][!] Warning: Could not automatically open browser. Please copy the URL manually:[/yellow]"
                    )
                    console.print(console_url)

            except webbrowser.Error as e:
                console.print(
                    f"[yellow][!] Warning: Could not open browser ({e}). Please copy the URL manually:[/yellow]"
                )
                console.print(console_url)
    else:
        console.print("[bold red][!] Failed to generate console login URL.[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def aws_ssm_parameters(
    prefix: str = typer.Option("/", "--prefix", help="SSM path prefix to search"),
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="AWS CLI profile name to use."
    ),
    region: Optional[str] = typer.Option(
        None, "--region", "-r", help="AWS region to use."
    ),
):
    """
    Search SSM parameters interactively using fzf for selection.
    """
    try:
        parameters = search_parameters_with_fzf(
            prefix=prefix, profile_name=profile, region_name=region
        )

        if not parameters:
            raise typer.Exit(code=1)

        for param in parameters:
            console.print(param.model_dump_json(indent=2))

    except Exception as e:
        console.print(f"[bold red][!] ERROR: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def aws_ssm_instance(
    tunnel: bool = typer.Option(False, "--tunnel", help="Tunnel to the instance"),
    remote_host: str = typer.Option(
        "", "--remote-host", help="Remote host to tunnel to"
    ),
    remote_port: int = typer.Option(
        0, "--remote-port", help="Remote port to tunnel to"
    ),
    local_port: int = typer.Option(0, "--local-port", help="Local port to tunnel to"),
):
    instances = [
        f"{instance['instance_id']} | {instance['name']}"
        for instance in list_ssm_instances()
    ]
    selected = fzf_select(instances, "instance", multi_select=False)
    if not selected:
        raise typer.Exit(code=1)
    instance_id = selected[0].split(" | ")[0]
    ssm_instance(
        instance_id=instance_id,
        tunnel=tunnel,
        remote_host=remote_host,
        remote_port=remote_port,
        local_port=local_port,
    )


@app.command()
def aws_secrets(
    name_filter: Optional[str] = typer.Option(
        None, "--filter", help="Filter secrets by name prefix"
    ),
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="AWS CLI profile name to use."
    ),
    region: Optional[str] = typer.Option(
        None, "--region", "-r", help="AWS region to use."
    ),
):
    """
    Search Secrets Manager secrets interactively using fzf for selection.
    """
    try:
        secrets = search_secrets_with_fzf(
            name_filter=name_filter, profile_name=profile, region_name=region
        )

        if not secrets:
            raise typer.Exit(code=1)

        for secret in secrets:
            try:
                parsed_value = json.loads(secret.value)
                console.print(f"Name: '{secret.name}'")
                if secret.description:
                    console.print(f"Description: '{secret.description}'")
                console.print(f"ARN: '{secret.arn}'")
                console.print("Value (JSON):")
                console.print(json.dumps(parsed_value, indent=2))
                console.print("-" * 80)
                console.print()
            except json.JSONDecodeError:
                console.print(
                    f"[yellow][!] Warning: Could not parse secret '{secret.name}' as JSON, showing raw value[/yellow]"
                )
                console.print(secret.model_dump_json(indent=2))
                console.print("-" * 80)
                console.print()

    except Exception as e:
        console.print(f"[bold red][!] ERROR: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def help():
    """Show help information."""
    console.print("[bold]CloudUtil - AWS utilities[/bold]")
    console.print("\nAvailable commands:")
    console.print(
        "  [cyan]aws-login[/cyan]     - Generate and open AWS console login URL"
    )
    console.print(
        "  [cyan]aws-ssm[/cyan]       - Search SSM parameters interactively with fzf"
    )
    console.print(
        "  [cyan]aws-secrets[/cyan]   - Search Secrets Manager secrets interactively with fzf"
    )
    console.print(
        "\nUse 'cloudutil <command> --help' for detailed command information."
    )


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()

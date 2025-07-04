"""CLI interface for cloudutil."""

import json
import webbrowser
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from cloudutil.aws.login import generate_federated_console_url
from cloudutil.aws.ssm import search_parameters_with_fzf

app = typer.Typer(
    help="AWS utilities including console login and SSM parameter management.",
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
def aws_ssm(
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
def help():
    """Show help information."""
    console.print("[bold]CloudUtil - AWS utilities[/bold]")
    console.print("\nAvailable commands:")
    console.print(
        "  [cyan]aws-login[/cyan]   - Generate and open AWS console login URL"
    )
    console.print(
        "  [cyan]ssm-search[/cyan]  - Search SSM parameters interactively with fzf"
    )
    console.print("  [cyan]ssm-list[/cyan]    - List SSM parameter names by prefix")
    console.print("  [cyan]ssm-get[/cyan]     - Get a specific SSM parameter")
    console.print(
        "\nUse 'cloudutil <command> --help' for detailed command information."
    )


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()

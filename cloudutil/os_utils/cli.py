"""CLI for os_utils (e.g. YAML diff checker)."""

import subprocess
from pathlib import Path
from typing import Annotated
import os

import typer
from rich.rule import Rule
from cloudutil.utils import console
from cloudutil.os_utils.yaml_diff import (
    DiffCheckConfig,
    compare_pair,
    extract,
    load_yaml,
)

app = typer.Typer(
    name="yaml-diffcheck",
    help="[cyan]Compare YAML files at a JMESPath location and report key/value differences.[/cyan]",
    rich_markup_mode="rich",
    no_args_is_help=True,
)


@app.command()
def history():
    shell = os.environ.get("SHELL", "")

    if "zsh" in shell:
        cmd = r"""cat ~/.zsh_history | sed 's/^: [0-9]*:[0-9]*;//' | sort -u | fzf -e"""
    elif "bash" in shell:
        cmd = r"""cat ~/.bash_history | sort -u | fzf -e"""
    else:
        raise typer.Exit(1, f"Unsupported shell: {shell}")

    subprocess.run(["bash", "-c", cmd])


@app.command()
def ydiff(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Path to the YAML diff checker config file.",
            show_default=True,
            rich_help_panel="Options",
        ),
    ] = Path("ydiff_config.yaml"),
) -> None:
    """
    [bold cyan]YAML Diff Checker[/bold cyan] — compare YAML nodes via JMESPath.

    Reads a config YAML and compares all alias pairs, reporting missing keys
    and value differences.
    """
    cfg = DiffCheckConfig.from_yaml(config)
    total_pairs = sum(len(e.pairs()) for e in cfg.checks)

    console.print(
        Rule(
            f"[bold]YAML DIFF CHECKER[/bold]  [dim]·[/dim]  "
            f"[cyan]{len(cfg.checks)} check(s)[/cyan]  [dim]·[/dim]  "
            f"[cyan]{total_pairs} pair(s)[/cyan]",
            style="cyan",
        )
    )

    total_issues = 0

    for idx, entry in enumerate(cfg.checks, 1):
        loaded: dict[str, dict] = {fe.alias: load_yaml(fe.path) for fe in entry.files}

        for pair_idx, (fa, fb) in enumerate(entry.pairs(), 1):
            console.print(
                f"\n[dim][{idx}/{len(cfg.checks)}] pair {pair_idx}/{len(entry.pairs())}[/dim]  "
                f"[magenta bold]{fa.alias}[/magenta bold] [dim]↔[/dim] [blue bold]{fb.alias}[/blue bold]"
            )

            try:
                node_a = extract(loaded[fa.alias], entry.jsmec)
            except KeyError as exc:
                console.print(
                    f"  [yellow][WARN] {exc} in '{fa.alias}' — skipping pair.[/yellow]"
                )
                continue

            try:
                node_b = extract(loaded[fb.alias], entry.jsmec)
            except KeyError as exc:
                console.print(
                    f"  [yellow][WARN] {exc} in '{fb.alias}' — skipping pair.[/yellow]"
                )
                continue

            total_issues += compare_pair(
                node_a, node_b, fa, fb, entry.jsmec, entry.ignore_patterns
            )

    # ── Overall result ─────────────────────────────────────────────────────────
    console.print()
    if total_issues == 0:
        console.print(
            Rule(
                "[bold green]🎉  ALL CHECKS PASSED — no differences detected.[/bold green]",
                style="green",
            )
        )
    else:
        console.print(
            Rule(
                f"[bold red]❌  {total_issues} total issue(s) across all pairs.[/bold red]",
                style="red",
            )
        )
    console.print()

    raise typer.Exit(1 if total_issues else 0)


if __name__ == "__main__":
    app()

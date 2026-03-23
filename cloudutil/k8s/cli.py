"""CLI for Kubernetes utilities (secrets, configmaps)."""

from __future__ import annotations

from typing import Optional

import typer

from cloudutil.k8s.configmap import view_configmaps_with_fzf
from cloudutil.k8s.secrets import view_secrets_with_fzf

app = typer.Typer(
    pretty_exceptions_enable=False,
    help="Kubernetes-related commands",
)


@app.command("secrets")
def k8s_secrets(
    all_namespaces: bool = typer.Option(
        False,
        "--all-namespaces",
        "-A",
        help="Search secrets across all namespaces.",
    ),
    namespace: Optional[str] = typer.Option(
        None,
        "--namespace",
        "-n",
        help="Namespace to search (ignored if --all-namespaces is set).",
    ),
    select_namespace: bool = typer.Option(
        False,
        "--select-namespace",
        help="Use fzf to select a namespace instead of scanning all namespaces.",
    ),
) -> None:
    """
    Interactive fzf view for Kubernetes secrets (decodes base64 data before printing).
    """
    if all_namespaces:
        namespace = None
    view_secrets_with_fzf(
        all_namespaces=all_namespaces,
        namespace=namespace,
        select_namespace=select_namespace,
    )


@app.command("configmaps")
def k8s_configmaps(
    all_namespaces: bool = typer.Option(
        False,
        "--all-namespaces",
        "-A",
        help="Search ConfigMaps across all namespaces.",
    ),
    namespace: Optional[str] = typer.Option(
        None,
        "--namespace",
        "-n",
        help="Namespace to search (ignored if --all-namespaces is set).",
    ),
    select_namespace: bool = typer.Option(
        False,
        "--select-namespace",
        help="Use fzf to select a namespace instead of scanning all namespaces.",
    ),
) -> None:
    """
    Interactive fzf view for Kubernetes ConfigMaps.
    """
    if all_namespaces:
        namespace = None
    view_configmaps_with_fzf(
        all_namespaces=all_namespaces,
        namespace=namespace,
        select_namespace=select_namespace,
    )

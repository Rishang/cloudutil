"""Common helper utilities for cloudutil."""

import subprocess
from typing import List, Optional, Tuple
from rich.console import Console

console = Console()


class BaseCrud:
    """Base class for AWS CRUD operations."""

    def __init__(self, client: object):
        self.client = client

    def list(self, **kwargs): ...

    def get(self, **kwargs): ...

    def create(self, **kwargs): ...

    def update(self, **kwargs): ...


class ShellRunner:
    """Utility class for running shell commands."""

    def __init__(self):
        self.console = Console()

    def run_command(
        self,
        command: List[str],
        input_text: Optional[str] = None,
        capture_output: bool = True,
        text: bool = True,
    ) -> Tuple[bool, str, str]:
        """
        Run a shell command and return success status and output.

        Args:
            command: Command to run as list of strings
            input_text: Input to pass to the command
            capture_output: Whether to capture stdout/stderr
            text: Whether to treat input/output as text

        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            result = subprocess.run(
                command,
                input=input_text,
                capture_output=capture_output,
                text=text,
                check=False,  # Don't raise exception on non-zero exit
            )

            success = result.returncode == 0
            stdout = result.stdout or ""
            stderr = result.stderr or ""

            return success, stdout, stderr

        except FileNotFoundError:
            return False, "", f"Command not found: {' '.join(command)}"
        except Exception as e:
            return False, "", str(e)


# Global shell runner instance
shell = ShellRunner()

# Export for direct use by other modules
__all__ = ["ShellRunner", "shell", "fzf_select"]


def fzf_select(
    items: List[str],
    service_name: str = "item",
    multi_select: bool = True,
    quiet: bool = False,
) -> List[str]:
    """
    Interactive selection using fzf.

    Args:
        items: List of items to select from
        service_name: Name of the service/item type for error messages
        multi_select: Whether to allow multiple selections
        quiet: Whether to suppress status messages

    Returns:
        List of selected items (empty list if no selection or error)
    """
    if not items:
        if not quiet:
            console.print(f"[yellow][!] No {service_name}s found.[/yellow]")
        return []

    if not quiet:
        console.print(
            f"[*] Found {len(items)} {service_name}s. Opening fzf for selection..."
        )

    # Build fzf command
    fzf_cmd = ["fzf", "-e"]
    if multi_select:
        fzf_cmd.append("-m")

    # Use shell runner to execute fzf
    success, stdout, stderr = shell.run_command(fzf_cmd, input_text="\n".join(items))

    if not success:
        if "Command not found" in stderr and "fzf" in stderr:
            console.print(
                f"[bold red][!] ERROR: fzf not found. Please install fzf for interactive {service_name} selection.[/bold red]"
            )
        else:
            console.print(
                f"[bold red][!] ERROR: fzf selection failed: {stderr}[/bold red]"
            )
        return []

    selected = stdout.strip().splitlines()

    if not selected or len(selected) == 0:
        if not quiet:
            console.print("[yellow][!] No selection made.[/yellow]")
        return []

    return selected

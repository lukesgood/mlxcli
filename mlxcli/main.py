"""Main entry point for MLX-CLI using Typer.

This module provides the CLI entry point using Typer, allowing the application
to be run as a command-line tool with options like --root for specifying the
project root directory.

Usage:
    python -m mlxcli
    python -m mlxcli --root /path/to/project
    mlx-cli (when installed via pyproject.toml entry point)

Example:
    >>> from mlxcli.main import app
    >>> # Run via: python -m mlxcli --help
    >>> # Or: typer run mlxcli.main:app
"""

from pathlib import Path
from typing import Optional

import typer

from mlxcli.cli import CLI

# Create the Typer app
app = typer.Typer(
    name="mlx-cli",
    help="Terminal-based LLM CLI tool with MLX backend",
)


@app.command()
def main(
    root: Optional[Path] = typer.Option(
        None,
        "--root",
        "-r",
        help="Project root directory",
    ),
) -> None:
    """Run the MLX-CLI interactive interface.

    Starts the interactive REPL loop for the MLX-CLI tool. The project root
    can be specified via --root/-r option, otherwise defaults to current directory.

    Args:
        root: Optional path to project root. Defaults to current working directory.

    Example:
        mlx-cli --root /path/to/project
        mlx-cli -r /home/user/my-project
        mlx-cli  # Uses current directory
    """
    # Create CLI instance with the specified project root
    cli = CLI(project_root=root)

    # Run the interactive interface
    cli.run()


if __name__ == "__main__":
    app()

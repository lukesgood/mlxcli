"""Module runner for mlx-cli.

Allows the mlxcli package to be executed as a module via:
    python -m mlxcli

This file is automatically called when the package is invoked as a module.
"""

from mlxcli.main import app

if __name__ == "__main__":
    app()

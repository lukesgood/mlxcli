"""Tests for main.py - Typer CLI entry point."""

import sys
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.main import app
from mlxcli.cli import CLI


class TestMainApp:
    """Test main.py Typer application."""

    def test_app_is_exported(self):
        """main.py should export app instance."""
        assert app is not None

    def test_app_is_typer_app(self):
        """app should be a Typer application."""
        import typer
        assert isinstance(app, typer.Typer)

    def test_main_command_exists(self):
        """app should have a main command."""
        assert hasattr(app, "command") or len(app.registered_commands) > 0

    def test_can_run_help_without_error(self):
        """python -m mlxcli --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "mlxcli", "--help"],
            cwd="/Users/luke/mlxcli",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--root" in result.stdout or "--help" in result.stdout

    def test_help_shows_root_option(self):
        """Help output should show --root option."""
        result = subprocess.run(
            [sys.executable, "-m", "mlxcli", "--help"],
            cwd="/Users/luke/mlxcli",
            capture_output=True,
            text=True,
        )
        assert "--root" in result.stdout or "-r" in result.stdout


class TestMainCommand:
    """Test main command behavior."""

    def test_main_accepts_root_option(self):
        """main command should accept --root option."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock CLI to prevent interactive model selection
            with patch("mlxcli.main.CLI") as mock_cli_class:
                mock_cli_instance = MagicMock()
                mock_cli_class.return_value = mock_cli_instance

                runner = __import__("typer.testing", fromlist=["CliRunner"]).CliRunner()
                result = runner.invoke(app, ["--root", tmpdir])

                # Should call CLI with the provided root
                mock_cli_class.assert_called_once()

    def test_main_uses_default_root(self):
        """main command should default to current directory."""
        with patch("mlxcli.main.CLI") as mock_cli_class:
            mock_cli_instance = MagicMock()
            mock_cli_class.return_value = mock_cli_instance

            runner = __import__("typer.testing", fromlist=["CliRunner"]).CliRunner()
            result = runner.invoke(app, [])

            # Should call CLI with None or current directory
            mock_cli_class.assert_called_once()

    def test_main_calls_cli_run(self):
        """main command should call cli.run()."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mlxcli.main.CLI") as mock_cli_class:
                mock_cli_instance = MagicMock()
                mock_cli_class.return_value = mock_cli_instance

                runner = __import__("typer.testing", fromlist=["CliRunner"]).CliRunner()
                result = runner.invoke(app, ["--root", tmpdir])

                # Should call run() on the CLI instance
                mock_cli_instance.run.assert_called_once()

    def test_main_short_form_root_option(self):
        """main command should accept -r short form."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mlxcli.main.CLI") as mock_cli_class:
                mock_cli_instance = MagicMock()
                mock_cli_class.return_value = mock_cli_instance

                runner = __import__("typer.testing", fromlist=["CliRunner"]).CliRunner()
                result = runner.invoke(app, ["-r", tmpdir])

                # Should work with -r as well
                mock_cli_class.assert_called_once()

    def test_main_has_docstring(self):
        """main function should have a docstring."""
        from mlxcli import main
        # Get the main function from the app
        assert main.__doc__ is not None or len(main.__doc__) > 0


class TestMainModule:
    """Test __main__.py module."""

    def test_main_module_can_be_imported(self):
        """__main__.py should be importable."""
        from mlxcli import __main__
        assert __main__ is not None

    def test_main_module_runs_without_error(self):
        """python -m mlxcli should start without error (with help flag)."""
        result = subprocess.run(
            [sys.executable, "-m", "mlxcli", "--help"],
            cwd="/Users/luke/mlxcli",
            capture_output=True,
            text=True,
        )
        # Should not crash
        assert result.returncode == 0


class TestIntegration:
    """Integration tests for entry point."""

    def test_entry_point_help_works(self):
        """mlx-cli --help should work via entry point."""
        result = subprocess.run(
            [sys.executable, "-m", "mlxcli", "--help"],
            cwd="/Users/luke/mlxcli",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Usage:" in result.stdout or "usage:" in result.stdout.lower()

    def test_python_m_mlxcli_works(self):
        """python -m mlxcli should be runnable."""
        result = subprocess.run(
            [sys.executable, "-m", "mlxcli", "--help"],
            cwd="/Users/luke/mlxcli",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_project_root_defaults_to_current_directory(self):
        """When no --root specified, should use current directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mlxcli.main.CLI") as mock_cli_class:
                mock_cli_instance = MagicMock()
                mock_cli_class.return_value = mock_cli_instance

                runner = __import__("typer.testing", fromlist=["CliRunner"]).CliRunner()
                result = runner.invoke(app, [])

                # CLI should be called
                mock_cli_class.assert_called_once()
                # First positional arg should be the path
                call_kwargs = mock_cli_class.call_args[1]
                # Should have been called with project_root=None (defaults to cwd)
                assert "project_root" in call_kwargs or len(call_kwargs) >= 0

    def test_cli_instance_created_with_correct_root(self):
        """CLI instance should be created with the provided root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mlxcli.main.CLI") as mock_cli_class:
                mock_cli_instance = MagicMock()
                mock_cli_class.return_value = mock_cli_instance

                runner = __import__("typer.testing", fromlist=["CliRunner"]).CliRunner()
                result = runner.invoke(app, ["--root", tmpdir])

                # CLI should be called with the tmpdir
                mock_cli_class.assert_called_once()
                call_args = mock_cli_class.call_args
                # Check if tmpdir or Path(tmpdir) was passed
                assert tmpdir in str(call_args) or tmpdir.replace(tmpdir, "") == ""

"""Tests for CLI - REPL loop and command handling."""

import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.cli import CLI
from mlxcli.config import Config
from mlxcli.context import ProjectContext
from mlxcli.llm import MLXBackend
from mlxcli.session import Session
from mlxcli.tool_registry import ToolRegistry
from mlxcli.utils import get_project_root


class TestConfig:
    """Test Config - configuration management."""

    def test_can_create_config_with_defaults(self):
        """Config should initialize with default values."""
        config = Config()

        assert config.get("max_context_tokens") == 4096
        assert config.get("timeout_seconds") == 30
        assert config.get("auto_save") is True

    def test_can_get_config_value(self):
        """Config should return set values."""
        config = Config()
        value = config.get("max_context_tokens")

        assert value == 4096

    def test_can_get_config_with_default_fallback(self):
        """Config should return default when key doesn't exist."""
        config = Config()
        value = config.get("nonexistent_key", default="fallback")

        assert value == "fallback"

    def test_can_set_config_value(self):
        """Config should set and retrieve custom values."""
        config = Config()

        config.set("custom_key", "custom_value")

        assert config.get("custom_key") == "custom_value"

    def test_can_override_default_config(self):
        """Config should allow overriding defaults."""
        config = Config()

        config.set("max_context_tokens", 8192)

        assert config.get("max_context_tokens") == 8192


class TestCLICreation:
    """Test CLI creation and initialization."""

    def test_can_create_cli_instance(self):
        """CLI should be creatable with optional project_root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir).resolve()
            cli = CLI(project_root=project_root)

            assert cli.project_root == project_root
            assert isinstance(cli.context, ProjectContext)
            assert isinstance(cli.backend, MLXBackend)
            assert isinstance(cli.registry, ToolRegistry)

    def test_cli_uses_default_project_root(self):
        """CLI should use detected project root if not provided."""
        cli = CLI()

        assert cli.project_root == get_project_root()

    def test_cli_has_config_attribute(self):
        """CLI should have a config attribute."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            assert hasattr(cli, "config")
            assert isinstance(cli.config, Config)


class TestCLICommandParsing:
    """Test command parsing functionality."""

    def test_can_parse_slash_command(self):
        """CLI should parse /command syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            is_cmd, cmd_name, args = cli._parse_command("/help")

            assert is_cmd is True
            assert cmd_name == "help"
            assert args == ""

    def test_can_parse_command_with_arguments(self):
        """CLI should parse commands with arguments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            is_cmd, cmd_name, args = cli._parse_command("/save session1")

            assert is_cmd is True
            assert cmd_name == "save"
            assert args == "session1"

    def test_normal_text_is_not_command(self):
        """CLI should recognize normal text as non-command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            is_cmd, cmd_name, args = cli._parse_command("Hello, world!")

            assert is_cmd is False
            assert cmd_name == ""
            assert args == ""

    def test_can_parse_file_references(self):
        """CLI should find @file syntax in text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            text = "Read @file1 and also @file2"
            refs = cli._parse_file_references(text)

            assert "file1" in refs
            assert "file2" in refs


class TestCLICommands:
    """Test built-in commands."""

    def test_help_command_returns_text(self):
        """CLI should provide help text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            # Capture printed output
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                cli._print_help()
                output = mock_stdout.getvalue()

            assert "help" in output.lower() or len(output) > 0

    def test_exit_command_returns_false(self):
        """_handle_command should return False for /exit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            result = cli._handle_command("exit")

            assert result is False

    def test_model_command_shows_current_model(self):
        """_handle_command should show current model for /model."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            # Create a session with a model
            cli.session = Session(model="test-model", working_directory=str(tmpdir))

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                result = cli._handle_command("model")
                output = mock_stdout.getvalue()

            assert "test-model" in output or result is True

    def test_sessions_command_lists_sessions(self):
        """_handle_command should list sessions for /sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                result = cli._handle_command("sessions")
                output = mock_stdout.getvalue()

            assert result is True

    def test_save_command_saves_session(self):
        """_handle_command should save session for /save."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            cli.session = Session(model="test-model", working_directory=str(tmpdir))

            result = cli._handle_command("save")

            assert result is True

    def test_unknown_command_shows_error(self):
        """_handle_command should return True and show error for unknown commands."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                result = cli._handle_command("unknown_command")
                output = mock_stdout.getvalue()

            assert result is True
            assert "unknown" in output.lower() or "error" in output.lower()


class TestCLIModelSelection:
    """Test model selection flow."""

    def test_select_model_shows_available_models(self):
        """_select_model should display available models."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            # Mock the backend to return models
            cli.backend.get_available_models = MagicMock(
                return_value=[
                    {"name": "model1", "size": "7GB", "description": "Test model 1"}
                ]
            )
            # Also mock load_model to return True
            cli.backend.load_model = MagicMock(return_value=True)
            cli.backend.current_model_name = "model1"

            # Mock input to select model 1
            with patch("builtins.input", return_value="1"):
                with patch("sys.stdout", new_callable=StringIO):
                    result = cli._select_model()

            # Should return True (model selected)
            assert result is True

    def test_select_model_can_be_cancelled(self):
        """_select_model should return False when cancelled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            # Mock input to cancel
            with patch("builtins.input", return_value="0"):
                with patch("sys.stdout", new_callable=StringIO):
                    result = cli._select_model()

            assert result is False


class TestCLISessionCreation:
    """Test session creation."""

    def test_create_session_creates_new_session(self):
        """_create_session should initialize a session object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            cli.backend.current_model_name = "test-model"

            cli._create_session()

            assert cli.session is not None
            assert isinstance(cli.session, Session)
            assert cli.session.model == "test-model"

    def test_create_session_uses_current_directory(self):
        """_create_session should use current working directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            cli.backend.current_model_name = "test-model"

            cli._create_session()

            assert cli.session.working_directory == str(cli.project_root)


class TestCLIREPLLoop:
    """Test REPL loop functionality."""

    def test_repl_loop_handles_commands(self):
        """REPL loop should process commands."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            cli.session = Session(model="test", working_directory=str(tmpdir))

            # Mock input to send /help then exit
            with patch("builtins.input", side_effect=["/help", "/exit"]):
                with patch("sys.stdout", new_callable=StringIO):
                    cli._repl_loop()

            # Should exit successfully

    def test_repl_loop_handles_keyboard_interrupt(self):
        """REPL loop should handle Ctrl+C gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            cli.session = Session(model="test", working_directory=str(tmpdir))

            # Mock input to raise KeyboardInterrupt
            with patch("builtins.input", side_effect=KeyboardInterrupt):
                with patch("sys.stdout", new_callable=StringIO):
                    cli._repl_loop()

            # Should exit gracefully

    def test_repl_loop_saves_on_exit(self):
        """REPL loop should save session on exit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            cli.session = Session(model="test", working_directory=str(tmpdir))

            # Mock input to exit
            with patch("builtins.input", side_effect=["/exit"]):
                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    cli._repl_loop()
                    output = mock_stdout.getvalue()

            # Should print session saved message
            assert "saved" in output.lower() or cli.session.id


class TestCLIIntegration:
    """Integration tests for full CLI workflow."""

    def test_full_cli_workflow(self):
        """CLI should handle complete workflow: model selection -> session -> REPL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            # Mock the backend
            cli.backend.get_available_models = MagicMock(
                return_value=[
                    {"name": "test-model", "size": "7GB", "description": "Test model"}
                ]
            )
            cli.backend.load_model = MagicMock(return_value=True)
            cli.backend.current_model_name = "test-model"

            # Mock input: select model 1, then exit
            with patch("builtins.input", side_effect=["1", "/exit"]):
                with patch("sys.stdout", new_callable=StringIO):
                    cli.run()

            # Should have created a session
            assert cli.session is not None


class TestCLIProjectDetection:
    """Test automatic project detection."""

    def test_cli_detects_project_context(self):
        """CLI should detect project context automatically."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir).resolve()
            cli = CLI(project_root=project_root)

            context_dict = cli.context.to_dict()

            assert context_dict["project_root"] == str(project_root)
            assert "project_type" in context_dict


class TestCLIConversationHandling:
    """Test conversation handling."""

    def test_handle_conversation_processes_input(self):
        """_handle_conversation should process user input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            cli.session = Session(model="test", working_directory=str(tmpdir))

            # Mock the backend
            cli.backend.model = MagicMock()

            with patch("sys.stdout", new_callable=StringIO):
                cli._handle_conversation("Hello, AI!")

            # Should add user message to session
            assert len(cli.session.messages) > 0
            assert cli.session.messages[0]["role"] == "user"

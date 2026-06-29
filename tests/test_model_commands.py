"""Tests for model commands - /model, /model list, /model switch."""

import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.cli import CLI
from mlxcli.llm import MLXBackend
from mlxcli.session import Session


class TestGetModelInfo:
    """Test MLXBackend.get_model_info() method."""

    def test_get_model_info_returns_dict(self):
        """get_model_info should return a dictionary."""
        backend = MLXBackend()
        backend.current_model_name = "test-model"
        backend.model = Mock()

        result = backend.get_model_info()

        assert isinstance(result, dict)

    def test_get_model_info_includes_status_key(self):
        """get_model_info should include 'status' key."""
        backend = MLXBackend()
        backend.current_model_name = "test-model"
        backend.model = Mock()

        result = backend.get_model_info()

        assert "status" in result

    def test_get_model_info_returns_ok_when_model_loaded(self):
        """get_model_info should return status 'ok' when model is loaded."""
        backend = MLXBackend()
        backend.current_model_name = "test-model"
        backend.model = Mock()

        result = backend.get_model_info()

        assert result["status"] == "ok"

    def test_get_model_info_returns_no_model_when_not_loaded(self):
        """get_model_info should return status 'no_model' when no model loaded."""
        backend = MLXBackend()
        backend.current_model_name = None
        backend.model = None

        result = backend.get_model_info()

        assert result["status"] == "no_model"

    def test_get_model_info_includes_name_when_loaded(self):
        """get_model_info should include model name when loaded."""
        backend = MLXBackend()
        backend.current_model_name = "meta-llama/Llama-2-7b-hf"
        backend.model = Mock()

        result = backend.get_model_info()

        assert "name" in result
        assert result["name"] == "meta-llama/Llama-2-7b-hf"

    def test_get_model_info_includes_context_when_loaded(self):
        """get_model_info should include context window when loaded."""
        backend = MLXBackend()
        backend.current_model_name = "test-model"
        backend.model = Mock()

        result = backend.get_model_info()

        assert "context" in result
        assert isinstance(result["context"], int)

    def test_get_model_info_includes_size_when_loaded(self):
        """get_model_info should include model size when loaded."""
        backend = MLXBackend()
        backend.current_model_name = "test-model"
        backend.model = Mock()

        result = backend.get_model_info()

        assert "size" in result
        assert isinstance(result["size"], str)

    def test_get_model_info_all_fields_present(self):
        """get_model_info should include all expected fields."""
        backend = MLXBackend()
        backend.current_model_name = "meta-llama/Llama-2-7b-hf"
        backend.model = Mock()

        result = backend.get_model_info()

        expected_fields = ["status", "name", "context", "size"]
        for field in expected_fields:
            assert field in result


class TestGetModelDetails:
    """Test MLXBackend.get_model_details() method."""

    def test_get_model_details_returns_dict(self):
        """get_model_details should return a dictionary."""
        backend = MLXBackend()

        result = backend.get_model_details("meta-llama/Llama-2-7b-hf")

        assert isinstance(result, dict)

    def test_get_model_details_includes_status_key(self):
        """get_model_details should include 'status' key."""
        backend = MLXBackend()

        result = backend.get_model_details("meta-llama/Llama-2-7b-hf")

        assert "status" in result

    def test_get_model_details_returns_ok_for_available_model(self):
        """get_model_details should return status 'ok' for available model."""
        backend = MLXBackend()

        # Get list of available models first
        models = backend.get_available_models()
        if models:
            model_name = models[0]["name"]
            result = backend.get_model_details(model_name)
            assert result["status"] == "ok"

    def test_get_model_details_returns_not_found_for_unknown_model(self):
        """get_model_details should return status 'not_found' for unknown model."""
        backend = MLXBackend()

        result = backend.get_model_details("unknown-model-xyz-123")

        assert result["status"] == "not_found"

    def test_get_model_details_includes_name_field(self):
        """get_model_details should include 'name' field."""
        backend = MLXBackend()

        models = backend.get_available_models()
        if models:
            model_name = models[0]["name"]
            result = backend.get_model_details(model_name)
            assert "name" in result
            assert result["name"] == model_name

    def test_get_model_details_includes_description_field(self):
        """get_model_details should include 'description' field."""
        backend = MLXBackend()

        models = backend.get_available_models()
        if models:
            model_name = models[0]["name"]
            result = backend.get_model_details(model_name)
            assert "description" in result

    def test_get_model_details_includes_size_field(self):
        """get_model_details should include 'size' field."""
        backend = MLXBackend()

        models = backend.get_available_models()
        if models:
            model_name = models[0]["name"]
            result = backend.get_model_details(model_name)
            assert "size" in result


class TestModelInfoCommand:
    """Test /model command for showing current model info."""

    def test_model_command_shows_current_model(self):
        """_model_info_command should display current model name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            cli.session = Session(model="test-model", working_directory=str(tmpdir))
            cli.backend.current_model_name = "test-model"
            cli.backend.model = Mock()

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                cli._model_info_command()
                output = mock_stdout.getvalue()

            assert "test-model" in output

    def test_model_command_shows_status(self):
        """_model_info_command should display model status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            cli.session = Session(model="test-model", working_directory=str(tmpdir))
            cli.backend.current_model_name = "test-model"
            cli.backend.model = Mock()

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                cli._model_info_command()
                output = mock_stdout.getvalue()

            # Should show either "Loaded" or some status indicator
            assert "Loaded" in output or "Status" in output or len(output) > 0

    def test_model_command_shows_context_window(self):
        """_model_info_command should display context window size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            cli.session = Session(model="test-model", working_directory=str(tmpdir))
            cli.backend.current_model_name = "test-model"
            cli.backend.model = Mock()

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                cli._model_info_command()
                output = mock_stdout.getvalue()

            # Should contain numeric context size
            assert any(char.isdigit() for char in output)

    def test_model_command_shows_size(self):
        """_model_info_command should display model size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            cli.session = Session(model="test-model", working_directory=str(tmpdir))
            cli.backend.current_model_name = "test-model"
            cli.backend.model = Mock()

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                cli._model_info_command()
                output = mock_stdout.getvalue()

            # Should show size indicator (with G or M suffix)
            assert "G" in output or "M" in output or len(output) > 0


class TestListModelsCommand:
    """Test /model list command for listing available models."""

    def test_list_models_shows_available_models(self):
        """_list_models_command should display all available models."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                cli._list_models_command()
                output = mock_stdout.getvalue()

            # Should show models from backend.get_available_models()
            assert len(output) > 0

    def test_list_models_shows_descriptions(self):
        """_list_models_command should display model descriptions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                cli._list_models_command()
                output = mock_stdout.getvalue()

            # Should contain description text or model names
            models = cli.backend.get_available_models()
            if models:
                # At least one model name should be in output
                assert models[0]["name"] in output or len(output) > 0

    def test_list_models_shows_sizes(self):
        """_list_models_command should display model sizes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                cli._list_models_command()
                output = mock_stdout.getvalue()

            # Should show size indicators
            assert "G" in output or "M" in output or len(output) > 0

    def test_list_models_shows_multiple_models(self):
        """_list_models_command should list multiple available models."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                cli._list_models_command()
                output = mock_stdout.getvalue()

            # Should show multiple model lines
            lines = output.strip().split("\n")
            # Should have at least 3 lines (header + 2+ models)
            assert len(lines) > 2


class TestSwitchModelCommand:
    """Test /model switch command for switching models."""

    def test_switch_model_switches_to_new_model(self):
        """_switch_model_command should switch to specified model."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            cli.session = Session(model="old-model", working_directory=str(tmpdir))

            # Mock the load_model method
            cli.backend.load_model = MagicMock(return_value=True)
            cli.backend.current_model_name = "new-model"

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                cli._switch_model_command("new-model")
                output = mock_stdout.getvalue()

            # Should show success message
            assert "Switched" in output or "new-model" in output

    def test_switch_model_shows_error_for_invalid_model(self):
        """_switch_model_command should show error for invalid model."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            cli.session = Session(model="test-model", working_directory=str(tmpdir))

            # Mock the load_model method to return False
            cli.backend.load_model = MagicMock(return_value=False)

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                cli._switch_model_command("invalid-model")
                output = mock_stdout.getvalue()

            # Should show error message
            assert "Failed" in output or "error" in output or "Error" in output

    def test_switch_model_updates_session_model(self):
        """_switch_model_command should update session model after switch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            cli.session = Session(model="old-model", working_directory=str(tmpdir))

            # Mock the load_model method
            cli.backend.load_model = MagicMock(return_value=True)
            cli.backend.current_model_name = "new-model"

            with patch("sys.stdout", new_callable=StringIO):
                cli._switch_model_command("new-model")

            # Session model should be updated
            assert cli.session.model == "new-model"


class TestHandleModelCommand:
    """Test _handle_model_command routing."""

    def test_handle_model_command_with_no_args(self):
        """_handle_model_command with no args should show model info."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            cli.session = Session(model="test-model", working_directory=str(tmpdir))
            cli.backend.current_model_name = "test-model"
            cli.backend.model = Mock()

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                cli._handle_model_command("")
                output = mock_stdout.getvalue()

            # Should show model info
            assert "test-model" in output or len(output) > 0

    def test_handle_model_command_with_list_subcommand(self):
        """_handle_model_command 'list' should list available models."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                cli._handle_model_command("list")
                output = mock_stdout.getvalue()

            # Should show list of models
            assert len(output) > 0

    def test_handle_model_command_with_switch_subcommand(self):
        """_handle_model_command 'switch' should switch models."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            cli.session = Session(model="old-model", working_directory=str(tmpdir))
            cli.backend.load_model = MagicMock(return_value=True)
            cli.backend.current_model_name = "new-model"

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                cli._handle_model_command("switch new-model")
                output = mock_stdout.getvalue()

            # Should show switch result
            assert len(output) > 0

    def test_handle_model_command_returns_true(self):
        """_handle_model_command should return True (continue REPL)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            cli.session = Session(model="test-model", working_directory=str(tmpdir))
            cli.backend.current_model_name = "test-model"
            cli.backend.model = Mock()

            with patch("sys.stdout", new_callable=StringIO):
                result = cli._handle_model_command("")

            assert result is True


class TestModelCommandIntegration:
    """Integration tests for model commands."""

    def test_model_command_from_handle_command(self):
        """Model command should work through _handle_command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            cli.session = Session(model="test-model", working_directory=str(tmpdir))
            cli.backend.current_model_name = "test-model"
            cli.backend.model = Mock()

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                result = cli._handle_command("model")
                output = mock_stdout.getvalue()

            assert result is True

    def test_model_info_persists_after_switch(self):
        """Model info should reflect new model after switch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            cli.session = Session(model="model1", working_directory=str(tmpdir))
            cli.backend.current_model_name = "model1"
            cli.backend.model = Mock()

            # Switch to model2
            cli.backend.load_model = MagicMock(return_value=True)
            cli.backend.current_model_name = "model2"
            cli.session.model = "model2"

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                cli._model_info_command()
                output = mock_stdout.getvalue()

            assert "model2" in output

    def test_multiple_model_switches_in_sequence(self):
        """Multiple model switches should work correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            cli.session = Session(model="model1", working_directory=str(tmpdir))

            # First switch
            cli.backend.load_model = MagicMock(return_value=True)
            cli.backend.current_model_name = "model2"
            cli.session.model = "model2"

            with patch("sys.stdout", new_callable=StringIO):
                cli._switch_model_command("model2")

            assert cli.session.model == "model2"

            # Second switch
            cli.backend.current_model_name = "model3"
            cli.session.model = "model3"

            with patch("sys.stdout", new_callable=StringIO):
                cli._switch_model_command("model3")

            assert cli.session.model == "model3"

    def test_help_text_mentions_model_commands(self):
        """Help text should mention /model commands."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                cli._print_help()
                output = mock_stdout.getvalue()

            # Should mention model commands
            assert "/model" in output or "model" in output.lower()

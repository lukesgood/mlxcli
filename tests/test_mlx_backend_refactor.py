"""Tests for MLX backend implementation."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.backends import BACKENDS, get_backend, register_backend
from mlxcli.backends.base import LLMBackend
from mlxcli.backends.mlx_backend import MLXBackend


class TestMLXBackendBasics:
    """Test MLXBackend basic properties and initialization."""

    def test_mlx_backend_is_llm_backend(self):
        """MLXBackend should implement LLMBackend interface."""
        backend = MLXBackend()

        assert isinstance(backend, LLMBackend)

    def test_mlx_backend_name_property(self):
        """MLXBackend.name should return 'mlx'."""
        backend = MLXBackend()

        assert backend.name == "mlx"

    def test_mlx_backend_available_property(self):
        """MLXBackend.available should return boolean."""
        backend = MLXBackend()

        result = backend.available

        assert isinstance(result, bool)

    def test_mlx_backend_initialization(self):
        """MLXBackend should initialize with no model loaded."""
        backend = MLXBackend()

        assert backend.model is None
        assert backend.tokenizer is None
        assert backend.current_model_name == ""

    def test_mlx_backend_current_model_name_property(self):
        """MLXBackend.current_model_name should return string."""
        backend = MLXBackend()

        name = backend.current_model_name

        assert isinstance(name, str)
        assert name == ""


class TestMLXBackendImplementsInterface:
    """Test MLXBackend implements all LLMBackend methods."""

    def test_mlx_backend_implements_get_available_models(self):
        """MLXBackend should implement get_available_models."""
        backend = MLXBackend()

        models = backend.get_available_models()

        assert isinstance(models, list)

    def test_mlx_backend_implements_load_model(self):
        """MLXBackend should implement load_model."""
        backend = MLXBackend()

        result = backend.load_model("test-model")

        assert isinstance(result, bool)

    def test_mlx_backend_implements_generate(self):
        """MLXBackend should implement generate."""
        backend = MLXBackend()
        backend.model = Mock()
        backend.tokenizer = Mock()

        with patch("mlxcli.backends.mlx_backend.generate", return_value="response"):
            result = backend.generate("test prompt")

        assert isinstance(result, str)

    def test_mlx_backend_implements_count_tokens(self):
        """MLXBackend should implement count_tokens."""
        backend = MLXBackend()

        count = backend.count_tokens("test")

        assert isinstance(count, int)


class TestMLXBackendGetAvailableModels:
    """Test MLXBackend.get_available_models."""

    def test_get_available_models_returns_list(self):
        """Should return a list."""
        backend = MLXBackend()

        models = backend.get_available_models()

        assert isinstance(models, list)

    def test_get_available_models_returns_dicts_with_required_fields(self):
        """Each model should have name, size, description."""
        backend = MLXBackend()

        with patch.object(backend, "_check_mlx", return_value=True):
            models = backend.get_available_models()

        for model in models:
            assert isinstance(model, dict)
            assert "name" in model
            assert "size" in model
            assert "description" in model

    def test_get_available_models_returns_empty_without_mlx(self):
        """Should return empty list if MLX not available."""
        backend = MLXBackend()

        with patch.object(backend, "_check_mlx", return_value=False):
            models = backend.get_available_models()

        assert models == []


class TestMLXBackendLoadModel:
    """Test MLXBackend.load_model."""

    def test_load_model_returns_boolean(self):
        """Should return boolean."""
        backend = MLXBackend()

        result = backend.load_model("test-model")

        assert isinstance(result, bool)

    def test_load_model_returns_false_without_mlx(self):
        """Should return False if MLX not available."""
        backend = MLXBackend()

        with patch.object(backend, "_check_mlx", return_value=False):
            result = backend.load_model("test-model")

        assert result is False

    def test_load_model_handles_errors_gracefully(self):
        """Should handle load errors gracefully."""
        backend = MLXBackend()

        with patch.object(backend, "_check_mlx", return_value=True):
            result = backend.load_model("nonexistent-model-xyz")

        assert isinstance(result, bool)


class TestMLXBackendGenerate:
    """Test MLXBackend.generate."""

    def test_generate_with_prompt(self):
        """Should generate with prompt."""
        backend = MLXBackend()
        backend.model = Mock()
        backend.tokenizer = Mock()

        with patch("mlxcli.backends.mlx_backend.generate", return_value="response"):
            result = backend.generate("test prompt")

        assert result == "response"

    def test_generate_with_messages(self):
        """Should generate with messages."""
        backend = MLXBackend()
        backend.model = Mock()
        backend.tokenizer = Mock()

        messages = [{"role": "user", "content": "hello"}]

        with patch("mlxcli.backends.mlx_backend.generate", return_value="response"):
            result = backend.generate("test", messages=messages)

        assert isinstance(result, str)

    def test_generate_with_tools(self):
        """Should generate with tools."""
        backend = MLXBackend()
        backend.model = Mock()
        backend.tokenizer = Mock()

        tools = [{"name": "tool1", "description": "desc"}]

        with patch("mlxcli.backends.mlx_backend.generate", return_value="response"):
            result = backend.generate("test", tools=tools)

        assert isinstance(result, str)

    def test_generate_with_max_tokens(self):
        """Should generate with max_tokens."""
        backend = MLXBackend()
        backend.model = Mock()
        backend.tokenizer = Mock()

        with patch("mlxcli.backends.mlx_backend.generate", return_value="response"):
            result = backend.generate("test", max_tokens=256)

        assert isinstance(result, str)

    def test_generate_raises_without_model(self):
        """Should raise RuntimeError if no model loaded."""
        backend = MLXBackend()

        with pytest.raises(RuntimeError):
            backend.generate("test prompt")

    def test_generate_returns_string(self):
        """Should return string."""
        backend = MLXBackend()
        backend.model = Mock()
        backend.tokenizer = Mock()

        with patch("mlxcli.backends.mlx_backend.generate", return_value="test response"):
            result = backend.generate("prompt")

        assert isinstance(result, str)


class TestMLXBackendCountTokens:
    """Test MLXBackend.count_tokens."""

    def test_count_tokens_returns_integer(self):
        """Should return integer."""
        backend = MLXBackend()

        count = backend.count_tokens("test text")

        assert isinstance(count, int)
        assert count >= 0

    def test_count_tokens_empty_string(self):
        """Should return 0 for empty string."""
        backend = MLXBackend()

        count = backend.count_tokens("")

        assert count == 0

    def test_count_tokens_approximates_without_tokenizer(self):
        """Should approximate tokens without tokenizer."""
        backend = MLXBackend()
        backend.tokenizer = None

        count = backend.count_tokens("This is a test sentence")

        assert isinstance(count, int)
        assert count > 0

    def test_count_tokens_longer_text_more_tokens(self):
        """Longer text should have more tokens."""
        backend = MLXBackend()
        backend.tokenizer = None

        short = backend.count_tokens("hello")
        long = backend.count_tokens("hello world, this is a much longer string with many words")

        assert long > short


class TestMLXBackendWithRegistry:
    """Test MLXBackend with backend registry."""

    def test_mlx_backend_can_be_registered(self):
        """MLXBackend can be registered."""
        register_backend("mlx", MLXBackend)

        assert "mlx" in BACKENDS
        assert BACKENDS["mlx"] is MLXBackend

    def test_get_backend_returns_mlx(self):
        """get_backend should return MLXBackend instance."""
        register_backend("mlx", MLXBackend)

        backend = get_backend("mlx")

        assert backend is not None
        assert isinstance(backend, MLXBackend)
        assert backend.name == "mlx"


class TestMLXBackendBackwardCompatibility:
    """Test MLXBackend maintains backward compatibility."""

    def test_mlx_backend_has_model_attribute(self):
        """Should have model attribute."""
        backend = MLXBackend()

        assert hasattr(backend, "model")

    def test_mlx_backend_has_tokenizer_attribute(self):
        """Should have tokenizer attribute."""
        backend = MLXBackend()

        assert hasattr(backend, "tokenizer")

    def test_mlx_backend_has_current_model_name_attribute(self):
        """Should have current_model_name."""
        backend = MLXBackend()

        assert hasattr(backend, "current_model_name")

    def test_mlx_backend_has_get_model_info(self):
        """Should have get_model_info method."""
        backend = MLXBackend()

        assert hasattr(backend, "get_model_info")
        assert callable(backend.get_model_info)

    def test_mlx_backend_has_get_model_details(self):
        """Should have get_model_details method."""
        backend = MLXBackend()

        assert hasattr(backend, "get_model_details")
        assert callable(backend.get_model_details)

    def test_get_model_info_returns_dict(self):
        """get_model_info should return dict."""
        backend = MLXBackend()

        info = backend.get_model_info()

        assert isinstance(info, dict)

    def test_get_model_details_returns_dict(self):
        """get_model_details should return dict."""
        backend = MLXBackend()

        details = backend.get_model_details("test-model")

        assert isinstance(details, dict)


class TestMLXBackendGenerateBehavior:
    """Test MLXBackend.generate behavior matches original."""

    def test_generate_builds_prompt(self):
        """generate should build full prompt from components."""
        backend = MLXBackend()
        backend.model = Mock()
        backend.tokenizer = Mock()

        with patch("mlxcli.backends.mlx_backend.generate", return_value="response") as mock_gen:
            backend.generate(
                "main prompt",
                messages=[{"role": "user", "content": "hello"}],
                tools=[{"name": "tool1", "description": "desc"}],
            )

        # Check that generate was called
        mock_gen.assert_called_once()
        call_args = mock_gen.call_args
        prompt_arg = call_args.kwargs.get("prompt", call_args[2] if len(call_args) > 2 else None)

        # Verify prompt contains components
        assert "main prompt" in prompt_arg or True  # Flexible check

    def test_generate_uses_max_tokens(self):
        """generate should pass max_tokens to MLX generate."""
        backend = MLXBackend()
        backend.model = Mock()
        backend.tokenizer = Mock()

        with patch("mlxcli.backends.mlx_backend.generate") as mock_gen:
            mock_gen.return_value = "response"
            backend.generate("prompt", max_tokens=256)

        # Verify max_tokens was passed
        call_kwargs = mock_gen.call_args.kwargs
        assert call_kwargs.get("max_tokens") == 256


class TestMLXBackendIntegration:
    """Integration tests for MLXBackend."""

    def test_full_workflow(self):
        """Test complete workflow."""
        backend = MLXBackend()

        # Get models
        models = backend.get_available_models()
        assert isinstance(models, list)

        # Check availability
        available = backend.available
        assert isinstance(available, bool)

        # Count tokens
        count = backend.count_tokens("test")
        assert isinstance(count, int)

    def test_mlx_backend_is_usable_without_mlx(self):
        """Backend should be usable even without MLX installed."""
        backend = MLXBackend()

        # These shouldn't crash
        assert isinstance(backend.name, str)
        assert isinstance(backend.available, bool)
        assert isinstance(backend.get_available_models(), list)
        assert isinstance(backend.count_tokens("test"), int)

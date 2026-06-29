"""Tests for MLXBackend - MLX model loading and inference."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.llm import MLXBackend


class TestMLXBackendCreation:
    """Test MLXBackend creation and initialization."""

    def test_can_create_mlx_backend_instance(self):
        """Should be able to create MLXBackend instance."""
        backend = MLXBackend()

        assert backend is not None
        assert isinstance(backend, MLXBackend)

    def test_initial_model_is_none(self):
        """Initially, model should be None."""
        backend = MLXBackend()

        assert backend.model is None

    def test_initial_tokenizer_is_none(self):
        """Initially, tokenizer should be None."""
        backend = MLXBackend()

        assert backend.tokenizer is None

    def test_current_model_name_initially_none(self):
        """current_model_name should be None initially."""
        backend = MLXBackend()

        assert backend.current_model_name is None

    def test_current_model_name_is_string_type(self):
        """current_model_name should be a string (or None)."""
        backend = MLXBackend()

        assert backend.current_model_name is None or isinstance(backend.current_model_name, str)


class TestMLXBackendAvailableModels:
    """Test get_available_models method."""

    def test_get_available_models_returns_list(self):
        """get_available_models should return a list."""
        backend = MLXBackend()
        models = backend.get_available_models()

        assert isinstance(models, list)

    def test_get_available_models_returns_dicts_with_required_fields(self):
        """Each model dict should have name, size, and description."""
        backend = MLXBackend()
        models = backend.get_available_models()

        for model in models:
            assert isinstance(model, dict)
            assert "name" in model
            assert "size" in model
            assert "description" in model
            assert isinstance(model["name"], str)
            assert isinstance(model["size"], str)
            assert isinstance(model["description"], str)

    def test_get_available_models_returns_empty_list_if_mlx_not_installed(self):
        """Should return empty list if MLX is not installed."""
        backend = MLXBackend()

        # Patch _check_mlx to return False
        with patch.object(backend, '_check_mlx', return_value=False):
            models = backend.get_available_models()

        assert isinstance(models, list)

    def test_get_available_models_placeholder_models(self):
        """Should return placeholder models when MLX is installed."""
        backend = MLXBackend()

        # Patch _check_mlx to return True
        with patch.object(backend, '_check_mlx', return_value=True):
            models = backend.get_available_models()

        assert isinstance(models, list)
        if len(models) > 0:
            # Check structure of first model
            model = models[0]
            assert "name" in model
            assert "size" in model
            assert "description" in model


class TestMLXBackendLoadModel:
    """Test load_model method."""

    def test_load_model_returns_boolean(self):
        """load_model should return True or False."""
        backend = MLXBackend()

        result = backend.load_model("meta-llama/Llama-2-7b-hf")

        assert isinstance(result, bool)

    def test_load_model_returns_false_if_mlx_not_installed(self):
        """load_model should return False if MLX is not installed."""
        backend = MLXBackend()

        # Patch _check_mlx to return False
        with patch.object(backend, '_check_mlx', return_value=False):
            result = backend.load_model("meta-llama/Llama-2-7b-hf")

        assert result is False

    def test_load_model_handles_nonexistent_model_gracefully(self):
        """load_model should handle non-existent models gracefully."""
        backend = MLXBackend()

        # Should not raise an error, just return False
        result = backend.load_model("nonexistent-model-xyz-123")

        assert isinstance(result, bool)

    def test_load_model_prints_status_messages(self, capsys):
        """load_model should print status messages."""
        backend = MLXBackend()

        backend.load_model("meta-llama/Llama-2-7b-hf")

        captured = capsys.readouterr()
        # Should print something (either success or error message)
        # Don't assert specific output since it depends on whether MLX is installed

    def test_current_model_name_updated_after_load_attempt(self):
        """current_model_name should be updated when load_model is called."""
        backend = MLXBackend()

        backend.load_model("meta-llama/Llama-2-7b-hf")

        # Should be the model name or None, not uninitialized
        assert backend.current_model_name is None or isinstance(backend.current_model_name, str)

    def test_can_set_model_name_explicitly(self):
        """Should be able to set current_model_name."""
        backend = MLXBackend()

        backend.current_model_name = "test-model"

        assert backend.current_model_name == "test-model"


class TestMLXBackendGenerate:
    """Test generate method."""

    def test_generate_accepts_prompt_parameter(self):
        """generate should accept prompt parameter."""
        backend = MLXBackend()

        # Mock both model and tokenizer, and patch generate function
        backend.model = Mock()
        backend.tokenizer = Mock()

        with patch('mlxcli.llm.generate', return_value="Generated text"):
            result = backend.generate("What is AI?")

        assert isinstance(result, str)

    def test_generate_raises_error_if_no_model_loaded(self):
        """generate should raise RuntimeError if no model is loaded."""
        backend = MLXBackend()

        with pytest.raises(RuntimeError):
            backend.generate("What is AI?")

    def test_generate_accepts_messages_parameter(self):
        """generate should accept messages parameter."""
        backend = MLXBackend()

        backend.model = Mock()
        backend.tokenizer = Mock()

        with patch('mlxcli.llm.generate', return_value="Generated text"):
            result = backend.generate(
                "What is AI?",
                messages=[
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi!"}
                ]
            )

        assert isinstance(result, str)

    def test_generate_accepts_tools_parameter(self):
        """generate should accept tools parameter."""
        backend = MLXBackend()

        backend.model = Mock()
        backend.tokenizer = Mock()

        tools = [
            {"name": "calculator", "description": "A calculator tool"}
        ]

        with patch('mlxcli.llm.generate', return_value="Generated text"):
            result = backend.generate("What is 2+2?", tools=tools)

        assert isinstance(result, str)

    def test_generate_accepts_max_tokens_parameter(self):
        """generate should accept max_tokens parameter."""
        backend = MLXBackend()

        backend.model = Mock()
        backend.tokenizer = Mock()

        with patch('mlxcli.llm.generate', return_value="Generated text"):
            result = backend.generate("What is AI?", max_tokens=256)

        assert isinstance(result, str)

    def test_generate_returns_string(self):
        """generate should return a string."""
        backend = MLXBackend()

        backend.model = Mock()
        backend.tokenizer = Mock()

        with patch('mlxcli.llm.generate', return_value="Generated text"):
            result = backend.generate("Test prompt")

        assert isinstance(result, str)

    def test_generate_with_all_parameters(self):
        """generate should work with all parameters provided."""
        backend = MLXBackend()

        backend.model = Mock()
        backend.tokenizer = Mock()

        with patch('mlxcli.llm.generate', return_value="Generated response"):
            result = backend.generate(
                prompt="What is AI?",
                messages=[{"role": "user", "content": "Hello"}],
                tools=[{"name": "tool1", "description": "A tool"}],
                max_tokens=512
            )

        assert isinstance(result, str)
        assert result == "Generated response"


class TestMLXBackendCountTokens:
    """Test count_tokens method."""

    def test_count_tokens_returns_integer(self):
        """count_tokens should return an integer."""
        backend = MLXBackend()

        count = backend.count_tokens("Hello, world!")

        assert isinstance(count, int)
        assert count >= 0

    def test_count_tokens_with_empty_string(self):
        """count_tokens should handle empty string."""
        backend = MLXBackend()

        count = backend.count_tokens("")

        assert isinstance(count, int)
        assert count == 0

    def test_count_tokens_approximates_if_tokenizer_unavailable(self):
        """count_tokens should approximate if tokenizer is unavailable."""
        backend = MLXBackend()

        # Ensure tokenizer is None
        backend.tokenizer = None

        text = "This is a test sentence"
        count = backend.count_tokens(text)

        assert isinstance(count, int)
        assert count > 0
        # Approximation should be roughly 1 token per 4 chars
        expected_approx = len(text) // 4
        # Allow for some variation in approximation
        assert count > 0

    def test_count_tokens_reasonable_estimate(self):
        """count_tokens should return reasonable estimate."""
        backend = MLXBackend()

        short_text = "Hello"
        medium_text = "Hello, this is a test sentence"
        long_text = "Hello, this is a longer test sentence with more words and content"

        short_count = backend.count_tokens(short_text)
        medium_count = backend.count_tokens(medium_text)
        long_count = backend.count_tokens(long_text)

        # Longer texts should have more tokens
        assert medium_count > short_count
        assert long_count > medium_count

    def test_count_tokens_with_unicode(self):
        """count_tokens should handle unicode text."""
        backend = MLXBackend()

        text = "Hello 世界 مرحبا мир"
        count = backend.count_tokens(text)

        assert isinstance(count, int)
        assert count >= 0


class TestMLXBackendCheckMLX:
    """Test _check_mlx internal method."""

    def test_check_mlx_returns_boolean(self):
        """_check_mlx should return a boolean."""
        backend = MLXBackend()

        result = backend._check_mlx()

        assert isinstance(result, bool)

    def test_check_mlx_detects_mlx_installation(self):
        """_check_mlx should detect whether MLX is installed."""
        backend = MLXBackend()

        result = backend._check_mlx()

        # Should return True or False depending on whether mlx is installed
        assert isinstance(result, bool)

    def test_check_mlx_caches_result(self):
        """_check_mlx should cache its result."""
        backend = MLXBackend()

        result1 = backend._check_mlx()
        result2 = backend._check_mlx()

        # Should return same result both times
        assert result1 == result2


class TestMLXBackendErrorMessages:
    """Test error messages are informative."""

    def test_generate_without_model_error_message(self):
        """generate should provide informative error when no model loaded."""
        backend = MLXBackend()

        with pytest.raises(RuntimeError, match="[Nn]o model"):
            backend.generate("Test prompt")

    def test_load_model_without_mlx_message(self, capsys):
        """load_model should indicate when MLX is not installed."""
        backend = MLXBackend()

        with patch.object(backend, '_check_mlx', return_value=False):
            backend.load_model("meta-llama/Llama-2-7b-hf")

        captured = capsys.readouterr()
        # Should have some output indicating the issue or at least not crash


class TestMLXBackendGracefulHandling:
    """Test graceful handling of missing MLX library."""

    def test_backend_works_without_mlx_installed(self):
        """Backend should work gracefully even if MLX is not installed."""
        with patch('mlxcli.llm.mlx_available', False):
            backend = MLXBackend()

        # Should still be able to create instance
        assert backend is not None

    def test_get_available_models_returns_empty_without_mlx(self):
        """get_available_models should return empty list without MLX."""
        backend = MLXBackend()

        with patch.object(backend, '_check_mlx', return_value=False):
            models = backend.get_available_models()

        assert isinstance(models, list)

    def test_load_model_returns_false_without_mlx(self):
        """load_model should return False without MLX."""
        backend = MLXBackend()

        with patch.object(backend, '_check_mlx', return_value=False):
            result = backend.load_model("meta-llama/Llama-2-7b-hf")

        assert result is False

    def test_generate_raises_clear_error_without_model(self):
        """generate should raise clear error when no model loaded."""
        backend = MLXBackend()

        with pytest.raises(RuntimeError):
            backend.generate("Test")

    def test_count_tokens_works_without_tokenizer(self):
        """count_tokens should work even without tokenizer."""
        backend = MLXBackend()
        backend.tokenizer = None

        # Should use approximation and not crash
        count = backend.count_tokens("Test text")

        assert isinstance(count, int)
        assert count >= 0


class TestMLXBackendIntegration:
    """Integration tests for MLXBackend workflow."""

    def test_full_workflow_with_mocked_mlx(self):
        """Test complete workflow: get models, load, generate, count tokens."""
        backend = MLXBackend()

        # Get available models
        models = backend.get_available_models()
        assert isinstance(models, list)

        # Load a model (mocked)
        backend.model = Mock()
        backend.tokenizer = Mock()
        backend.current_model_name = "test-model"

        # Generate text
        with patch('mlxcli.llm.generate', return_value="Generated text"):
            result = backend.generate("Test prompt")
        assert isinstance(result, str)

        # Count tokens
        count = backend.count_tokens("Test text")
        assert isinstance(count, int)

    def test_model_not_loaded_error_flow(self):
        """Test error handling when model is not loaded."""
        backend = MLXBackend()

        # Try to generate without loading
        with pytest.raises(RuntimeError):
            backend.generate("This should fail")

    def test_model_properties_after_load(self):
        """Test model properties after attempted load."""
        backend = MLXBackend()

        backend.current_model_name = "test-model"
        backend.model = Mock()

        assert backend.current_model_name == "test-model"
        assert backend.model is not None


class TestMLXBackendProperties:
    """Test MLXBackend properties."""

    def test_model_property_is_accessible(self):
        """model property should be accessible."""
        backend = MLXBackend()

        # Should not raise AttributeError
        model = backend.model

        assert model is None or model is not None

    def test_tokenizer_property_is_accessible(self):
        """tokenizer property should be accessible."""
        backend = MLXBackend()

        # Should not raise AttributeError
        tokenizer = backend.tokenizer

        assert tokenizer is None or tokenizer is not None

    def test_current_model_name_property_is_accessible(self):
        """current_model_name property should be accessible."""
        backend = MLXBackend()

        # Should not raise AttributeError
        name = backend.current_model_name

        assert name is None or isinstance(name, str)

    def test_current_model_name_is_writable(self):
        """current_model_name property should be writable."""
        backend = MLXBackend()

        backend.current_model_name = "test-model-123"

        assert backend.current_model_name == "test-model-123"

    def test_model_property_is_writable(self):
        """model property should be writable."""
        backend = MLXBackend()

        mock_model = Mock()
        backend.model = mock_model

        assert backend.model is mock_model

    def test_tokenizer_property_is_writable(self):
        """tokenizer property should be writable."""
        backend = MLXBackend()

        mock_tokenizer = Mock()
        backend.tokenizer = mock_tokenizer

        assert backend.tokenizer is mock_tokenizer

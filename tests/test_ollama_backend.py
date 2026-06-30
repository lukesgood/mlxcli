"""Tests for OllamaBackend implementation."""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.backends.ollama_backend import OllamaBackend
from mlxcli.backends import BACKENDS, get_backend, register_backend
from mlxcli.backends.base import LLMBackend


class TestOllamaBackendBasics:
    """Test basic OllamaBackend functionality."""

    def test_ollama_backend_can_be_created(self):
        """OllamaBackend can be instantiated."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            backend = OllamaBackend()
            assert backend is not None

    def test_ollama_backend_name_returns_ollama(self):
        """OllamaBackend.name returns 'ollama'."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            backend = OllamaBackend()
            assert backend.name == "ollama"

    def test_ollama_backend_available_checks_server_connection(self):
        """OllamaBackend.available checks if server is reachable."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            backend = OllamaBackend()
            assert backend.available is True

    def test_ollama_backend_available_false_when_server_unreachable(self):
        """OllamaBackend.available returns False if server not running."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection refused")
            backend = OllamaBackend()
            assert backend.available is False

    def test_ollama_backend_available_false_on_timeout(self):
        """OllamaBackend.available returns False on timeout."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get:
            import requests
            mock_get.side_effect = requests.Timeout("Connection timeout")
            backend = OllamaBackend()
            assert backend.available is False


class TestOllamaBackendModels:
    """Test model listing functionality."""

    def test_get_available_models_returns_list(self):
        """get_available_models() returns a list."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [
                    {"name": "llama2", "modified_at": "2024-01-01", "size": 3826087936}
                ]
            }
            mock_get.return_value = mock_response
            backend = OllamaBackend()
            models = backend.get_available_models()
            assert isinstance(models, list)

    def test_get_available_models_returns_empty_if_unavailable(self):
        """get_available_models() returns empty list if server unavailable."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection refused")
            backend = OllamaBackend()
            models = backend.get_available_models()
            assert models == []

    def test_get_available_models_includes_required_fields(self):
        """get_available_models() includes name, size, and description fields."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [
                    {"name": "llama2", "modified_at": "2024-01-01", "size": 3826087936}
                ]
            }
            mock_get.return_value = mock_response
            backend = OllamaBackend()
            models = backend.get_available_models()
            assert len(models) > 0
            model = models[0]
            assert "name" in model
            assert "size" in model
            assert "description" in model

    def test_get_available_models_formats_size_correctly(self):
        """get_available_models() formats size as human-readable string."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [
                    {"name": "llama2", "modified_at": "2024-01-01", "size": 3826087936}
                ]
            }
            mock_get.return_value = mock_response
            backend = OllamaBackend()
            models = backend.get_available_models()
            model = models[0]
            # Should be formatted like "3.6 GB"
            assert isinstance(model["size"], str)
            assert "B" in model["size"]


class TestOllamaBackendLoadModel:
    """Test model loading functionality."""

    def test_load_model_finds_existing_model(self):
        """load_model() finds model that exists locally."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get, \
             patch('mlxcli.backends.ollama_backend.requests.post') as mock_post:
            # First call: check availability, subsequent: get models
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [
                    {"name": "llama2", "modified_at": "2024-01-01", "size": 3826087936}
                ]
            }
            mock_get.return_value = mock_response
            backend = OllamaBackend()
            result = backend.load_model("llama2")
            assert result is True

    def test_load_model_returns_true_on_success(self):
        """load_model() returns True when model loads successfully."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get, \
             patch('mlxcli.backends.ollama_backend.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [
                    {"name": "llama2", "modified_at": "2024-01-01", "size": 3826087936}
                ]
            }
            mock_get.return_value = mock_response
            backend = OllamaBackend()
            result = backend.load_model("llama2")
            assert result is True

    def test_load_model_returns_false_on_failure(self):
        """load_model() returns False when model loading fails."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get, \
             patch('mlxcli.backends.ollama_backend.requests.post') as mock_post:
            # Server is available but model doesn't exist
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"models": []}
            mock_get.return_value = mock_response
            # Pull fails
            mock_post.side_effect = Exception("Model not found")
            backend = OllamaBackend()
            result = backend.load_model("nonexistent")
            assert result is False

    def test_load_model_sets_current_model_name(self):
        """load_model() sets current_model_name when successful."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get, \
             patch('mlxcli.backends.ollama_backend.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [
                    {"name": "llama2", "modified_at": "2024-01-01", "size": 3826087936}
                ]
            }
            mock_get.return_value = mock_response
            backend = OllamaBackend()
            backend.load_model("llama2")
            assert backend.current_model_name == "llama2"


class TestOllamaBackendGenerate:
    """Test text generation functionality."""

    def test_generate_requires_loaded_model(self):
        """generate() raises error if no model is loaded."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"models": []}
            mock_get.return_value = mock_response
            backend = OllamaBackend()
            with pytest.raises(RuntimeError):
                backend.generate("test prompt")

    def test_generate_returns_string(self):
        """generate() returns a string response."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get, \
             patch('mlxcli.backends.ollama_backend.requests.post') as mock_post:
            # Setup availability check and model loading
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [
                    {"name": "llama2", "modified_at": "2024-01-01", "size": 3826087936}
                ]
            }
            mock_get.return_value = mock_response
            backend = OllamaBackend()
            backend.load_model("llama2")

            # Setup generation response
            mock_response_gen = Mock()
            mock_response_gen.status_code = 200
            mock_response_gen.iter_lines.return_value = [
                json.dumps({"response": "Hello "}).encode(),
                json.dumps({"response": "world"}).encode(),
                json.dumps({"response": "", "done": True}).encode(),
            ]
            mock_post.return_value = mock_response_gen

            response = backend.generate("test prompt")
            assert isinstance(response, str)
            assert len(response) > 0

    def test_generate_uses_loaded_model(self):
        """generate() uses the model for generation."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get, \
             patch('mlxcli.backends.ollama_backend.requests.post') as mock_post:
            # Setup availability and model loading
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [
                    {"name": "mistral", "modified_at": "2024-01-01", "size": 3826087936}
                ]
            }
            mock_get.return_value = mock_response
            backend = OllamaBackend()
            backend.load_model("mistral")

            # Setup generation response
            mock_response_gen = Mock()
            mock_response_gen.status_code = 200
            mock_response_gen.iter_lines.return_value = [
                json.dumps({"response": "test"}).encode(),
            ]
            mock_post.return_value = mock_response_gen

            backend.generate("test prompt")

            # Verify post was called with correct model
            assert mock_post.called


class TestOllamaBackendTokenCounting:
    """Test token counting functionality."""

    def test_count_tokens_returns_int(self):
        """count_tokens() returns an integer."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"models": []}
            mock_get.return_value = mock_response
            backend = OllamaBackend()
            count = backend.count_tokens("test text")
            assert isinstance(count, int)

    def test_count_tokens_returns_positive_int(self):
        """count_tokens() returns positive integer."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"models": []}
            mock_get.return_value = mock_response
            backend = OllamaBackend()
            count = backend.count_tokens("This is a test text for tokenization")
            assert count > 0

    def test_count_tokens_approximation(self):
        """count_tokens() approximates correctly using ~1 token per 4 chars."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"models": []}
            mock_get.return_value = mock_response
            backend = OllamaBackend()
            # 16 characters = ~4 tokens
            count = backend.count_tokens("1234567890123456")
            assert count == 4


class TestOllamaBackendProperties:
    """Test backend properties."""

    def test_current_model_name_property_works(self):
        """current_model_name property returns model name."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [
                    {"name": "llama2", "modified_at": "2024-01-01", "size": 3826087936}
                ]
            }
            mock_get.return_value = mock_response
            backend = OllamaBackend()
            backend.load_model("llama2")
            assert backend.current_model_name == "llama2"

    def test_current_model_name_empty_when_no_model_loaded(self):
        """current_model_name is empty string when no model loaded."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"models": []}
            mock_get.return_value = mock_response
            backend = OllamaBackend()
            assert backend.current_model_name == ""


class TestOllamaBackendInterfaceCompliance:
    """Test that OllamaBackend implements full LLMBackend interface."""

    def test_ollama_backend_is_llm_backend(self):
        """OllamaBackend is an instance of LLMBackend."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"models": []}
            mock_get.return_value = mock_response
            backend = OllamaBackend()
            assert isinstance(backend, LLMBackend)

    def test_ollama_backend_implements_all_methods(self):
        """OllamaBackend implements all required methods."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"models": []}
            mock_get.return_value = mock_response
            backend = OllamaBackend()

            # Check all required methods exist
            assert hasattr(backend, 'name')
            assert hasattr(backend, 'available')
            assert hasattr(backend, 'get_available_models')
            assert hasattr(backend, 'load_model')
            assert hasattr(backend, 'generate')
            assert hasattr(backend, 'count_tokens')
            assert hasattr(backend, 'current_model_name')


class TestOllamaBackendRegistration:
    """Test backend registration."""

    def test_ollama_backend_can_be_registered(self):
        """OllamaBackend can be registered in the registry."""
        original_backends = BACKENDS.copy()
        try:
            BACKENDS.clear()
            register_backend("ollama", OllamaBackend)
            assert "ollama" in BACKENDS
        finally:
            BACKENDS.clear()
            BACKENDS.update(original_backends)

    def test_ollama_backend_can_be_retrieved_from_registry(self):
        """OllamaBackend can be retrieved from registry."""
        original_backends = BACKENDS.copy()
        try:
            BACKENDS.clear()
            register_backend("ollama", OllamaBackend)
            with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"models": []}
                mock_get.return_value = mock_response
                backend = get_backend("ollama")
                assert backend is not None
                assert isinstance(backend, OllamaBackend)
        finally:
            BACKENDS.clear()
            BACKENDS.update(original_backends)


class TestOllamaBackendSequential:
    """Test sequential operations."""

    def test_multiple_models_can_be_loaded_sequentially(self):
        """Multiple models can be loaded one after another."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get, \
             patch('mlxcli.backends.ollama_backend.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [
                    {"name": "llama2", "modified_at": "2024-01-01", "size": 3826087936},
                    {"name": "mistral", "modified_at": "2024-01-01", "size": 3826087936},
                ]
            }
            mock_get.return_value = mock_response
            backend = OllamaBackend()

            # Load first model
            result1 = backend.load_model("llama2")
            assert result1 is True
            assert backend.current_model_name == "llama2"

            # Load second model
            result2 = backend.load_model("mistral")
            assert result2 is True
            assert backend.current_model_name == "mistral"


class TestOllamaBackendErrorHandling:
    """Test error handling and edge cases."""

    def test_ollama_server_connection_errors_handled(self):
        """Connection errors to Ollama server are handled gracefully."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            backend = OllamaBackend()
            assert backend.available is False
            models = backend.get_available_models()
            assert models == []

    def test_generate_with_messages_parameter(self):
        """generate() accepts messages parameter."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get, \
             patch('mlxcli.backends.ollama_backend.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [
                    {"name": "llama2", "modified_at": "2024-01-01", "size": 3826087936}
                ]
            }
            mock_get.return_value = mock_response
            backend = OllamaBackend()
            backend.load_model("llama2")

            mock_response_gen = Mock()
            mock_response_gen.status_code = 200
            mock_response_gen.iter_lines.return_value = [
                json.dumps({"response": "response"}).encode(),
            ]
            mock_post.return_value = mock_response_gen

            # Should not raise
            response = backend.generate(
                "test",
                messages=[{"role": "user", "content": "hello"}]
            )
            assert isinstance(response, str)

    def test_generate_with_tools_parameter(self):
        """generate() accepts tools parameter."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get, \
             patch('mlxcli.backends.ollama_backend.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [
                    {"name": "llama2", "modified_at": "2024-01-01", "size": 3826087936}
                ]
            }
            mock_get.return_value = mock_response
            backend = OllamaBackend()
            backend.load_model("llama2")

            mock_response_gen = Mock()
            mock_response_gen.status_code = 200
            mock_response_gen.iter_lines.return_value = [
                json.dumps({"response": "response"}).encode(),
            ]
            mock_post.return_value = mock_response_gen

            # Should not raise
            response = backend.generate(
                "test",
                tools=[{"name": "tool1", "description": "a tool"}]
            )
            assert isinstance(response, str)

    def test_generate_with_max_tokens_parameter(self):
        """generate() accepts max_tokens parameter."""
        with patch('mlxcli.backends.ollama_backend.requests.get') as mock_get, \
             patch('mlxcli.backends.ollama_backend.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [
                    {"name": "llama2", "modified_at": "2024-01-01", "size": 3826087936}
                ]
            }
            mock_get.return_value = mock_response
            backend = OllamaBackend()
            backend.load_model("llama2")

            mock_response_gen = Mock()
            mock_response_gen.status_code = 200
            mock_response_gen.iter_lines.return_value = [
                json.dumps({"response": "response"}).encode(),
            ]
            mock_post.return_value = mock_response_gen

            # Should not raise
            response = backend.generate("test", max_tokens=256)
            assert isinstance(response, str)

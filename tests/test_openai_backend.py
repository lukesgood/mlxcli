"""Tests for OpenAIBackend implementation."""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.backends.openai_backend import OpenAIBackend
from mlxcli.backends import BACKENDS, get_backend, register_backend
from mlxcli.backends.base import LLMBackend


class TestOpenAIBackendBasics:
    """Test basic OpenAIBackend functionality."""

    def test_openai_backend_can_be_created(self):
        """OpenAIBackend can be instantiated."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            assert backend is not None

    def test_openai_backend_name_returns_openai(self):
        """OpenAIBackend.name returns 'openai'."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            assert backend.name == "openai"

    def test_openai_backend_available_true_with_api_key(self):
        """OpenAIBackend.available returns True if API key is set."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            assert backend.available is True

    def test_openai_backend_available_false_without_api_key(self):
        """OpenAIBackend.available returns False if API key is not set."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("mlxcli.backends.openai_backend.OpenAIBackend._load_api_key_from_config") as mock_load:
                mock_load.return_value = None
                backend = OpenAIBackend()
                assert backend.available is False

    def test_openai_backend_available_true_from_config(self):
        """OpenAIBackend.available returns True if API key is in config."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("mlxcli.backends.openai_backend.OpenAIBackend._load_api_key_from_config") as mock_load:
                mock_load.return_value = "config-key"
                backend = OpenAIBackend()
                assert backend.available is True


class TestOpenAIBackendModels:
    """Test model listing functionality."""

    def test_get_available_models_returns_list(self):
        """get_available_models() returns a list."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            models = backend.get_available_models()
            assert isinstance(models, list)

    def test_get_available_models_returns_non_empty_list(self):
        """get_available_models() returns non-empty list."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            models = backend.get_available_models()
            assert len(models) > 0

    def test_get_available_models_includes_gpt4(self):
        """get_available_models() includes gpt-4."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            models = backend.get_available_models()
            model_names = [m["name"] for m in models]
            assert "gpt-4" in model_names

    def test_get_available_models_includes_gpt35_turbo(self):
        """get_available_models() includes gpt-3.5-turbo."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            models = backend.get_available_models()
            model_names = [m["name"] for m in models]
            assert "gpt-3.5-turbo" in model_names

    def test_get_available_models_includes_gpt4_turbo(self):
        """get_available_models() includes gpt-4-turbo-preview."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            models = backend.get_available_models()
            model_names = [m["name"] for m in models]
            assert "gpt-4-turbo-preview" in model_names

    def test_get_available_models_includes_required_fields(self):
        """get_available_models() includes name, size, and description fields."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            models = backend.get_available_models()
            for model in models:
                assert "name" in model
                assert "size" in model
                assert "description" in model


class TestOpenAIBackendLoadModel:
    """Test model loading functionality."""

    def test_load_model_validates_model_name(self):
        """load_model() validates that model exists in available list."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            result = backend.load_model("invalid-model-name")
            assert result is False

    def test_load_model_returns_true_for_valid_model(self):
        """load_model() returns True for valid model name."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            result = backend.load_model("gpt-4")
            assert result is True

    def test_load_model_returns_true_for_gpt35_turbo(self):
        """load_model() returns True for gpt-3.5-turbo."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            result = backend.load_model("gpt-3.5-turbo")
            assert result is True

    def test_load_model_returns_true_for_gpt4_turbo(self):
        """load_model() returns True for gpt-4-turbo-preview."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            result = backend.load_model("gpt-4-turbo-preview")
            assert result is True

    def test_load_model_sets_current_model_name(self):
        """load_model() sets current_model_name property."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            backend.load_model("gpt-4")
            assert backend.current_model_name == "gpt-4"


class TestOpenAIBackendGenerate:
    """Test text generation functionality."""

    def test_generate_raises_error_if_no_model_loaded(self):
        """generate() raises RuntimeError if no model is loaded."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            with pytest.raises(RuntimeError):
                backend.generate("Hello, world!")

    def test_generate_raises_error_if_no_api_key(self):
        """generate() raises RuntimeError if API key is not available."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("mlxcli.backends.openai_backend.OpenAIBackend._load_api_key_from_config") as mock_load:
                mock_load.return_value = None
                backend = OpenAIBackend()
                backend._current_model_name = "gpt-4"
                with pytest.raises(RuntimeError):
                    backend.generate("Hello, world!")

    @patch("mlxcli.backends.openai_backend.requests.post")
    def test_generate_calls_openai_api(self, mock_post):
        """generate() makes HTTP request to OpenAI API."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello, there!"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            backend.load_model("gpt-4")
            response = backend.generate("Hello, world!")
            assert mock_post.called

    @patch("mlxcli.backends.openai_backend.requests.post")
    def test_generate_returns_response_text(self, mock_post):
        """generate() returns the response text from OpenAI API."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello, there!"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            backend.load_model("gpt-4")
            response = backend.generate("Hello, world!")
            assert response == "Hello, there!"

    @patch("mlxcli.backends.openai_backend.requests.post")
    def test_generate_accepts_max_tokens(self, mock_post):
        """generate() accepts max_tokens parameter."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello!"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            backend.load_model("gpt-4")
            response = backend.generate("Hello!", max_tokens=100)
            assert response == "Hello!"

    @patch("mlxcli.backends.openai_backend.requests.post")
    def test_generate_sends_correct_headers(self, mock_post):
        """generate() sends correct Authorization header."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hi"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            backend.load_model("gpt-4")
            backend.generate("Hello!")

            # Check headers
            call_args = mock_post.call_args
            headers = call_args[1]["headers"]
            assert "Authorization" in headers
            assert headers["Authorization"] == "Bearer test-key"

    @patch("mlxcli.backends.openai_backend.requests.post")
    def test_generate_sends_correct_endpoint(self, mock_post):
        """generate() sends request to correct OpenAI endpoint."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hi"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            backend.load_model("gpt-4")
            backend.generate("Hello!")

            # Check endpoint
            call_args = mock_post.call_args
            url = call_args[0][0]
            assert "https://api.openai.com/v1/chat/completions" in url

    @patch("mlxcli.backends.openai_backend.requests.post")
    def test_generate_with_messages(self, mock_post):
        """generate() accepts and uses messages parameter."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            backend.load_model("gpt-4")
            messages = [{"role": "user", "content": "Hi"}]
            response = backend.generate("Hello!", messages=messages)
            assert response == "Response"


class TestOpenAIBackendTokenCounting:
    """Test token counting functionality."""

    def test_count_tokens_returns_integer(self):
        """count_tokens() returns an integer."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            count = backend.count_tokens("Hello, world!")
            assert isinstance(count, int)

    def test_count_tokens_returns_positive_count(self):
        """count_tokens() returns positive count for non-empty text."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            count = backend.count_tokens("Hello, world!")
            assert count > 0

    def test_count_tokens_returns_zero_for_empty_text(self):
        """count_tokens() returns 0 for empty text."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            count = backend.count_tokens("")
            assert count == 0

    def test_count_tokens_approximates_count(self):
        """count_tokens() approximates token count using character ratio."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            # ~1 token per 4 characters
            text = "x" * 100  # 100 chars should be ~25 tokens
            count = backend.count_tokens(text)
            assert 20 <= count <= 30  # Reasonable approximation range


class TestOpenAIBackendCurrentModel:
    """Test current_model_name property."""

    def test_current_model_name_returns_string(self):
        """current_model_name returns a string."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            model_name = backend.current_model_name
            assert isinstance(model_name, str)

    def test_current_model_name_empty_initially(self):
        """current_model_name is empty string initially."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            assert backend.current_model_name == ""

    def test_current_model_name_after_load_model(self):
        """current_model_name returns loaded model name."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            backend.load_model("gpt-4")
            assert backend.current_model_name == "gpt-4"


class TestOpenAIBackendInterfaceCompliance:
    """Test that OpenAIBackend properly implements LLMBackend interface."""

    def test_openai_backend_is_subclass_of_llm_backend(self):
        """OpenAIBackend is a subclass of LLMBackend."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            assert isinstance(backend, LLMBackend)

    def test_openai_backend_implements_all_abstract_methods(self):
        """OpenAIBackend implements all abstract methods."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            # Check that all required methods exist and are callable
            assert hasattr(backend, "name")
            assert hasattr(backend, "available")
            assert callable(backend.get_available_models)
            assert callable(backend.load_model)
            assert callable(backend.generate)
            assert callable(backend.count_tokens)
            assert hasattr(backend, "current_model_name")


class TestOpenAIBackendRegistration:
    """Test backend registration in registry."""

    def test_openai_backend_can_be_registered(self):
        """OpenAIBackend can be registered in backend registry."""
        # Clear previous registration if any
        if "openai" in BACKENDS:
            del BACKENDS["openai"]

        register_backend("openai", OpenAIBackend)
        assert "openai" in BACKENDS

    def test_get_backend_returns_openai_backend(self):
        """get_backend('openai') returns OpenAIBackend instance."""
        # Ensure it's registered
        if "openai" in BACKENDS:
            del BACKENDS["openai"]
        register_backend("openai", OpenAIBackend)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = get_backend("openai")
            assert backend is not None
            assert isinstance(backend, OpenAIBackend)


class TestOpenAIBackendConfigIntegration:
    """Test API key configuration loading."""

    def test_api_key_loaded_from_environment(self):
        """OpenAIBackend loads API key from OPENAI_API_KEY environment variable."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            with patch("mlxcli.backends.openai_backend.OpenAIBackend._load_api_key_from_config"):
                backend = OpenAIBackend()
                assert backend.api_key == "env-key"

    def test_api_key_loaded_from_config_fallback(self):
        """OpenAIBackend loads API key from config if not in environment."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("mlxcli.backends.openai_backend.OpenAIBackend._load_api_key_from_config") as mock_load:
                mock_load.return_value = "config-key"
                backend = OpenAIBackend()
                assert backend.api_key == "config-key"


class TestOpenAIBackendSequentialRequests:
    """Test multiple sequential requests work correctly."""

    @patch("mlxcli.backends.openai_backend.requests.post")
    def test_sequential_generate_requests(self, mock_post):
        """Multiple sequential generate() requests work correctly."""
        mock_response1 = Mock()
        mock_response1.json.return_value = {
            "choices": [{"message": {"content": "Response 1"}}]
        }

        mock_response2 = Mock()
        mock_response2.json.return_value = {
            "choices": [{"message": {"content": "Response 2"}}]
        }

        mock_post.side_effect = [mock_response1, mock_response2]

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()
            backend.load_model("gpt-4")

            response1 = backend.generate("Hello!")
            response2 = backend.generate("Hi again!")

            assert response1 == "Response 1"
            assert response2 == "Response 2"

    def test_load_model_can_be_changed(self):
        """load_model() can be called multiple times to change models."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            backend = OpenAIBackend()

            backend.load_model("gpt-4")
            assert backend.current_model_name == "gpt-4"

            backend.load_model("gpt-3.5-turbo")
            assert backend.current_model_name == "gpt-3.5-turbo"

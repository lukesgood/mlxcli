"""Tests for LLMBackend abstract interface and registry."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.backends import (
    BACKENDS,
    get_backend,
    list_available_backends,
    list_backends,
    register_backend,
)
from mlxcli.backends.base import LLMBackend


class TestLLMBackendAbstract:
    """Test LLMBackend is properly abstract."""

    def test_llm_backend_cannot_be_instantiated(self):
        """LLMBackend should be abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError, match="abstract"):
            LLMBackend()

    def test_llm_backend_requires_name_property(self):
        """Subclass must implement name property."""

        class IncompleteBackend(LLMBackend):
            @property
            def available(self):
                return True

            def get_available_models(self):
                return []

            def load_model(self, model_name):
                return False

            def generate(self, prompt, messages=None, tools=None, max_tokens=512):
                return ""

            def count_tokens(self, text):
                return 0

            @property
            def current_model_name(self):
                return ""

        with pytest.raises(TypeError):
            IncompleteBackend()

    def test_llm_backend_requires_available_property(self):
        """Subclass must implement available property."""

        class IncompleteBackend(LLMBackend):
            @property
            def name(self):
                return "test"

            def get_available_models(self):
                return []

            def load_model(self, model_name):
                return False

            def generate(self, prompt, messages=None, tools=None, max_tokens=512):
                return ""

            def count_tokens(self, text):
                return 0

            @property
            def current_model_name(self):
                return ""

        with pytest.raises(TypeError):
            IncompleteBackend()

    def test_llm_backend_requires_get_available_models(self):
        """Subclass must implement get_available_models method."""

        class IncompleteBackend(LLMBackend):
            @property
            def name(self):
                return "test"

            @property
            def available(self):
                return True

            def load_model(self, model_name):
                return False

            def generate(self, prompt, messages=None, tools=None, max_tokens=512):
                return ""

            def count_tokens(self, text):
                return 0

            @property
            def current_model_name(self):
                return ""

        with pytest.raises(TypeError):
            IncompleteBackend()

    def test_llm_backend_requires_load_model(self):
        """Subclass must implement load_model method."""

        class IncompleteBackend(LLMBackend):
            @property
            def name(self):
                return "test"

            @property
            def available(self):
                return True

            def get_available_models(self):
                return []

            def generate(self, prompt, messages=None, tools=None, max_tokens=512):
                return ""

            def count_tokens(self, text):
                return 0

            @property
            def current_model_name(self):
                return ""

        with pytest.raises(TypeError):
            IncompleteBackend()

    def test_llm_backend_requires_generate(self):
        """Subclass must implement generate method."""

        class IncompleteBackend(LLMBackend):
            @property
            def name(self):
                return "test"

            @property
            def available(self):
                return True

            def get_available_models(self):
                return []

            def load_model(self, model_name):
                return False

            def count_tokens(self, text):
                return 0

            @property
            def current_model_name(self):
                return ""

        with pytest.raises(TypeError):
            IncompleteBackend()

    def test_llm_backend_requires_count_tokens(self):
        """Subclass must implement count_tokens method."""

        class IncompleteBackend(LLMBackend):
            @property
            def name(self):
                return "test"

            @property
            def available(self):
                return True

            def get_available_models(self):
                return []

            def load_model(self, model_name):
                return False

            def generate(self, prompt, messages=None, tools=None, max_tokens=512):
                return ""

            @property
            def current_model_name(self):
                return ""

        with pytest.raises(TypeError):
            IncompleteBackend()

    def test_llm_backend_requires_current_model_name_property(self):
        """Subclass must implement current_model_name property."""

        class IncompleteBackend(LLMBackend):
            @property
            def name(self):
                return "test"

            @property
            def available(self):
                return True

            def get_available_models(self):
                return []

            def load_model(self, model_name):
                return False

            def generate(self, prompt, messages=None, tools=None, max_tokens=512):
                return ""

            def count_tokens(self, text):
                return 0

        with pytest.raises(TypeError):
            IncompleteBackend()


class TestBackendRegistry:
    """Test backend registry functions."""

    def test_register_backend(self):
        """Should be able to register a backend."""
        # Create a minimal complete backend
        class TestBackend(LLMBackend):
            @property
            def name(self):
                return "test"

            @property
            def available(self):
                return True

            def get_available_models(self):
                return []

            def load_model(self, model_name):
                return False

            def generate(self, prompt, messages=None, tools=None, max_tokens=512):
                return "test response"

            def count_tokens(self, text):
                return 0

            @property
            def current_model_name(self):
                return ""

        register_backend("test", TestBackend)

        assert "test" in BACKENDS
        assert BACKENDS["test"] is TestBackend

    def test_get_backend_returns_instance(self):
        """get_backend should return an instance of backend."""
        class TestBackend(LLMBackend):
            @property
            def name(self):
                return "test"

            @property
            def available(self):
                return True

            def get_available_models(self):
                return []

            def load_model(self, model_name):
                return False

            def generate(self, prompt, messages=None, tools=None, max_tokens=512):
                return ""

            def count_tokens(self, text):
                return 0

            @property
            def current_model_name(self):
                return ""

        register_backend("test", TestBackend)

        backend = get_backend("test")

        assert backend is not None
        assert isinstance(backend, LLMBackend)
        assert isinstance(backend, TestBackend)

    def test_get_backend_returns_none_for_unknown(self):
        """get_backend should return None for unknown backend names."""
        backend = get_backend("unknown-backend-xyz-123")

        assert backend is None

    def test_list_backends(self):
        """list_backends should return list of registered backend names."""
        class TestBackend(LLMBackend):
            @property
            def name(self):
                return "test"

            @property
            def available(self):
                return True

            def get_available_models(self):
                return []

            def load_model(self, model_name):
                return False

            def generate(self, prompt, messages=None, tools=None, max_tokens=512):
                return ""

            def count_tokens(self, text):
                return 0

            @property
            def current_model_name(self):
                return ""

        register_backend("test1", TestBackend)
        register_backend("test2", TestBackend)

        backends = list_backends()

        assert isinstance(backends, list)
        assert "test1" in backends
        assert "test2" in backends

    def test_list_available_backends(self):
        """list_available_backends should only include available backends."""
        class AvailableBackend(LLMBackend):
            @property
            def name(self):
                return "available"

            @property
            def available(self):
                return True

            def get_available_models(self):
                return []

            def load_model(self, model_name):
                return False

            def generate(self, prompt, messages=None, tools=None, max_tokens=512):
                return ""

            def count_tokens(self, text):
                return 0

            @property
            def current_model_name(self):
                return ""

        class UnavailableBackend(LLMBackend):
            @property
            def name(self):
                return "unavailable"

            @property
            def available(self):
                return False

            def get_available_models(self):
                return []

            def load_model(self, model_name):
                return False

            def generate(self, prompt, messages=None, tools=None, max_tokens=512):
                return ""

            def count_tokens(self, text):
                return 0

            @property
            def current_model_name(self):
                return ""

        # Clear existing backends for this test
        original_backends = BACKENDS.copy()
        BACKENDS.clear()

        register_backend("available", AvailableBackend)
        register_backend("unavailable", UnavailableBackend)

        available = list_available_backends()

        assert isinstance(available, list)
        assert "available" in available
        assert "unavailable" not in available

        # Restore original backends
        BACKENDS.clear()
        BACKENDS.update(original_backends)

    def test_multiple_backends_can_be_registered(self):
        """Should be able to register multiple different backends."""
        class Backend1(LLMBackend):
            @property
            def name(self):
                return "backend1"

            @property
            def available(self):
                return True

            def get_available_models(self):
                return []

            def load_model(self, model_name):
                return False

            def generate(self, prompt, messages=None, tools=None, max_tokens=512):
                return ""

            def count_tokens(self, text):
                return 0

            @property
            def current_model_name(self):
                return ""

        class Backend2(LLMBackend):
            @property
            def name(self):
                return "backend2"

            @property
            def available(self):
                return True

            def get_available_models(self):
                return []

            def load_model(self, model_name):
                return False

            def generate(self, prompt, messages=None, tools=None, max_tokens=512):
                return ""

            def count_tokens(self, text):
                return 0

            @property
            def current_model_name(self):
                return ""

        register_backend("backend1", Backend1)
        register_backend("backend2", Backend2)

        b1 = get_backend("backend1")
        b2 = get_backend("backend2")

        assert b1 is not None
        assert b2 is not None
        assert type(b1) is Backend1
        assert type(b2) is Backend2
        assert b1.name == "backend1"
        assert b2.name == "backend2"

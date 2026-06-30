"""Ollama backend registration module.

This module registers the OllamaBackend in the backend registry.
It should be imported once during application startup to register the backend.
"""

from mlxcli.backends.ollama_backend import OllamaBackend
from mlxcli.backends import register_backend

# Register the Ollama backend in the registry
register_backend("ollama", OllamaBackend)

__all__ = ["OllamaBackend"]

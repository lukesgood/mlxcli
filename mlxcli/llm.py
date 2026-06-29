"""MLXBackend - Backward compatibility wrapper for new backend system.

This module provides backward compatibility for code that imports MLXBackend
from mlxcli.llm. The actual implementation is in mlxcli.backends.mlx_backend.

New code should use: from mlxcli.backends import get_backend
"""

from typing import Any, Optional

from mlxcli.backends.mlx_backend import MLXBackend as _MLXBackendImpl
from mlxcli.backends import register_backend

# Register the MLX backend in the registry
register_backend("mlx", _MLXBackendImpl)


class MLXBackend:
    """Backward compatibility wrapper for MLX backend.

    This class delegates all calls to the new backend system via registry.
    New code should use: from mlxcli.backends import get_backend

    This wrapper ensures that existing code importing from mlxcli.llm
    continues to work without modification.
    """

    def __init__(self) -> None:
        """Initialize MLXBackend wrapper.

        Gets the MLX backend from registry and delegates to it.
        """
        from mlxcli.backends import get_backend

        self._backend = get_backend("mlx")
        if not self._backend:
            raise RuntimeError("MLX backend not registered")

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to underlying backend.

        Args:
            name: Attribute name to access.

        Returns:
            Attribute value from underlying backend.
        """
        return getattr(self._backend, name)

    @property
    def model(self) -> Optional[Any]:
        """Get model from underlying backend."""
        return self._backend.model

    @model.setter
    def model(self, value: Optional[Any]) -> None:
        """Set model on underlying backend."""
        self._backend.model = value

    @property
    def tokenizer(self) -> Optional[Any]:
        """Get tokenizer from underlying backend."""
        return self._backend.tokenizer

    @tokenizer.setter
    def tokenizer(self, value: Optional[Any]) -> None:
        """Set tokenizer on underlying backend."""
        self._backend.tokenizer = value

    @property
    def current_model_name(self) -> Optional[str]:
        """Get current model name from underlying backend."""
        return self._backend.current_model_name or None

    @current_model_name.setter
    def current_model_name(self, value: Optional[str]) -> None:
        """Set current model name on underlying backend."""
        self._backend._current_model_name = value

    def get_available_models(self) -> list:
        """Delegate to underlying backend."""
        return self._backend.get_available_models()

    def load_model(self, model_name: str) -> bool:
        """Delegate to underlying backend."""
        return self._backend.load_model(model_name)

    def generate(
        self,
        prompt: str,
        messages: Optional[list] = None,
        tools: Optional[list] = None,
        max_tokens: int = 512,
    ) -> str:
        """Delegate to underlying backend."""
        return self._backend.generate(prompt, messages, tools, max_tokens)

    def count_tokens(self, text: str) -> int:
        """Delegate to underlying backend."""
        return self._backend.count_tokens(text)

    def get_model_info(self) -> dict:
        """Delegate to underlying backend."""
        return self._backend.get_model_info()

    def get_model_details(self, model_name: str) -> dict:
        """Delegate to underlying backend."""
        return self._backend.get_model_details(model_name)

    def _check_mlx(self) -> bool:
        """Delegate to underlying backend."""
        return self._backend._check_mlx()

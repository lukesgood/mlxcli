"""Backend registry and interface for LLM inference providers."""

from typing import Dict, Optional, Type

from mlxcli.backends.base import LLMBackend

# Backend registry mapping
BACKENDS: Dict[str, Type[LLMBackend]] = {}


def register_backend(name: str, backend_class: Type[LLMBackend]) -> None:
    """Register a backend.

    Args:
        name: Name of the backend (e.g., "mlx", "ollama", "openai").
        backend_class: The backend class to register.
    """
    BACKENDS[name] = backend_class


def get_backend(name: str) -> Optional[LLMBackend]:
    """Get backend instance by name.

    Args:
        name: Name of the backend to retrieve.

    Returns:
        An instance of the requested backend, or None if not found.
    """
    if name not in BACKENDS:
        return None
    return BACKENDS[name]()


def list_backends() -> list:
    """List all registered backend names.

    Returns:
        List of registered backend names.
    """
    return list(BACKENDS.keys())


def list_available_backends() -> list:
    """List backends that are actually available on system.

    Checks which backends are available by instantiating each one
    and checking its availability.

    Returns:
        List of available backend names.
    """
    available = []
    for name, backend_class in BACKENDS.items():
        try:
            if backend_class().available:
                available.append(name)
        except Exception:
            # Skip backends that fail to instantiate
            pass
    return available


__all__ = [
    "LLMBackend",
    "BACKENDS",
    "register_backend",
    "get_backend",
    "list_backends",
    "list_available_backends",
]

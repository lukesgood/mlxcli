"""Configuration management for MLX-CLI."""

from pathlib import Path
from typing import Any, Optional


class Config:
    """Simple configuration manager.

    Manages application configuration with default values.
    In Phase 2, this will be extended to support YAML file persistence.

    Default configuration values:
    - max_context_tokens: 4096 (max tokens for context window)
    - timeout_seconds: 30 (timeout for operations)
    - auto_save: True (automatically save sessions)

    Attributes:
        _config: Dictionary storing configuration key-value pairs.
        _defaults: Dictionary of default configuration values.
    """

    def __init__(self, config_dir: Optional[Path] = None) -> None:
        """Initialize Config with defaults.

        Args:
            config_dir: Optional path to config directory.
                       Currently unused (Phase 2 feature).
        """
        self._config: dict[str, Any] = {}
        self._defaults: dict[str, Any] = {
            "max_context_tokens": 4096,
            "timeout_seconds": 30,
            "auto_save": True,
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key to retrieve.
            default: Default value if key is not found and not in defaults.

        Returns:
            The configuration value, or default if not found.
        """
        if key in self._config:
            return self._config[key]
        if key in self._defaults:
            return self._defaults[key]
        return default

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key to set.
            value: Value to set.
        """
        self._config[key] = value

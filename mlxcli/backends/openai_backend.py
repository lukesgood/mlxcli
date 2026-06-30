"""OpenAI API backend implementation for cloud-based inference."""

import os
from typing import Optional

import requests

from mlxcli.backends.base import LLMBackend

# List of available OpenAI models
OPENAI_MODELS = [
    {
        "name": "gpt-4",
        "description": "Most capable GPT-4 model",
        "size": "Cloud API",
    },
    {
        "name": "gpt-4-turbo-preview",
        "description": "GPT-4 Turbo (faster, cheaper)",
        "size": "Cloud API",
    },
    {
        "name": "gpt-3.5-turbo",
        "description": "Fast, cost-effective GPT-3.5 Turbo",
        "size": "Cloud API",
    },
]


class OpenAIBackend(LLMBackend):
    """OpenAI API backend for cloud-based inference.

    Provides interface for:
    - Accessing OpenAI GPT models via API
    - Generating text using OpenAI models
    - Token counting
    - Managing API key configuration

    Attributes:
        api_key: OpenAI API key from environment or config.
        _current_model_name: Name of the currently selected model.
        _available: Whether the backend is available (API key is set).
    """

    def __init__(self) -> None:
        """Initialize OpenAIBackend.

        Loads API key from environment variable OPENAI_API_KEY or falls back
        to configuration file. Sets available=False if no API key found.
        """
        self.api_key = os.getenv("OPENAI_API_KEY") or self._load_api_key_from_config()
        self._current_model_name: Optional[str] = None
        self._available = self.api_key is not None

    @property
    def name(self) -> str:
        """Backend name.

        Returns:
            str: "openai"
        """
        return "openai"

    @property
    def available(self) -> bool:
        """Whether OpenAI API key is configured.

        Returns:
            bool: True if API key is available, False otherwise.
        """
        return self._available

    def _load_api_key_from_config(self) -> Optional[str]:
        """Load API key from config if not in environment.

        Attempts to load the OpenAI API key from the configuration file.

        Returns:
            str: API key from config, or None if not found.
        """
        try:
            from mlxcli.config import Config

            config = Config()
            return config.get("openai_api_key")
        except Exception:
            return None

    def get_available_models(self) -> list[dict]:
        """Get list of available OpenAI models.

        Returns information about available OpenAI models that can be used
        through this backend.

        Returns:
            List of model dicts with keys:
            - name: Model identifier (e.g., "gpt-4")
            - description: Human-readable description
            - size: Model size designation (Cloud API for all)
        """
        return OPENAI_MODELS

    def load_model(self, model_name: str) -> bool:
        """Validate and select a model.

        For OpenAI, this just validates that the model name is in the available
        list and sets it as the current model. No actual loading is needed since
        the API handles model management.

        Args:
            model_name: Name of the model to select.

        Returns:
            bool: True if model is valid and selected, False otherwise.
        """
        available_model_names = [m["name"] for m in self.get_available_models()]

        if model_name not in available_model_names:
            return False

        self._current_model_name = model_name
        return True

    def generate(
        self,
        prompt: str,
        messages: Optional[list] = None,
        tools: Optional[list] = None,
        max_tokens: int = 512,
    ) -> str:
        """Generate text using OpenAI API.

        Generates text based on the provided prompt and optional context
        (messages and tools) by making a request to the OpenAI API.

        Args:
            prompt: The main prompt/query text.
            messages: Optional list of message dicts (for conversation context).
                     Each dict should have "role" and "content" keys.
            tools: Optional list of tool definitions (currently unused).
            max_tokens: Maximum tokens to generate (default 512).

        Returns:
            str: Generated text response from OpenAI.

        Raises:
            RuntimeError: If no model is loaded or API key is not available.
        """
        if self._current_model_name is None:
            raise RuntimeError(
                "No model loaded. Call load_model() first to select a model."
            )

        if not self.api_key:
            raise RuntimeError("OpenAI API key is not configured.")

        # Build messages for API request
        request_messages = messages or []

        # Add the main prompt as a user message if not already in messages
        if not request_messages or request_messages[-1].get("role") != "user":
            request_messages.append({"role": "user", "content": prompt})
        elif not request_messages[-1].get("content"):
            # Update last user message content if empty
            request_messages[-1]["content"] = prompt

        # Prepare API request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self._current_model_name,
            "messages": request_messages,
            "max_tokens": max_tokens,
        }

        try:
            # Make API request
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )

            # Parse response
            response.raise_for_status()
            response_data = response.json()

            # Extract text from response
            if "choices" in response_data and len(response_data["choices"]) > 0:
                message = response_data["choices"][0].get("message", {})
                return message.get("content", "")

            return ""

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Approximates token count using character-based heuristic
        (~1 token per 4 characters). In a production system, this would
        use the actual OpenAI tokenizer.

        Args:
            text: Text to count tokens for.

        Returns:
            int: Approximate token count.
        """
        if not text:
            return 0

        # Approximation: ~1 token per 4 characters
        # This is a reasonable estimate for English text
        return max(1, len(text) // 4)

    @property
    def current_model_name(self) -> str:
        """Name of currently selected model.

        Returns:
            str: Name of selected model, or empty string if no model selected.
        """
        return self._current_model_name or ""

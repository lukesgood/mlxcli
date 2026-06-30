"""Ollama backend implementation for local inference server."""

import json
from typing import Optional

import requests

from mlxcli.backends.base import LLMBackend


class OllamaBackend(LLMBackend):
    """Ollama local inference server backend.

    Provides interface for:
    - Connecting to local Ollama server on localhost:11434
    - Listing available models from Ollama
    - Loading/pulling models from Ollama
    - Generating text using loaded models
    - Token counting with approximation

    Attributes:
        OLLAMA_URL: Base URL for Ollama server (localhost:11434)
        _available: Whether Ollama server is reachable
        _current_model_name: Name of currently loaded model
    """

    OLLAMA_URL = "http://localhost:11434"

    def __init__(self) -> None:
        """Initialize OllamaBackend.

        Attempts to connect to Ollama server and sets availability flag.
        """
        self._current_model_name: Optional[str] = None
        self._available = self._check_ollama_available()

    @property
    def name(self) -> str:
        """Backend name.

        Returns:
            str: "ollama"
        """
        return "ollama"

    @property
    def available(self) -> bool:
        """Whether Ollama server is available.

        Returns:
            bool: True if Ollama server is reachable, False otherwise.
        """
        return self._available

    def _check_ollama_available(self) -> bool:
        """Check if Ollama server is reachable.

        Makes a request to the Ollama server's /api/tags endpoint
        to verify it's running and accessible.

        Returns:
            bool: True if server responds with 200, False otherwise.
        """
        try:
            response = requests.get(f"{self.OLLAMA_URL}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def get_available_models(self) -> list[dict]:
        """Get list of available models from Ollama.

        Fetches the list of models from the Ollama server's /api/tags endpoint.
        If server is unavailable, returns an empty list.

        Returns:
            List of model dicts with keys:
            - name: Model identifier
            - size: Human-readable model size (e.g., "3.6 GB")
            - description: Description from model mapping or default
        """
        if not self.available:
            return []

        try:
            response = requests.get(f"{self.OLLAMA_URL}/api/tags", timeout=5)
            if response.status_code != 200:
                return []

            data = response.json()
            models = data.get("models", [])

            # Map Ollama models with descriptions
            ollama_models_map = {
                "llama2": {
                    "description": "Llama 2 - Meta's LLM",
                    "default_size": "~7GB",
                },
                "mistral": {
                    "description": "Mistral - Fast, quality model",
                    "default_size": "~7GB",
                },
                "neural-chat": {
                    "description": "Neural Chat - Optimized for chat",
                    "default_size": "~5GB",
                },
                "dolphin-mixtral": {
                    "description": "Dolphin Mixtral - Capable multimodal",
                    "default_size": "~26GB",
                },
                "phi": {
                    "description": "Phi - Efficient small model",
                    "default_size": "~2GB",
                },
            }

            result = []
            for model in models:
                model_name = model.get("name", "")
                size_bytes = model.get("size", 0)

                # Format size as human-readable
                if size_bytes > 0:
                    if size_bytes > 1e9:
                        size_str = f"{size_bytes / 1e9:.1f} GB"
                    elif size_bytes > 1e6:
                        size_str = f"{size_bytes / 1e6:.1f} MB"
                    else:
                        size_str = f"{size_bytes / 1e3:.1f} KB"
                else:
                    size_str = "Unknown"

                # Get description from map or use default
                base_name = model_name.split(":")[0]
                model_info = ollama_models_map.get(
                    base_name,
                    {"description": f"Ollama model: {base_name}"}
                )
                description = model_info.get("description", f"Ollama model: {base_name}")

                result.append({
                    "name": model_name,
                    "size": size_str,
                    "description": description,
                })

            return result
        except Exception:
            return []

    def load_model(self, model_name: str) -> bool:
        """Load a model from Ollama.

        Checks if model exists locally, and if not, pulls it from Ollama registry.
        Sets the model as the current model if successful.

        Args:
            model_name: Name/identifier of model to load.

        Returns:
            bool: True if model loaded successfully, False otherwise.
        """
        if not self.available:
            return False

        try:
            # Check if model exists in available models
            available = self.get_available_models()
            model_exists = any(m["name"] == model_name for m in available)

            if not model_exists:
                # Try to pull the model
                try:
                    response = requests.post(
                        f"{self.OLLAMA_URL}/api/pull",
                        json={"name": model_name},
                        timeout=300  # 5 minutes for pulling
                    )
                    if response.status_code != 200:
                        return False
                except Exception:
                    return False

            # Model is available, set it as current
            self._current_model_name = model_name
            return True
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        messages: Optional[list] = None,
        tools: Optional[list] = None,
        max_tokens: int = 512,
    ) -> str:
        """Generate text using Ollama.

        Generates text based on the provided prompt. If messages or tools are
        provided, they are included in the context.

        Args:
            prompt: The main prompt/query text.
            messages: Optional list of message dicts for conversation context.
            tools: Optional list of tool definitions (not actively used by Ollama).
            max_tokens: Maximum tokens to generate (default 512).

        Returns:
            str: Generated text response.

        Raises:
            RuntimeError: If no model is loaded.
        """
        if not self._current_model_name:
            raise RuntimeError(
                "No model loaded. Please load a model first using load_model()."
            )

        if not self.available:
            raise RuntimeError("Ollama server is not available.")

        try:
            # Build full prompt from components
            full_prompt = self._build_prompt(prompt, messages, tools)

            # Call Ollama generate endpoint with streaming
            response = requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={
                    "model": self._current_model_name,
                    "prompt": full_prompt,
                    "stream": True,
                },
                timeout=60
            )

            if response.status_code != 200:
                raise RuntimeError(f"Ollama API error: {response.status_code}")

            # Collect response from streaming
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        full_response += data.get("response", "")
                    except json.JSONDecodeError:
                        continue

            return full_response
        except requests.Timeout:
            raise RuntimeError("Generation request timed out.")
        except Exception as e:
            raise RuntimeError(f"Generation failed: {str(e)}")

    def count_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Ollama doesn't provide a token counting API, so this uses a simple
        approximation: ~1 token per 4 characters.

        Args:
            text: Text to count tokens for.

        Returns:
            int: Approximate token count.
        """
        if not text:
            return 0
        # Approximation: ~1 token per 4 characters
        return max(1, len(text) // 4)

    @property
    def current_model_name(self) -> str:
        """Name of currently loaded model.

        Returns:
            str: Model name if loaded, empty string otherwise.
        """
        return self._current_model_name or ""

    def _build_prompt(
        self,
        prompt: str,
        messages: Optional[list] = None,
        tools: Optional[list] = None,
    ) -> str:
        """Build full prompt from components.

        Combines the main prompt with context from messages and tools.

        Args:
            prompt: Main prompt text.
            messages: Optional conversation messages.
            tools: Optional tool definitions.

        Returns:
            str: Built prompt ready for model.
        """
        parts = []

        # Add tool context if provided
        if tools:
            parts.append("Available tools:")
            for tool in tools:
                name = tool.get("name", "unknown")
                desc = tool.get("description", "")
                parts.append(f"  - {name}: {desc}")
            parts.append("")

        # Add message context if provided
        if messages:
            parts.append("Conversation context:")
            for msg in messages:
                role = msg.get("role", "user").capitalize()
                content = msg.get("content", "")
                parts.append(f"{role}: {content}")
            parts.append("")

        # Add main prompt
        parts.append(prompt)

        return "\n".join(parts)

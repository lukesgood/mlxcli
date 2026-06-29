"""Abstract base class for LLM inference backends."""

from abc import ABC, abstractmethod
from typing import Optional


class LLMBackend(ABC):
    """Abstract base class for LLM inference backends.

    Defines the interface that all backends must implement.
    Backends provide inference capabilities for different LLM providers
    (MLX, Ollama, OpenAI, etc).

    Subclasses must implement all abstract methods and properties.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Backend name (mlx, ollama, openai, etc).

        Returns:
            str: Unique name identifying this backend.
        """
        pass

    @property
    @abstractmethod
    def available(self) -> bool:
        """Whether this backend is available on system.

        Checks if required dependencies are installed and
        the backend is ready to use.

        Returns:
            bool: True if backend is available, False otherwise.
        """
        pass

    @abstractmethod
    def get_available_models(self) -> list[dict]:
        """List available models with metadata.

        Returns information about models that can be loaded through
        this backend.

        Returns:
            List of model dicts with keys:
            - name: Model identifier (e.g., HuggingFace format)
            - size: Approximate model size (e.g., "~7GB")
            - description: Human-readable description
        """
        pass

    @abstractmethod
    def load_model(self, model_name: str) -> bool:
        """Load a model for inference.

        Loads a model identified by model_name and prepares it
        for inference.

        Args:
            model_name: Name/identifier of model to load.

        Returns:
            bool: True if model loaded successfully, False otherwise.
        """
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        messages: Optional[list] = None,
        tools: Optional[list] = None,
        max_tokens: int = 512,
    ) -> str:
        """Generate text response.

        Generates text based on the provided prompt and optional
        context (messages and tools).

        Args:
            prompt: The main prompt/query text.
            messages: Optional list of message dicts for conversation context.
                     Each dict should have "role" and "content" keys.
            tools: Optional list of tool definitions available to the model.
                   Each dict should have "name" and "description" keys.
            max_tokens: Maximum tokens to generate (default 512).

        Returns:
            str: Generated text response.

        Raises:
            RuntimeError: If model is not loaded.
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Counts the number of tokens that the given text would use
        when processed by this backend.

        Args:
            text: Text to count tokens for.

        Returns:
            int: Token count (exact if tokenizer available, approximate otherwise).
        """
        pass

    @property
    @abstractmethod
    def current_model_name(self) -> str:
        """Name of currently loaded model.

        Returns:
            str: Name of currently loaded model, or None/empty string if no model loaded.
        """
        pass

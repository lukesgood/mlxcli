"""MLXBackend - MLX model loading and inference backend."""

from typing import Optional, Any

# Check if MLX is available
try:
    import mlx.core as mx
    from mlx_lm import load, generate
    mlx_available = True
except ImportError:
    mlx_available = False


class MLXBackend:
    """MLX model loading and inference backend.

    Provides interface for:
    - Loading models from Hugging Face via MLX
    - Generating text using loaded models
    - Token counting
    - Managing model state

    Attributes:
        model: Loaded MLX model instance (or None if not loaded).
        tokenizer: Loaded MLX tokenizer (or None if not loaded).
        current_model_name: Name of the currently loaded model.
    """

    def __init__(self) -> None:
        """Initialize MLXBackend.

        Sets up the backend with no model loaded initially.
        """
        self.model: Optional[Any] = None
        self.tokenizer: Optional[Any] = None
        self.current_model_name: Optional[str] = None
        self._mlx_available = mlx_available

    def _check_mlx(self) -> bool:
        """Check if MLX is available and installed.

        Returns:
            bool: True if MLX is installed and available, False otherwise.
        """
        return self._mlx_available

    def get_available_models(self) -> list[dict]:
        """Get list of available models with metadata.

        Returns list of available models that can be loaded. If MLX is not
        installed, returns an empty list.

        Returns:
            List of model dicts with keys:
            - name: Model identifier (HuggingFace format)
            - size: Approximate model size
            - description: Human-readable description
        """
        if not self._check_mlx():
            return []

        # Placeholder models - will be fetched from HuggingFace in Phase 2
        models = [
            {
                "name": "meta-llama/Llama-2-7b-hf",
                "size": "~7GB",
                "description": "Llama 2 7B (good for most use cases)"
            },
            {
                "name": "mistral-community/Mistral-7B-v0.1",
                "size": "~7GB",
                "description": "Mistral 7B (fast, good quality)"
            },
            {
                "name": "meta-llama/Llama-2-13b-hf",
                "size": "~13GB",
                "description": "Llama 2 13B (larger, higher quality)"
            },
        ]

        return models

    def load_model(self, model_name: str) -> bool:
        """Load a model from the model hub.

        Attempts to load a model by name. Prints status messages during
        the loading process. If MLX is not installed, returns False.

        Args:
            model_name: Name of the model to load (HuggingFace format).

        Returns:
            bool: True if model loaded successfully, False otherwise.
        """
        if not self._check_mlx():
            print(f"MLX not installed. Cannot load model '{model_name}'")
            return False

        try:
            print(f"Loading model '{model_name}'...")
            self.model, self.tokenizer = load(model_name)
            self.current_model_name = model_name
            print(f"Successfully loaded model '{model_name}'")
            return True
        except Exception as e:
            print(f"Failed to load model '{model_name}': {str(e)}")
            self.model = None
            self.tokenizer = None
            return False

    def generate(
        self,
        prompt: str,
        messages: Optional[list] = None,
        tools: Optional[list[dict]] = None,
        max_tokens: int = 512
    ) -> str:
        """Generate text using the loaded model.

        Generates text based on the provided prompt and optional context
        (messages and tools). Builds the full prompt from components.

        Args:
            prompt: The main prompt/query text.
            messages: Optional list of message dicts (for conversation context).
                     Each dict should have "role" and "content" keys.
            tools: Optional list of tool definitions available to the model.
                   Each dict should have "name" and "description" keys.
            max_tokens: Maximum tokens to generate (default 512).

        Returns:
            str: Generated text response.

        Raises:
            RuntimeError: If no model is loaded.
        """
        if self.model is None:
            raise RuntimeError("No model loaded. Call load_model() first.")

        # Build full prompt from components
        full_prompt = self._build_prompt(prompt, messages, tools)

        # Generate using MLX
        response = generate(
            self.model,
            self.tokenizer,
            prompt=full_prompt,
            max_tokens=max_tokens,
            verbose=False
        )

        return response

    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Uses the loaded tokenizer if available. If tokenizer is not available,
        approximates token count using character-based heuristic (~1 token per 4 chars).

        Args:
            text: Text to count tokens for.

        Returns:
            int: Approximate or exact token count.
        """
        if not text:
            return 0

        if self.tokenizer is not None:
            try:
                # Use actual tokenizer
                tokens = self.tokenizer.encode(text)
                return len(tokens)
            except Exception:
                # Fall back to approximation
                pass

        # Approximation: ~1 token per 4 characters
        return max(1, len(text) // 4)

    def _build_prompt(
        self,
        prompt: str,
        messages: Optional[list] = None,
        tools: Optional[list[dict]] = None
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

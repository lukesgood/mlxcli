"""MLX backend implementation for local inference."""

from typing import Any, Optional

from mlxcli.backends.base import LLMBackend
from mlxcli.context_manager import ContextManager
from mlxcli.error_handler import ErrorHandler

# Check if MLX is available
try:
    import mlx.core as mx
    from mlx_lm import generate, load

    mlx_available = True
except ImportError:
    mlx_available = False


class MLXBackend(LLMBackend):
    """MLX backend for local model inference.

    Provides interface for:
    - Loading models from Hugging Face via MLX
    - Generating text using loaded models
    - Token counting
    - Managing model state

    Attributes:
        model: Loaded MLX model instance (or None if not loaded).
        tokenizer: Loaded MLX tokenizer (or None if not loaded).
        _current_model_name: Name of the currently loaded model.
    """

    def __init__(self) -> None:
        """Initialize MLXBackend.

        Sets up the backend with no model loaded initially.
        """
        self.model: Optional[Any] = None
        self.tokenizer: Optional[Any] = None
        self._current_model_name: Optional[str] = None
        self._mlx_available = mlx_available
        self.error_handler = ErrorHandler()
        self.context_manager = ContextManager()

    @property
    def name(self) -> str:
        """Backend name.

        Returns:
            str: "mlx"
        """
        return "mlx"

    @property
    def available(self) -> bool:
        """Whether MLX is available on system.

        Returns:
            bool: True if MLX is installed and available, False otherwise.
        """
        return self._check_mlx()

    def _check_mlx(self) -> bool:
        """Check if MLX is available and installed.

        Returns:
            bool: True if MLX is installed and available, False otherwise.
        """
        return self._mlx_available

    def get_available_models(self) -> list:
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

        # Latest models optimized for MLX on Apple Silicon (4bit quantized)
        models = [
            {
                "name": "mlx-community/Llama-3.2-1B-Instruct-4bit",
                "size": "~0.5GB",
                "description": "Llama 3.2 1B (fastest, mobile optimized, MLX native)",
            },
            {
                "name": "mlx-community/Llama-3.2-3B-Instruct-4bit",
                "size": "~2GB",
                "description": "Llama 3.2 3B (fast, good quality, MLX native)",
            },
            {
                "name": "mlx-community/Llama-3.2-11B-Vision-Instruct-4bit",
                "size": "~6GB",
                "description": "Llama 3.2 11B Vision (vision + text, MLX optimized)",
            },
            {
                "name": "mlx-community/Gemma-2-9B-4bit",
                "size": "~5GB",
                "description": "Gemma 2 9B (Google, efficient, MLX optimized)",
            },
            {
                "name": "mlx-community/Phi-4-4bit",
                "size": "~8GB",
                "description": "Phi-4 (Microsoft, powerful compact, MLX 4bit)",
            },
            {
                "name": "mlx-community/Qwen2.5-7B-4bit",
                "size": "~4GB",
                "description": "Qwen 2.5 7B (Chinese/English bilingual, MLX optimized)",
            },
            {
                "name": "mlx-community/Qwen2.5-14B-4bit",
                "size": "~8GB",
                "description": "Qwen 2.5 14B (Chinese/English, high quality, MLX 4bit)",
            },
            {
                "name": "mlx-community/Mistral-Large-2-4bit",
                "size": "~30GB",
                "description": "Mistral Large 2 (powerful reasoning, MLX 4bit)",
            },
            {
                "name": "mlx-community/DeepSeek-V2.5-4bit",
                "size": "~15GB",
                "description": "DeepSeek V2.5 (Chinese optimized, strong reasoning, MLX 4bit)",
            },
            {
                "name": "mlx-community/neural-chat-7b-v3-1-4bit",
                "size": "~4GB",
                "description": "Neural Chat 7B (conversational, lightweight, MLX native)",
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
            self._current_model_name = model_name
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
        tools: Optional[list] = None,
        max_tokens: int = 512,
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
            # Use error handler to provide actionable suggestion
            error_result = self.error_handler.handle_error(
                "model_not_found",
                {"model_name": self._current_model_name or "unknown"},
            )
            raise RuntimeError(f"{error_result['error']}. {error_result['suggestion']}")

        # Trim messages to fit context window
        if messages:
            messages = self.context_manager.trim_to_budget(
                messages, token_budget=3500  # Leave 500 for output
            )

        # Build full prompt from components
        full_prompt = self._build_prompt(prompt, messages, tools)

        # Generate using MLX
        response = generate(
            self.model,
            self.tokenizer,
            prompt=full_prompt,
            max_tokens=max_tokens,
            verbose=False,
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

    @property
    def current_model_name(self) -> str:
        """Name of currently loaded model.

        Returns:
            str: Model name if loaded, empty string otherwise.
        """
        return self._current_model_name or ""

    def get_model_info(self) -> dict:
        """Get current model information.

        Returns information about the currently loaded model, including
        its name, status (loaded/not loaded), context window, and size.

        Returns:
            dict: Model information with keys:
            - status: "ok" if model loaded, "no_model" if not loaded
            - name: Model name (if loaded)
            - context: Context window size in tokens (if loaded)
            - size: Approximate model size as string (if loaded)
        """
        if self.model is None or self._current_model_name is None:
            return {"status": "no_model"}

        # Get model details from available models list
        available_models = self.get_available_models()
        model_details = None

        for model in available_models:
            if model["name"] == self._current_model_name:
                model_details = model
                break

        # Default context window and size if model not found in list
        if model_details:
            size = model_details.get("size", "~7GB")
            # Extract numeric context based on model name
            context = self._estimate_context_window(self._current_model_name)
        else:
            size = "~7GB"
            context = self._estimate_context_window(self._current_model_name)

        return {
            "status": "ok",
            "name": self._current_model_name,
            "context": context,
            "size": size,
        }

    def get_model_details(self, model_name: str) -> dict:
        """Get details about a specific model.

        Looks up a model by name and returns its details including
        description and size. Returns "not_found" status if model
        doesn't exist in the available models list.

        Args:
            model_name: Name of the model to look up.

        Returns:
            dict: Model details with keys:
            - status: "ok" if found, "not_found" if not found
            - name: Model name (if found)
            - description: Human-readable description (if found)
            - size: Approximate model size (if found)
        """
        available_models = self.get_available_models()

        for model in available_models:
            if model["name"] == model_name:
                return {
                    "status": "ok",
                    "name": model["name"],
                    "description": model.get("description", ""),
                    "size": model.get("size", "Unknown"),
                }

        return {"status": "not_found"}

    def _estimate_context_window(self, model_name: str) -> int:
        """Estimate context window size from model name.

        Uses heuristics to estimate context window based on model name.
        Default is 4096 tokens (2k context).

        Args:
            model_name: Name of the model.

        Returns:
            int: Estimated context window in tokens.
        """
        # Common model context windows
        if "13b" in model_name.lower():
            return 4096
        elif "7b" in model_name.lower():
            return 4096
        elif "70b" in model_name.lower():
            return 4096
        elif "3b" in model_name.lower():
            return 2048
        else:
            return 4096

    def _build_prompt(
        self,
        prompt: str,
        messages: Optional[list] = None,
        tools: Optional[list[dict]] = None,
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

"""ContextManager - token-aware context management for conversations."""


class ContextManager:
    """Manages conversation context within a token budget.

    Trims conversation history to fit within a specified token budget,
    keeping the most recent messages and removing oldest messages first.

    Attributes:
        max_tokens: Maximum token budget for context.
    """

    def __init__(self, max_tokens: int = 4096):
        """Initialize ContextManager with max token budget.

        Args:
            max_tokens: Maximum token budget (default 4096).
        """
        self.max_tokens = max_tokens

    def get_context_size(self, text: str) -> int:
        """Estimate token count for text.

        Uses approximation: ~1 token per 4 characters for English text.
        Returns at least 1 token even for empty strings.

        Args:
            text: Text to estimate token count for.

        Returns:
            int: Estimated token count (minimum 1).
        """
        return max(1, len(text) // 4)

    def should_trim(self, messages: list) -> bool:
        """Check if messages exceed token budget.

        Calculates total tokens in all messages and compares to budget.

        Args:
            messages: List of message dicts with "content" key.

        Returns:
            bool: True if messages exceed budget, False otherwise.
        """
        total_tokens = 0
        for msg in messages:
            content = msg.get("content", "")
            total_tokens += self.get_context_size(content)

        return total_tokens > self.max_tokens

    def get_available_tokens(self, messages: list) -> int:
        """Get available tokens for new message.

        Calculates remaining tokens after accounting for current messages.

        Args:
            messages: List of message dicts with "content" key.

        Returns:
            int: Number of available tokens remaining in budget.
        """
        total_tokens = 0
        for msg in messages:
            content = msg.get("content", "")
            total_tokens += self.get_context_size(content)

        return self.max_tokens - total_tokens

    def trim_to_budget(self, messages: list, token_budget: int) -> list:
        """Trim messages to fit within token budget.

        Removes oldest messages first until total tokens fit within budget.
        Always keeps at least 1 message (system prompt context).

        Args:
            messages: List of message dicts with "content" key.
            token_budget: Maximum tokens allowed for all messages.

        Returns:
            list: Trimmed messages list, keeping most recent messages.
        """
        if not messages:
            return []

        # Calculate total tokens in all messages
        total_tokens = 0
        message_tokens = []

        for msg in messages:
            content = msg.get("content", "")
            tokens = self.get_context_size(content)
            message_tokens.append(tokens)
            total_tokens += tokens

        # If within budget, return all messages
        if total_tokens <= token_budget:
            return messages

        # Remove oldest messages one by one until within budget
        # Start from the beginning and remove messages until we fit
        trimmed_messages = messages[:]
        token_count = total_tokens

        while token_count > token_budget and len(trimmed_messages) > 1:
            removed_msg = trimmed_messages.pop(0)
            removed_tokens = self.get_context_size(removed_msg.get("content", ""))
            token_count -= removed_tokens

        return trimmed_messages

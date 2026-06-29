"""Tests for ContextManager - token-aware context management."""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.context_manager import ContextManager


class TestContextManagerCreation:
    """Test ContextManager creation and initialization."""

    def test_can_create_context_manager_instance(self):
        """Should be able to create ContextManager instance."""
        manager = ContextManager()

        assert manager is not None
        assert isinstance(manager, ContextManager)

    def test_context_manager_has_default_max_tokens(self):
        """ContextManager should have default max_tokens of 4096."""
        manager = ContextManager()

        assert manager.max_tokens == 4096

    def test_context_manager_accepts_custom_max_tokens(self):
        """Should be able to set custom max_tokens."""
        manager = ContextManager(max_tokens=2048)

        assert manager.max_tokens == 2048

    def test_context_manager_accepts_large_max_tokens(self):
        """Should accept large max_tokens values."""
        manager = ContextManager(max_tokens=8192)

        assert manager.max_tokens == 8192


class TestGetContextSize:
    """Test get_context_size token estimation."""

    def test_get_context_size_returns_integer(self):
        """get_context_size should return an integer."""
        manager = ContextManager()
        result = manager.get_context_size("hello")

        assert isinstance(result, int)

    def test_get_context_size_calculates_one_token_per_four_chars(self):
        """get_context_size should calculate ~1 token per 4 characters."""
        manager = ContextManager()

        # 4 chars = 1 token
        assert manager.get_context_size("abcd") == 1

        # 8 chars = 2 tokens
        assert manager.get_context_size("abcdefgh") == 2

        # 100 chars = 25 tokens
        assert manager.get_context_size("a" * 100) == 25

    def test_get_context_size_returns_at_least_one_for_empty_string(self):
        """get_context_size should return at least 1 for empty string."""
        manager = ContextManager()

        assert manager.get_context_size("") >= 1

    def test_get_context_size_handles_short_strings(self):
        """get_context_size should handle short strings correctly."""
        manager = ContextManager()

        # Less than 4 chars should return 1
        assert manager.get_context_size("a") == 1
        assert manager.get_context_size("ab") == 1
        assert manager.get_context_size("abc") == 1

    def test_get_context_size_is_consistent(self):
        """Token counting should be consistent across calls."""
        manager = ContextManager()
        text = "This is a test message with some content."

        count1 = manager.get_context_size(text)
        count2 = manager.get_context_size(text)

        assert count1 == count2


class TestShouldTrim:
    """Test should_trim method."""

    def test_should_trim_returns_boolean(self):
        """should_trim should return a boolean."""
        manager = ContextManager()
        result = manager.should_trim([])

        assert isinstance(result, bool)

    def test_should_trim_returns_false_if_within_budget(self):
        """should_trim should return False if messages within budget."""
        manager = ContextManager(max_tokens=1000)
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ]

        assert manager.should_trim(messages) is False

    def test_should_trim_returns_true_if_over_budget(self):
        """should_trim should return True if messages exceed budget."""
        manager = ContextManager(max_tokens=10)
        messages = [
            {"role": "user", "content": "a" * 100},
            {"role": "assistant", "content": "b" * 100},
        ]

        assert manager.should_trim(messages) is True

    def test_should_trim_with_empty_messages(self):
        """should_trim should handle empty messages list."""
        manager = ContextManager()

        assert manager.should_trim([]) is False


class TestGetAvailableTokens:
    """Test get_available_tokens method."""

    def test_get_available_tokens_returns_integer(self):
        """get_available_tokens should return an integer."""
        manager = ContextManager()
        result = manager.get_available_tokens([])

        assert isinstance(result, int)

    def test_get_available_tokens_calculates_remaining_tokens(self):
        """get_available_tokens should return remaining tokens."""
        manager = ContextManager(max_tokens=1000)
        messages = [{"role": "user", "content": "hello"}]

        available = manager.get_available_tokens(messages)

        # Available should be less than max_tokens
        assert available < 1000
        assert available > 0

    def test_get_available_tokens_with_empty_messages(self):
        """get_available_tokens should return full budget for empty messages."""
        manager = ContextManager(max_tokens=1000)

        available = manager.get_available_tokens([])

        # Should be close to max_tokens
        assert available > 900

    def test_get_available_tokens_returns_zero_if_full(self):
        """get_available_tokens should return 0 or low value if budget full."""
        manager = ContextManager(max_tokens=10)
        messages = [
            {"role": "user", "content": "a" * 100},
            {"role": "assistant", "content": "b" * 100},
        ]

        available = manager.get_available_tokens(messages)

        # Should be 0 or very small
        assert available <= 0


class TestTrimToBudget:
    """Test trim_to_budget message trimming."""

    def test_trim_to_budget_returns_list(self):
        """trim_to_budget should return a list."""
        manager = ContextManager()
        messages = [{"role": "user", "content": "hello"}]

        result = manager.trim_to_budget(messages, token_budget=1000)

        assert isinstance(result, list)

    def test_trim_to_budget_returns_all_messages_if_within_budget(self):
        """trim_to_budget should return all messages if within budget."""
        manager = ContextManager()
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "world"},
            {"role": "user", "content": "how are you"},
        ]

        result = manager.trim_to_budget(messages, token_budget=10000)

        assert len(result) == 3

    def test_trim_to_budget_removes_oldest_messages(self):
        """trim_to_budget should remove oldest messages first."""
        manager = ContextManager()
        messages = [
            {"role": "user", "content": "a" * 100, "id": 1},
            {"role": "assistant", "content": "b" * 100, "id": 2},
            {"role": "user", "content": "c" * 100, "id": 3},
        ]

        result = manager.trim_to_budget(messages, token_budget=50)

        # Should have fewer messages
        assert len(result) < len(messages)

        # Most recent messages should be kept
        # The last message (id=3) should definitely be in result
        assert any(msg.get("id") == 3 for msg in result)

    def test_trim_to_budget_keeps_most_recent_messages(self):
        """trim_to_budget should prioritize keeping recent messages."""
        manager = ContextManager()
        messages = [
            {"role": "user", "content": "a", "order": 1},
            {"role": "assistant", "content": "b", "order": 2},
            {"role": "user", "content": "c", "order": 3},
            {"role": "assistant", "content": "d", "order": 4},
        ]

        result = manager.trim_to_budget(messages, token_budget=100)

        # If all fit in budget, should keep all
        if len(result) == len(messages):
            assert result == messages
        else:
            # If trimmed, most recent should be kept
            assert result[-1]["order"] == 4

    def test_trim_to_budget_always_keeps_at_least_one_message(self):
        """trim_to_budget should always keep at least 1 message."""
        manager = ContextManager()
        messages = [
            {"role": "user", "content": "a" * 100},
            {"role": "assistant", "content": "b" * 100},
            {"role": "user", "content": "c" * 100},
        ]

        # Try with very small budget
        result = manager.trim_to_budget(messages, token_budget=5)

        assert len(result) >= 1

    def test_trim_to_budget_with_many_long_messages(self):
        """trim_to_budget should handle many long messages correctly."""
        manager = ContextManager()
        messages = [
            {"role": "user", "content": "message " + str(i) + " " + "a" * 200} for i in range(10)
        ]

        result = manager.trim_to_budget(messages, token_budget=200)

        # Should have trimmed some messages
        assert len(result) < len(messages)

        # Should have at least one message
        assert len(result) >= 1

    def test_trim_to_budget_with_single_message(self):
        """trim_to_budget should handle single message within budget."""
        manager = ContextManager()
        messages = [{"role": "user", "content": "hello world"}]

        result = manager.trim_to_budget(messages, token_budget=1000)

        assert len(result) == 1
        assert result[0]["content"] == "hello world"

    def test_trim_to_budget_does_not_modify_original(self):
        """trim_to_budget should not modify the original messages list."""
        manager = ContextManager()
        messages = [
            {"role": "user", "content": "a" * 100},
            {"role": "assistant", "content": "b" * 100},
        ]
        original_length = len(messages)

        manager.trim_to_budget(messages, token_budget=50)

        # Original should be unchanged
        assert len(messages) == original_length


class TestMultipleTrimOperations:
    """Test multiple trim operations."""

    def test_multiple_trim_operations_work_correctly(self):
        """Multiple trim operations should work consistently."""
        manager = ContextManager(max_tokens=1000)
        messages = [{"role": "user", "content": "a" * 100, "id": i} for i in range(5)]

        result1 = manager.trim_to_budget(messages, token_budget=200)
        result2 = manager.trim_to_budget(messages, token_budget=200)

        # Results should be consistent
        assert len(result1) == len(result2)

    def test_token_counting_is_consistent(self):
        """Token counting should be consistent across calls."""
        manager = ContextManager()
        text = "This is a test message."

        count1 = manager.get_context_size(text)
        count2 = manager.get_context_size(text)
        count3 = manager.get_context_size(text)

        assert count1 == count2 == count3

    def test_large_conversation_histories_trim_properly(self):
        """Large conversation histories should trim properly."""
        manager = ContextManager()
        messages = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": "m" * 50} for i in range(100)
        ]

        result = manager.trim_to_budget(messages, token_budget=500)

        # Should have trimmed significantly
        assert len(result) < len(messages)

        # Should have at least one message
        assert len(result) >= 1

    def test_single_message_within_budget_preserved(self):
        """Single message within budget should be preserved."""
        manager = ContextManager()
        messages = [{"role": "user", "content": "hello world"}]

        result = manager.trim_to_budget(messages, token_budget=1000)

        assert len(result) == 1
        assert result[0] == messages[0]

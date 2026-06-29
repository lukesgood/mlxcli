"""Tests for ErrorHandler - centralized error handling with recovery strategies."""

import json
import logging
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.error_handler import ErrorHandler
from mlxcli.session import Session


class TestErrorHandlerHandleError:
    """Test handle_error method for various error types."""

    def test_handle_error_model_not_found_returns_dict(self):
        """handle_error should return dict with actionable suggestion for model_not_found."""
        handler = ErrorHandler()
        context = {"model_name": "meta-llama/Llama-2-7b-hf"}

        result = handler.handle_error("model_not_found", context)

        assert isinstance(result, dict)
        assert "status" in result
        assert "error" in result
        assert "suggestion" in result
        assert "next_step" in result

    def test_handle_error_model_not_found_suggests_download(self):
        """model_not_found error should suggest downloading the model."""
        handler = ErrorHandler()
        context = {"model_name": "meta-llama/Llama-2-7b-hf"}

        result = handler.handle_error("model_not_found", context)

        assert result["status"] == "handled"
        # Suggestion should mention download
        assert "download" in result["suggestion"].lower()
        # Should include actionable steps or commands
        assert len(result["suggestion"]) > 0
        # next_step should tell user what to do
        assert len(result["next_step"]) > 0

    def test_handle_error_oom_returns_dict(self):
        """handle_error should return dict for out of memory error."""
        handler = ErrorHandler()
        context = {"available_memory": "2GB", "required_memory": "8GB"}

        result = handler.handle_error("oom", context)

        assert isinstance(result, dict)
        assert result["status"] == "handled"
        assert "suggestion" in result
        # Should suggest reduction of resources or smaller model
        assert "reduce" in result["suggestion"].lower() or "simplif" in result["suggestion"].lower()

    def test_handle_error_session_corrupted_returns_recovery_strategy(self):
        """handle_error should return recovery strategy for corrupted session."""
        handler = ErrorHandler()
        context = {
            "session_id": "abc12345",
            "error_detail": "JSON parse error",
        }

        result = handler.handle_error("session_corrupted", context)

        assert result["status"] == "handled"
        # Should explain the issue
        assert "session" in result["error"].lower()
        # Should suggest recovery
        assert "recover" in result["suggestion"].lower() or ("new" in result["suggestion"].lower())

    def test_handle_error_timeout_suggests_simplification(self):
        """timeout error should suggest simplifying the prompt."""
        handler = ErrorHandler()
        context = {"timeout_seconds": 30, "operation": "model_inference"}

        result = handler.handle_error("timeout", context)

        assert result["status"] == "handled"
        # Should mention timeout
        assert "timeout" in result["error"].lower() or "timed out" in result["error"].lower()
        # Should suggest simplification
        assert "simplif" in result["suggestion"].lower() or "reduce" in result["suggestion"].lower()

    def test_handle_error_permission_denied_returns_dict(self):
        """handle_error should return dict for permission denied error."""
        handler = ErrorHandler()
        context = {"path": "/root/.mlxcli/sessions", "operation": "write"}

        result = handler.handle_error("permission_denied", context)

        assert result["status"] == "handled"
        assert "permission" in result["error"].lower()
        # Should suggest fixing permissions or checking path
        assert len(result["suggestion"]) > 0

    def test_handle_error_disk_full_suggests_cleanup(self):
        """disk_full error should suggest cleanup operations."""
        handler = ErrorHandler()
        context = {"available_space": "100MB", "required_space": "2GB"}

        result = handler.handle_error("disk_full", context)

        assert result["status"] == "handled"
        # Should mention disk space
        assert "disk" in result["error"].lower() or "space" in result["error"].lower()
        # Should suggest cleanup or deletion of files
        assert (
            "clean" in result["suggestion"].lower()
            or "free" in result["suggestion"].lower()
            or "delete" in result["suggestion"].lower()
        )

    def test_handle_error_unknown_type_handled_gracefully(self):
        """Unknown error types should be handled gracefully."""
        handler = ErrorHandler()
        context = {"some": "context"}

        result = handler.handle_error("unknown_error_type", context)

        assert isinstance(result, dict)
        assert result["status"] == "handled"
        # Should still provide helpful information
        assert "error" in result
        assert "suggestion" in result

    def test_handle_error_preserves_context_in_result(self):
        """Context dict should be preserved in error handling result."""
        handler = ErrorHandler()
        context = {"model_name": "test-model", "extra_field": "extra_value"}

        result = handler.handle_error("model_not_found", context)

        # Context should be preserved (usually in additional fields)
        assert "model_name" in result or "context" in result

    def test_handle_error_multiple_types_in_sequence(self):
        """Multiple error types can be handled in sequence."""
        handler = ErrorHandler()

        result1 = handler.handle_error("model_not_found", {"model_name": "m1"})
        result2 = handler.handle_error("oom", {"available_memory": "1GB"})
        result3 = handler.handle_error("timeout", {"timeout_seconds": 30})

        assert result1["status"] == "handled"
        assert result2["status"] == "handled"
        assert result3["status"] == "handled"

    def test_handle_error_messages_follow_consistent_format(self):
        """All error messages should follow consistent format."""
        handler = ErrorHandler()
        error_types = [
            ("model_not_found", {"model_name": "test"}),
            ("oom", {"available_memory": "1GB"}),
            ("session_corrupted", {"session_id": "test123"}),
            ("timeout", {"timeout_seconds": 30}),
            ("permission_denied", {"path": "/test"}),
            ("disk_full", {"available_space": "100MB"}),
        ]

        for error_type, context in error_types:
            result = handler.handle_error(error_type, context)

            # All should have these fields
            assert "status" in result
            assert "error" in result
            assert "suggestion" in result
            assert "next_step" in result
            # All values should be strings (except status)
            assert isinstance(result["error"], str)
            assert isinstance(result["suggestion"], str)
            assert isinstance(result["next_step"], str)
            # Should be actionable (have some length)
            assert len(result["suggestion"]) > 0
            assert len(result["next_step"]) > 0

    def test_handle_error_suggestions_are_actionable(self):
        """Recovery suggestions should include commands or clear steps."""
        handler = ErrorHandler()

        # Test each error type has actionable suggestions
        errors = [
            ("model_not_found", {"model_name": "test-model"}),
            ("oom", {"available_memory": "1GB"}),
            ("timeout", {"timeout_seconds": 30}),
            ("disk_full", {"available_space": "100MB"}),
        ]

        for error_type, context in errors:
            result = handler.handle_error(error_type, context)
            suggestion = result["suggestion"].lower()

            # Should contain action words or specific steps
            action_words = [
                "download",
                "simplif",
                "reduce",
                "clean",
                "check",
                "verify",
                "try",
                "use",
                "set",
                "remove",
                "delete",
            ]
            has_action = any(word in suggestion for word in action_words)
            assert has_action, f"Suggestion for {error_type} not actionable: {suggestion}"


class TestErrorHandlerSuggestRecovery:
    """Test suggest_recovery method for exception types."""

    def test_suggest_recovery_memory_error(self):
        """suggest_recovery should return recovery string for MemoryError."""
        handler = ErrorHandler()
        error = MemoryError("Out of memory")

        suggestion = handler.suggest_recovery(error)

        assert isinstance(suggestion, str)
        assert len(suggestion) > 0
        # Should suggest memory-related recovery
        assert (
            "simplif" in suggestion.lower()
            or "reduce" in suggestion.lower()
            or "memory" in suggestion.lower()
        )

    def test_suggest_recovery_timeout_error(self):
        """suggest_recovery should return recovery string for TimeoutError."""
        handler = ErrorHandler()
        error = TimeoutError("Operation timed out")

        suggestion = handler.suggest_recovery(error)

        assert isinstance(suggestion, str)
        assert len(suggestion) > 0
        # Should suggest timeout-related recovery
        assert (
            "timeout" in suggestion.lower()
            or "simplif" in suggestion.lower()
            or "retry" in suggestion.lower()
        )

    def test_suggest_recovery_permission_error(self):
        """suggest_recovery should return recovery string for PermissionError."""
        handler = ErrorHandler()
        error = PermissionError("Permission denied")

        suggestion = handler.suggest_recovery(error)

        assert isinstance(suggestion, str)
        assert len(suggestion) > 0
        # Should suggest permission-related recovery
        assert (
            "permission" in suggestion.lower()
            or "chmod" in suggestion.lower()
            or "check" in suggestion.lower()
        )

    def test_suggest_recovery_file_not_found_error(self):
        """suggest_recovery should return recovery string for FileNotFoundError."""
        handler = ErrorHandler()
        error = FileNotFoundError("File not found")

        suggestion = handler.suggest_recovery(error)

        assert isinstance(suggestion, str)
        assert len(suggestion) > 0

    def test_suggest_recovery_json_decode_error(self):
        """suggest_recovery should return recovery string for JSON errors."""
        handler = ErrorHandler()
        error = json.JSONDecodeError("Invalid JSON", "", 0)

        suggestion = handler.suggest_recovery(error)

        assert isinstance(suggestion, str)
        assert len(suggestion) > 0

    def test_suggest_recovery_generic_exception(self):
        """suggest_recovery should handle generic exceptions."""
        handler = ErrorHandler()
        error = Exception("Something went wrong")

        suggestion = handler.suggest_recovery(error)

        assert isinstance(suggestion, str)
        assert len(suggestion) > 0


class TestErrorHandlerLogError:
    """Test log_error method for error logging."""

    def test_log_error_captures_exception_and_context(self):
        """log_error should log exception with context."""
        handler = ErrorHandler()
        context = {"operation": "model_load", "model_name": "test-model"}
        error = RuntimeError("Failed to load model")

        # Should not raise an exception
        handler.log_error(error, context)

    def test_log_error_with_empty_context(self):
        """log_error should work with empty context dict."""
        handler = ErrorHandler()
        error = ValueError("Invalid value")

        # Should not raise an exception
        handler.log_error(error, {})

    def test_log_error_with_various_error_types(self):
        """log_error should handle various exception types."""
        handler = ErrorHandler()
        context = {"test": "context"}

        errors = [
            RuntimeError("Runtime error"),
            ValueError("Value error"),
            TypeError("Type error"),
            MemoryError("Memory error"),
            TimeoutError("Timeout error"),
        ]

        for error in errors:
            # Should not raise an exception
            handler.log_error(error, context)


class TestErrorHandlerSessionRecovery:
    """Test integration with Session.recover_corrupted."""

    @pytest.fixture
    def temp_sessions_dir(self):
        """Create a temporary sessions directory."""
        tmpdir = Path(tempfile.mkdtemp())
        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_recover_corrupted_creates_new_session(self, temp_sessions_dir):
        """recover_corrupted should create a new session for corrupted session_id."""
        session_id = "corrupted123"

        recovered = Session.recover_corrupted(session_id, temp_sessions_dir)

        assert isinstance(recovered, Session)
        assert recovered.id == session_id

    def test_recover_corrupted_session_is_usable(self, temp_sessions_dir):
        """Recovered session should be usable for adding messages."""
        session_id = "corrupted456"

        recovered = Session.recover_corrupted(session_id, temp_sessions_dir)

        # Should be able to add message
        recovered.add_message(role="user", content="test")
        assert len(recovered.messages) == 1

    def test_recover_corrupted_session_can_be_saved(self, temp_sessions_dir):
        """Recovered session should be saveable."""
        session_id = "corrupted789"

        recovered = Session.recover_corrupted(session_id, temp_sessions_dir)

        # Should be able to save
        path = recovered.save(temp_sessions_dir)
        assert path.exists()

    def test_recover_corrupted_preserves_session_id(self, temp_sessions_dir):
        """recover_corrupted should preserve the original session_id."""
        original_id = "test_session_abc"

        recovered = Session.recover_corrupted(original_id, temp_sessions_dir)

        assert recovered.id == original_id

    def test_handle_error_session_corrupted_suggests_recover_corrupted(self):
        """handle_error for session_corrupted should mention recovery method."""
        handler = ErrorHandler()
        context = {"session_id": "test123"}

        result = handler.handle_error("session_corrupted", context)

        # Should suggest using recovery method or creating new session
        suggestion_lower = result["suggestion"].lower()
        assert (
            "recover" in suggestion_lower
            or "new" in suggestion_lower
            or "create" in suggestion_lower
        )


class TestErrorHandlerIntegration:
    """Integration tests for error handling workflow."""

    def test_full_error_handling_workflow(self):
        """Test complete error handling workflow."""
        handler = ErrorHandler()

        # Handle an error
        result = handler.handle_error("model_not_found", {"model_name": "test-model"})

        assert result["status"] == "handled"
        assert "error" in result
        assert "suggestion" in result
        assert "next_step" in result

    def test_error_handler_with_exception_and_context(self):
        """Test error handler with both exception and context."""
        handler = ErrorHandler()

        error = RuntimeError("Model loading failed")
        context = {"model_name": "test", "available_memory": "2GB"}

        # Log the error
        handler.log_error(error, context)

        # Get recovery suggestion
        suggestion = handler.suggest_recovery(error)

        assert isinstance(suggestion, str)
        assert len(suggestion) > 0

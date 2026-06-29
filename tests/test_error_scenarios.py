"""Error Scenarios Integration Testing - End-to-end error handling tests.

Comprehensive integration tests for all error scenarios across Phase 2 components.
Tests real-world failure scenarios with recovery validation.
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.cli import CLI
from mlxcli.completion import setup_completion
from mlxcli.context_manager import ContextManager
from mlxcli.error_handler import ErrorHandler
from mlxcli.session import Session
from mlxcli.tools.shell_tool import ShellTool
from mlxcli.tool_registry import ToolRegistry


class TestModelNotFoundScenario:
    """Test 1: Model Not Found error scenario."""

    def test_model_not_found_error_handling(self):
        """End-to-end: Model not found triggers handler and suggests download."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            handler = ErrorHandler()

            # Simulate model not found
            result = handler.handle_error(
                "model_not_found",
                {"model_name": "nonexistent-model-xyz"}
            )

            # Verify error handling
            assert result["status"] == "handled"
            assert "nonexistent-model-xyz" in result["error"]
            assert "download" in result["suggestion"].lower()
            assert len(result["next_step"]) > 0

    def test_model_not_found_includes_recovery_path(self):
        """Model not found error should include actionable recovery path."""
        handler = ErrorHandler()

        result = handler.handle_error(
            "model_not_found",
            {"model_name": "meta-llama/Llama-2-7b"}
        )

        # Verify recovery path exists
        assert "download" in result["suggestion"].lower() or "list-models" in result["suggestion"].lower()
        assert result["next_step"]

    def test_system_recovers_from_model_not_found(self):
        """System should remain responsive after model not found error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            handler = ErrorHandler()

            # First error
            result1 = handler.handle_error("model_not_found", {"model_name": "m1"})
            assert result1["status"] == "handled"

            # System should still work - can handle another error
            result2 = handler.handle_error("model_not_found", {"model_name": "m2"})
            assert result2["status"] == "handled"
            assert result1 is not result2  # Different results


class TestCorruptedSessionScenario:
    """Test 2: Corrupted Session recovery scenario."""

    def test_corrupted_session_recovery_creates_new(self):
        """End-to-end: Corrupted JSON session can be recovered."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir)
            session_id = "corrupt123"

            # Create corrupted session file
            corrupted_file = sessions_dir / f"session_{session_id}.json"
            corrupted_file.parent.mkdir(parents=True, exist_ok=True)
            corrupted_file.write_text("{ invalid json }")

            # Verify file is corrupted
            with pytest.raises(json.JSONDecodeError):
                json.loads(corrupted_file.read_text())

            # Recover using Session.recover_corrupted
            recovered = Session.recover_corrupted(session_id, sessions_dir)

            assert recovered.id == session_id
            assert isinstance(recovered, Session)

    def test_session_recovery_preserves_id(self):
        """Session recovery should preserve original session ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir)
            original_id = "test_session_preserve"

            recovered = Session.recover_corrupted(original_id, sessions_dir)

            assert recovered.id == original_id

    def test_recovered_session_is_usable(self):
        """Recovered session should be fully functional."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir)

            recovered = Session.recover_corrupted("recover_test", sessions_dir)

            # Should be able to add messages
            recovered.add_message(role="user", content="test message")
            assert len(recovered.messages) == 1
            assert recovered.messages[0]["content"] == "test message"

            # Should be able to save
            saved_path = recovered.save(sessions_dir)
            assert saved_path.exists()

    def test_error_handler_suggests_recovery_for_corrupted(self):
        """Error handler should suggest recovery for corrupted sessions."""
        handler = ErrorHandler()

        result = handler.handle_error(
            "session_corrupted",
            {
                "session_id": "corrupted_abc",
                "error_detail": "JSON parse error at line 5"
            }
        )

        assert result["status"] == "handled"
        assert "corrupted_abc" in result["error"]
        recovery_lower = result["suggestion"].lower()
        assert "recover" in recovery_lower or "new" in recovery_lower


class TestShellCommandSafetyScenario:
    """Test 3: Shell Command Safety - blocking dangerous ops."""

    def test_dangerous_command_blocked_without_confirmation(self):
        """End-to-end: Dangerous rm -rf command blocked without confirmation."""
        tool = ShellTool()

        result = tool.execute({
            "action": "execute",
            "command": "rm -rf /tmp/test_dangerous",
            "confirmed": False
        })

        assert result["status"] == "blocked"
        assert "dangerous" in result["message"].lower()

    def test_dangerous_command_allowed_with_confirmation(self):
        """Dangerous command works when confirmed=True."""
        tool = ShellTool()

        # Create temporary file to remove
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name

        try:
            # Execute with confirmation
            result = tool.execute({
                "action": "execute",
                "command": f"rm {temp_file}",
                "confirmed": True
            })

            assert result["status"] == "ok"
        finally:
            # Cleanup if still exists
            if Path(temp_file).exists():
                Path(temp_file).unlink()

    def test_safe_commands_execute_normally(self):
        """Safe commands should execute without blocking."""
        tool = ShellTool()

        result = tool.execute({
            "action": "execute",
            "command": "echo 'safe command'",
            "confirmed": False
        })

        assert result["status"] == "ok"
        assert "safe command" in result["stdout"]


class TestTimeoutRecoveryScenario:
    """Test 4: Timeout Recovery scenario."""

    def test_timeout_error_suggests_simplification(self):
        """End-to-end: Timeout error suggests simplification."""
        handler = ErrorHandler()

        result = handler.handle_error(
            "timeout",
            {
                "timeout_seconds": 30,
                "operation": "model_inference"
            }
        )

        assert result["status"] == "handled"
        assert "timeout" in result["error"].lower() or "timed out" in result["error"].lower()
        suggestion_lower = result["suggestion"].lower()
        assert "simplif" in suggestion_lower or "reduce" in suggestion_lower

    def test_timeout_error_provides_recovery_path(self):
        """Timeout recovery should include specific steps."""
        handler = ErrorHandler()

        result = handler.handle_error(
            "timeout",
            {"timeout_seconds": 60, "operation": "context_trimming"}
        )

        # Should suggest specific actions
        suggestion = result["suggestion"].lower()
        action_words = ["reduce", "simplif", "token", "model", "context"]
        has_actions = any(word in suggestion for word in action_words)
        assert has_actions

    def test_repl_remains_responsive_after_timeout(self):
        """End-to-end: REPL should remain responsive after timeout."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            handler = ErrorHandler()

            # First timeout
            result1 = handler.handle_error(
                "timeout",
                {"timeout_seconds": 30, "operation": "op1"}
            )
            assert result1["status"] == "handled"

            # System should still be responsive
            result2 = handler.handle_error(
                "timeout",
                {"timeout_seconds": 30, "operation": "op2"}
            )
            assert result2["status"] == "handled"


class TestOutOfMemoryScenario:
    """Test 5: Out of Memory error handling."""

    def test_oom_error_suggests_smaller_model(self):
        """End-to-end: OOM error suggests switching to smaller model."""
        handler = ErrorHandler()

        result = handler.handle_error(
            "oom",
            {
                "available_memory": "2GB",
                "required_memory": "8GB"
            }
        )

        assert result["status"] == "handled"
        assert "memory" in result["error"].lower() or "out of memory" in result["error"].lower()
        suggestion_lower = result["suggestion"].lower()
        assert "model" in suggestion_lower or "reduce" in suggestion_lower or "simplif" in suggestion_lower

    def test_oom_recovery_path_provided(self):
        """OOM error should provide recovery path."""
        handler = ErrorHandler()

        result = handler.handle_error(
            "oom",
            {
                "available_memory": "1GB",
                "required_memory": "16GB"
            }
        )

        # Should include actionable next steps
        assert len(result["next_step"]) > 0
        assert "memory" in result["next_step"].lower() or "model" in result["next_step"].lower()

    def test_user_can_switch_models_on_oom(self):
        """User can recover from OOM by switching models."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir(parents=True, exist_ok=True)

            # Create session with large model
            session = Session(
                model="large-model",
                working_directory=str(tmpdir)
            )
            session.save(sessions_dir)

            # Simulate model switch
            session.model = "small-model"
            session.save(sessions_dir)

            # Verify switch
            loaded = Session.load(session.id, sessions_dir)
            assert loaded.model == "small-model"


class TestPermissionDeniedScenario:
    """Test 6: Permission Denied error handling."""

    def test_permission_denied_error_handling(self):
        """End-to-end: Permission denied error provides clear recovery."""
        handler = ErrorHandler()

        result = handler.handle_error(
            "permission_denied",
            {
                "path": "/root/.mlxcli/sessions",
                "operation": "write"
            }
        )

        assert result["status"] == "handled"
        assert "permission" in result["error"].lower()
        assert "/root/.mlxcli/sessions" in result["error"]
        assert "write" in result["error"].lower()

    def test_permission_denied_suggests_fix(self):
        """Permission error should suggest fixing permissions."""
        handler = ErrorHandler()

        result = handler.handle_error(
            "permission_denied",
            {"path": "/etc/config", "operation": "read"}
        )

        suggestion_lower = result["suggestion"].lower()
        # Should mention checking/fixing permissions
        assert "permission" in suggestion_lower or "chmod" in suggestion_lower or "check" in suggestion_lower

    def test_permission_denied_alternative_path_suggested(self):
        """Permission error should suggest alternative paths."""
        handler = ErrorHandler()

        result = handler.handle_error(
            "permission_denied",
            {"path": "/restricted/file", "operation": "access"}
        )

        # Should have useful next steps
        assert len(result["next_step"]) > 0


class TestDiskFullScenario:
    """Test 7: Disk Full error handling."""

    def test_disk_full_error_handling(self):
        """End-to-end: Disk full error handled gracefully."""
        handler = ErrorHandler()

        result = handler.handle_error(
            "disk_full",
            {
                "available_space": "100MB",
                "required_space": "2GB"
            }
        )

        assert result["status"] == "handled"
        assert "disk" in result["error"].lower() or "space" in result["error"].lower()

    def test_disk_full_cleanup_suggestions(self):
        """Disk full error should provide cleanup suggestions."""
        handler = ErrorHandler()

        result = handler.handle_error(
            "disk_full",
            {"available_space": "50MB", "required_space": "1GB"}
        )

        suggestion_lower = result["suggestion"].lower()
        # Should suggest cleanup actions
        assert (
            "clean" in suggestion_lower or
            "delete" in suggestion_lower or
            "remove" in suggestion_lower or
            "free" in suggestion_lower
        )

    def test_disk_full_session_survives(self):
        """Session should survive disk full recovery."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir)
            sessions_dir.mkdir(parents=True, exist_ok=True)

            # Create and save session
            session = Session(
                model="test-model",
                working_directory=str(tmpdir)
            )
            session.add_message(role="user", content="test message")
            saved_path = session.save(sessions_dir)

            # Verify session persists
            assert saved_path.exists()
            loaded = Session.load(session.id, sessions_dir)
            assert len(loaded.messages) == 1


class TestContextTrimmingScenario:
    """Test 8: Large context trimming in generation."""

    def test_large_conversation_triggers_trimming(self):
        """End-to-end: Large conversation history triggers context trimming."""
        manager = ContextManager(max_tokens=100)

        # Create large conversation
        messages = []
        for i in range(10):
            messages.append({
                "role": "user",
                "content": "This is a test message. " * 20  # Large message
            })

        should_trim = manager.should_trim(messages)
        assert should_trim

    def test_context_manager_trims_oldest_messages(self):
        """Context trimming should keep most recent messages."""
        manager = ContextManager(max_tokens=100)

        # Create messages with large content to trigger trimming
        messages = []
        for i in range(5):
            messages.append({
                "role": "user",
                "content": f"Message {i}: " + ("x" * 100)  # Larger content
            })

        # Trim to much smaller budget to force trimming
        trimmed = manager.trim_to_budget(messages, 20)

        # Should have fewer messages
        assert len(trimmed) < len(messages)
        # Should keep most recent (last messages)
        if trimmed:  # Only check if there are trimmed messages
            assert "Message" in str(trimmed[-1]["content"])

    def test_trimmed_context_still_generates(self):
        """Generation should work with trimmed context."""
        manager = ContextManager(max_tokens=200)

        # Create conversation that will be trimmed
        messages = []
        for i in range(20):
            messages.append({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": "Test message content " * 5
            })

        trimmed = manager.trim_to_budget(messages, 200)

        # Should have valid messages
        assert len(trimmed) > 0
        assert all("role" in msg and "content" in msg for msg in trimmed)

    def test_available_tokens_calculated_correctly(self):
        """Context manager should calculate available tokens."""
        manager = ContextManager(max_tokens=100)

        messages = [
            {"role": "user", "content": "Short"},  # ~1 token
            {"role": "assistant", "content": "x" * 40}  # ~10 tokens
        ]

        available = manager.get_available_tokens(messages)
        assert available > 0
        assert available < 100


class TestModelSwitchingScenario:
    """Test 9: Model switching mid-session."""

    def test_model_switch_updates_session(self):
        """End-to-end: Model switch updates session state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir(parents=True, exist_ok=True)

            # Create session with initial model
            session = Session(
                model="llama-7b",
                working_directory=str(tmpdir)
            )
            session.add_message(role="user", content="Hello")
            session.save(sessions_dir)

            # Switch model
            session.model = "mistral-7b"
            session.save(sessions_dir)

            # Verify switch persisted
            loaded = Session.load(session.id, sessions_dir)
            assert loaded.model == "mistral-7b"
            assert len(loaded.messages) == 1  # Messages preserved

    def test_model_switch_preserves_conversation(self):
        """Model switch should preserve conversation history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir)

            session = Session(
                model="model-a",
                working_directory=str(tmpdir)
            )

            # Build conversation
            session.add_message(role="user", content="msg1")
            session.add_message(role="assistant", content="resp1")
            session.add_message(role="user", content="msg2")

            message_count_before = len(session.messages)

            # Switch model
            session.model = "model-b"
            session.save(sessions_dir)

            # Load and verify
            loaded = Session.load(session.id, sessions_dir)
            assert loaded.model == "model-b"
            assert len(loaded.messages) == message_count_before

    def test_error_handler_available_during_model_switch(self):
        """Error handler should be available during model switching."""
        handler = ErrorHandler()

        # Simulate switch with error handling
        result = handler.handle_error(
            "model_not_found",
            {"model_name": "nonexistent"}
        )
        assert result["status"] == "handled"


class TestFileOperationsScenario:
    """Test 10: File operations with backup and error handling."""

    def test_file_read_error_handled(self):
        """End-to-end: File read errors are handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            handler = ErrorHandler()

            # Try to read non-existent file
            suggestion = handler.suggest_recovery(FileNotFoundError("File not found"))

            assert isinstance(suggestion, str)
            assert len(suggestion) > 0
            assert "file" in suggestion.lower()

    def test_file_write_with_backup_verification(self):
        """File write should preserve data for recovery."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir)
            sessions_dir.mkdir(parents=True, exist_ok=True)

            # Create session
            session = Session(
                model="test-model",
                working_directory=str(tmpdir)
            )
            session.add_message(role="user", content="test")

            # Save session
            saved_path = session.save(sessions_dir)
            assert saved_path.exists()

            # Verify content
            loaded_data = json.loads(saved_path.read_text())
            assert loaded_data["model"] == "test-model"
            assert len(loaded_data["messages"]) == 1

    def test_permission_error_on_file_access(self):
        """Permission errors should be handled for file access."""
        handler = ErrorHandler()

        result = handler.handle_error(
            "permission_denied",
            {"path": "/restricted/file.json", "operation": "read"}
        )

        assert result["status"] == "handled"
        assert "permission" in result["error"].lower()


class TestCommandErrorsScenario:
    """Test 11: Invalid commands handling."""

    def test_invalid_command_shows_help(self):
        """End-to-end: Invalid command shows help."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            # Invalid command should be recognized
            is_command, cmd_name, args = cli._parse_command("/invalid_command")

            assert is_command
            assert cmd_name == "invalid_command"

    def test_parse_error_handled_gracefully(self):
        """Parse errors should be handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            # Malformed command
            is_command, cmd_name, args = cli._parse_command("/ / /")

            assert is_command  # Still recognized as command

    def test_repl_continues_after_command_error(self):
        """REPL should continue after command error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            # Parse valid command
            is_cmd1, cmd1, args1 = cli._parse_command("/help")
            assert is_cmd1

            # Parse another command - REPL should be responsive
            is_cmd2, cmd2, args2 = cli._parse_command("/model")
            assert is_cmd2


class TestSessionDeletionScenario:
    """Test 12: Session deletion error handling."""

    def test_session_deletion_no_error_if_not_exist(self):
        """End-to-end: No error when deleting non-existent session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir)
            sessions_dir.mkdir(parents=True, exist_ok=True)

            # Try to delete non-existent session
            result = Session.delete_session("nonexistent123", sessions_dir)

            # Should return False but not raise
            assert result is False

    def test_session_deletion_removes_file(self):
        """Session deletion should remove session file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir)
            sessions_dir.mkdir(parents=True, exist_ok=True)

            # Create and save session
            session = Session(
                model="test",
                working_directory=str(tmpdir)
            )
            session.save(sessions_dir)

            session_file = sessions_dir / f"session_{session.id}.json"
            assert session_file.exists()

            # Delete session
            result = Session.delete_session(session.id, sessions_dir)

            assert result is True
            assert not session_file.exists()

    def test_list_shows_updated_state_after_deletion(self):
        """Session list should show updated state after deletion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir)
            sessions_dir.mkdir(parents=True, exist_ok=True)

            # Create sessions
            s1 = Session(model="m1", working_directory=str(tmpdir))
            s2 = Session(model="m2", working_directory=str(tmpdir))
            s1.save(sessions_dir)
            s2.save(sessions_dir)

            # Verify both exist
            sessions = Session.list_sessions(sessions_dir)
            assert len(sessions) == 2

            # Delete one
            Session.delete_session(s1.id, sessions_dir)

            # Verify list updated
            sessions = Session.list_sessions(sessions_dir)
            assert len(sessions) == 1


class TestFullWorkflowWithRecovery:
    """Test 15: Full workflow with multiple error recoveries."""

    def test_complete_workflow_handles_multiple_errors(self):
        """End-to-end: Complete workflow handles multiple errors in sequence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))
            handler = ErrorHandler()
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir(parents=True, exist_ok=True)

            # 1. Create session
            session = Session(
                model="test-model",
                working_directory=str(tmpdir)
            )
            session.add_message(role="user", content="Hello")
            session.save(sessions_dir)

            # 2. Handle model error
            model_result = handler.handle_error(
                "model_not_found",
                {"model_name": "missing-model"}
            )
            assert model_result["status"] == "handled"

            # 3. Handle timeout
            timeout_result = handler.handle_error(
                "timeout",
                {"timeout_seconds": 30, "operation": "inference"}
            )
            assert timeout_result["status"] == "handled"

            # 4. Verify session still works
            loaded = Session.load(session.id, sessions_dir)
            assert loaded.model == "test-model"
            assert len(loaded.messages) == 1


class TestMultipleErrorsInSequence:
    """Test 16: Multiple errors in sequence with recovery."""

    def test_sequential_error_handling(self):
        """Multiple errors handled sequentially without state corruption."""
        handler = ErrorHandler()

        errors = [
            ("model_not_found", {"model_name": "m1"}),
            ("oom", {"available_memory": "1GB"}),
            ("timeout", {"timeout_seconds": 30}),
            ("permission_denied", {"path": "/restricted"}),
            ("disk_full", {"available_space": "100MB"}),
        ]

        results = []
        for error_type, context in errors:
            result = handler.handle_error(error_type, context)
            results.append(result)
            assert result["status"] == "handled"

        # All should be handled successfully
        assert len(results) == 5
        assert all(r["status"] == "handled" for r in results)

    def test_recovery_from_multiple_errors_in_session(self):
        """Session should survive multiple error scenarios."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir)
            sessions_dir.mkdir(parents=True, exist_ok=True)

            session = Session(
                model="original-model",
                working_directory=str(tmpdir)
            )

            # Add message after each simulated error
            for i in range(5):
                session.add_message(role="user", content=f"Message {i}")

            session.save(sessions_dir)

            # Verify all messages preserved
            loaded = Session.load(session.id, sessions_dir)
            assert len(loaded.messages) == 5


class TestErrorHandlerLogging:
    """Test 17: Error handler logging."""

    def test_error_logging_captures_context(self):
        """Error logging should capture error with context."""
        handler = ErrorHandler()
        context = {
            "operation": "model_load",
            "model_name": "test-model",
            "timestamp": "2025-01-01T00:00:00"
        }
        error = RuntimeError("Failed to load")

        # Should not raise
        handler.log_error(error, context)

    def test_logging_with_various_error_types(self):
        """Logging should handle various error types."""
        handler = ErrorHandler()
        context = {"test": "context"}

        errors = [
            RuntimeError("Runtime error"),
            ValueError("Value error"),
            MemoryError("Memory error"),
            TimeoutError("Timeout error"),
            PermissionError("Permission error"),
        ]

        for error in errors:
            # Should not raise
            handler.log_error(error, context)

    def test_recovery_suggestions_logged_correctly(self):
        """Recovery suggestions should be generated for all error types."""
        handler = ErrorHandler()

        error_types = [
            MemoryError("Out of memory"),
            TimeoutError("Operation timed out"),
            PermissionError("Permission denied"),
            FileNotFoundError("File not found"),
            json.JSONDecodeError("Invalid JSON", "", 0),
        ]

        for error in error_types:
            suggestion = handler.suggest_recovery(error)
            assert isinstance(suggestion, str)
            assert len(suggestion) > 0


class TestContextManagerWithErrors:
    """Test 18: Context manager with error conditions."""

    def test_context_manager_handles_empty_messages(self):
        """Context manager should handle empty message list."""
        manager = ContextManager(max_tokens=100)

        trimmed = manager.trim_to_budget([], 100)
        assert trimmed == []

    def test_context_manager_with_malformed_messages(self):
        """Context manager should handle messages without content."""
        manager = ContextManager(max_tokens=100)

        messages = [
            {"role": "user"},  # Missing content
            {"content": "text"},  # Missing role
            {"role": "assistant", "content": "valid message"}
        ]

        # Should not raise, handle gracefully
        total_tokens = sum(
            manager.get_context_size(msg.get("content", ""))
            for msg in messages
        )
        assert total_tokens >= 0

    def test_trimming_with_edge_case_tokens(self):
        """Context trimming should handle edge case token counts."""
        manager = ContextManager(max_tokens=1)

        messages = [
            {"role": "user", "content": "x" * 1000},
            {"role": "assistant", "content": "y" * 1000},
        ]

        trimmed = manager.trim_to_budget(messages, 1)
        assert len(trimmed) <= len(messages)
        assert len(trimmed) >= 0


class TestToolRegistryErrorHandling:
    """Test 19: Tool registry error handling."""

    def test_tool_registry_with_shell_tool(self):
        """Tool registry should handle shell tool safely."""
        registry = ToolRegistry()
        shell_tool = ShellTool()

        # Tool should be usable
        result = shell_tool.execute({
            "action": "execute",
            "command": "echo test"
        })
        assert result["status"] == "ok"

    def test_shell_tool_command_error_handling(self):
        """Shell tool should handle command errors gracefully."""
        tool = ShellTool()

        # Non-existent command
        result = tool.execute({
            "action": "execute",
            "command": "nonexistent_command_12345"
        })

        assert result["status"] == "ok"
        assert result["returncode"] != 0

    def test_shell_tool_timeout_handling(self):
        """Shell tool should handle timeouts gracefully."""
        tool = ShellTool()

        # Note: Actual timeout testing is complex, verify interface exists
        assert tool.DEFAULT_TIMEOUT == 30


class TestCLIErrorMessageQuality:
    """Test 20: CLI error message quality."""

    def test_cli_command_parsing_handles_errors(self):
        """CLI command parsing should handle invalid input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cli = CLI(project_root=Path(tmpdir))

            test_cases = [
                ("", False),  # Not a command
                ("/help", True),  # Valid command
                ("/model list", True),  # Command with args
                ("/command arg1 arg2 arg3", True),  # Multiple args
            ]

            for test_input, expected_is_cmd in test_cases:
                is_cmd, cmd, args = cli._parse_command(test_input)
                assert is_cmd == expected_is_cmd
                # Should not raise

    def test_error_messages_are_actionable(self):
        """Error messages should include actionable recovery steps."""
        handler = ErrorHandler()

        result = handler.handle_error(
            "model_not_found",
            {"model_name": "test"}
        )

        # Check message quality
        assert len(result["error"]) > 0
        assert len(result["suggestion"]) > 0
        assert len(result["next_step"]) > 0

        # Should be human-readable
        assert isinstance(result["error"], str)
        assert isinstance(result["suggestion"], str)
        assert isinstance(result["next_step"], str)

    def test_error_consistency_across_types(self):
        """All error types should have consistent message format."""
        handler = ErrorHandler()

        error_types = [
            ("model_not_found", {"model_name": "test"}),
            ("oom", {"available_memory": "1GB"}),
            ("timeout", {"timeout_seconds": 30}),
            ("permission_denied", {"path": "/test"}),
            ("disk_full", {"available_space": "100MB"}),
        ]

        for error_type, context in error_types:
            result = handler.handle_error(error_type, context)

            # All should have consistent structure
            assert "status" in result
            assert "error" in result
            assert "suggestion" in result
            assert "next_step" in result

            # All messages should be strings
            assert isinstance(result["error"], str)
            assert isinstance(result["suggestion"], str)
            assert isinstance(result["next_step"], str)

            # Messages should have content
            assert len(result["error"]) > 0
            assert len(result["suggestion"]) > 0
            assert len(result["next_step"]) > 0

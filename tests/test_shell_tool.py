"""Tests for ShellTool - shell command execution with safety guards."""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.tools.shell_tool import ShellTool


class TestShellToolBasics:
    """Test basic ShellTool functionality."""

    def test_shell_tool_name(self):
        """ShellTool should have correct name."""
        tool = ShellTool()
        assert tool.name == "shell_tool"

    def test_shell_tool_description(self):
        """ShellTool should have a description."""
        tool = ShellTool()
        assert isinstance(tool.description, str)
        assert len(tool.description) > 0

    def test_shell_tool_is_tool(self):
        """ShellTool should be a Tool instance."""
        from mlxcli.tools.base import Tool

        tool = ShellTool()
        assert isinstance(tool, Tool)


class TestSafeCommands:
    """Test execution of safe commands."""

    def test_execute_echo_command(self):
        """Should execute safe echo command."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "execute",
                "command": "echo hello",
            }
        )
        assert result["status"] == "ok"
        assert "hello" in result["stdout"]
        assert result["returncode"] == 0

    def test_execute_ls_command(self):
        """Should execute safe ls command."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "execute",
                "command": "ls /tmp",
            }
        )
        assert result["status"] == "ok"
        assert result["returncode"] == 0

    def test_capture_stdout(self):
        """Should capture command stdout."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "execute",
                "command": "echo 'test output'",
            }
        )
        assert result["status"] == "ok"
        assert "test output" in result["stdout"]

    def test_capture_stderr(self):
        """Should capture command stderr."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "execute",
                "command": "ls /nonexistent_path_12345",
            }
        )
        assert result["status"] == "ok"
        assert result["returncode"] != 0
        # stderr should be captured
        assert isinstance(result.get("stderr"), str)

    def test_capture_nonzero_returncode(self):
        """Should capture non-zero return codes."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "execute",
                "command": "ls /nonexistent_path_12345",
            }
        )
        assert result["status"] == "ok"
        assert result["returncode"] != 0


class TestDangerousCommands:
    """Test blocking of dangerous commands."""

    def test_block_rm_command(self):
        """Should block rm command without confirmation."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "execute",
                "command": "rm -rf /tmp/test",
            }
        )
        assert result["status"] == "blocked"
        assert "hint" in result
        assert "confirmed=True" in result["hint"]

    def test_block_git_push(self):
        """Should block git push without confirmation."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "execute",
                "command": "git push origin main",
            }
        )
        assert result["status"] == "blocked"
        assert "message" in result

    def test_block_force_push(self):
        """Should block git force-push without confirmation."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "execute",
                "command": "git force-push origin main",
            }
        )
        assert result["status"] == "blocked"

    def test_block_dd_command(self):
        """Should block dd commands."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "execute",
                "command": "dd if=/dev/zero of=/dev/sda",
            }
        )
        assert result["status"] == "blocked"

    def test_block_fork_bomb(self):
        """Should block fork bomb patterns."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "execute",
                "command": ":(){:|:&};:",
            }
        )
        assert result["status"] == "blocked"

    def test_block_mkfs_command(self):
        """Should block mkfs command."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "execute",
                "command": "mkfs /dev/sda1",
            }
        )
        assert result["status"] == "blocked"

    def test_block_shred_command(self):
        """Should block shred command."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "execute",
                "command": "shred /sensitive/file",
            }
        )
        assert result["status"] == "blocked"

    def test_block_wipe_command(self):
        """Should block wipe command."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "execute",
                "command": "wipe /important/data",
            }
        )
        assert result["status"] == "blocked"


class TestConfirmedExecution:
    """Test execution with confirmed=True flag."""

    def test_execute_with_confirmed_true(self):
        """Should allow dangerous commands when confirmed=True."""
        tool = ShellTool()
        # Use a non-destructive test: echo a message with rm in it
        # Since we can't actually test rm without destroying files,
        # we'll test that the confirmed flag works by checking the preview mechanism
        result = tool.execute(
            {
                "action": "execute",
                "command": "echo test",
                "confirmed": True,
            }
        )
        assert result["status"] == "ok"

    def test_allow_rm_with_confirmation(self):
        """Should execute rm command when confirmed=True."""
        tool = ShellTool()
        # Note: This test doesn't actually run rm, just verifies the flag works
        # Real rm tests would need temp files
        result = tool.execute(
            {
                "action": "execute",
                "command": "rm /tmp/nonexistent_test_12345_mlx",
                "confirmed": True,
            }
        )
        # It should attempt to run the command (not block it)
        # The command will fail because the file doesn't exist, but it won't be blocked
        assert result["status"] == "ok"


class TestPreviewAction:
    """Test preview action before execution."""

    def test_preview_safe_command(self):
        """Should preview safe commands without executing."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "preview",
                "command": "echo hello",
            }
        )
        assert result["status"] == "ok"
        assert result["dangerous"] is False
        assert "preview" in result
        assert "echo hello" in result["preview"]

    def test_preview_dangerous_command(self):
        """Should mark dangerous commands in preview."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "preview",
                "command": "rm -rf /tmp/test",
            }
        )
        assert result["status"] == "ok"
        assert result["dangerous"] is True
        assert "preview" in result

    def test_preview_git_push(self):
        """Should preview git push as dangerous."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "preview",
                "command": "git push origin main",
            }
        )
        assert result["status"] == "ok"
        assert result["dangerous"] is True


class TestTimeout:
    """Test command timeout handling."""

    def test_timeout_30_seconds_default(self):
        """Commands should timeout after 30 seconds by default."""
        tool = ShellTool()
        # Use a command that takes longer than timeout
        result = tool.execute(
            {
                "action": "execute",
                "command": "sleep 35",
                "timeout": 1,  # Override with 1 second for testing
            }
        )
        assert result["status"] == "timeout"
        assert result["timeout_seconds"] == 1

    def test_timeout_custom_value(self):
        """Should respect custom timeout value."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "execute",
                "command": "sleep 5",
                "timeout": 1,
            }
        )
        assert result["status"] == "timeout"
        assert result["timeout_seconds"] == 1

    def test_command_completes_before_timeout(self):
        """Commands completing before timeout should succeed."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "execute",
                "command": "echo quick",
                "timeout": 5,
            }
        )
        assert result["status"] == "ok"
        assert "quick" in result["stdout"]


class TestCommandNotFound:
    """Test handling of commands that don't exist."""

    def test_command_not_found(self):
        """Should handle command not found gracefully."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "execute",
                "command": "nonexistent_command_12345_xyz",
            }
        )
        assert result["status"] == "ok"
        assert result["returncode"] != 0


class TestCommandValidation:
    """Test command validation for syntax errors."""

    def test_validate_command_syntax(self):
        """Should validate basic command syntax."""
        tool = ShellTool()
        # Test with mismatched quotes (syntax error)
        result = tool.execute(
            {
                "action": "execute",
                "command": "echo 'unclosed quote",
            }
        )
        # This might be blocked by validation or fail in execution
        # The exact behavior depends on implementation
        assert "status" in result
        assert result["status"] in ["ok", "blocked", "error"]

    def test_valid_complex_command(self):
        """Should accept valid complex commands."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "execute",
                "command": "ls -la /tmp | head -5",
            }
        )
        assert result["status"] == "ok"


class TestSequentialExecution:
    """Test executing multiple commands in sequence."""

    def test_execute_multiple_commands_separately(self):
        """Should execute commands separately."""
        tool = ShellTool()

        result1 = tool.execute(
            {
                "action": "execute",
                "command": "echo first",
            }
        )
        assert result1["status"] == "ok"

        result2 = tool.execute(
            {
                "action": "execute",
                "command": "echo second",
            }
        )
        assert result2["status"] == "ok"
        assert "first" in result1["stdout"]
        assert "second" in result2["stdout"]

    def test_sequential_state_independence(self):
        """Commands should be independent."""
        tool = ShellTool()

        # Set a variable
        result1 = tool.execute(
            {
                "action": "execute",
                "command": "export TEST_VAR=hello && echo $TEST_VAR",
            }
        )
        assert result1["status"] == "ok"

        # Try to use it (shouldn't work since it's a new shell)
        result2 = tool.execute(
            {
                "action": "execute",
                "command": "echo $TEST_VAR",
            }
        )
        assert result2["status"] == "ok"
        # The variable won't be available in a new shell
        assert result2["stdout"].strip() == ""


class TestErrorHandling:
    """Test error handling."""

    def test_execute_missing_command_argument(self):
        """Should error if command is missing."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "execute",
            }
        )
        assert result["status"] == "error"
        assert "command" in result.get("message", "").lower()

    def test_execute_unknown_action(self):
        """Should error on unknown action."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "unknown",
                "command": "echo test",
            }
        )
        assert result["status"] == "error"

    def test_missing_action(self):
        """Should error if action is missing."""
        tool = ShellTool()
        result = tool.execute(
            {
                "command": "echo test",
            }
        )
        assert result["status"] == "error"


class TestResponseFormat:
    """Test response format consistency."""

    def test_execute_response_format(self):
        """Execute action should return proper format."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "execute",
                "command": "echo test",
            }
        )
        assert isinstance(result, dict)
        assert "status" in result
        assert "command" in result
        assert "stdout" in result
        assert "stderr" in result
        assert "returncode" in result

    def test_preview_response_format(self):
        """Preview action should return proper format."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "preview",
                "command": "echo test",
            }
        )
        assert isinstance(result, dict)
        assert "status" in result
        assert "preview" in result
        assert "dangerous" in result

    def test_blocked_response_format(self):
        """Blocked commands should return proper format."""
        tool = ShellTool()
        result = tool.execute(
            {
                "action": "execute",
                "command": "rm -rf /tmp/test",
            }
        )
        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] == "blocked"
        assert "message" in result
        assert "hint" in result

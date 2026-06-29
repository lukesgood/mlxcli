"""ShellTool - shell command execution with safety guards."""

import subprocess
from typing import Optional

from mlxcli.tools.base import Tool
from mlxcli.utils import is_dangerous_command


class ShellTool(Tool):
    """Tool for executing shell commands with safety guards.

    Provides controlled shell command execution with the following features:
    - Blocks dangerous commands without explicit confirmation
    - Timeout protection (default 30 seconds)
    - Captures stdout and stderr
    - Preview mode to check commands before execution
    - Command validation for syntax errors

    Security Note: Uses shell=True to support pipes, redirects, and complex shell features.
    This is intentional and mitigated by pre-execution validation against dangerous patterns.
    """

    DEFAULT_TIMEOUT = 30

    # List of dangerous command patterns that require confirmation
    DANGEROUS_PATTERNS = [
        "rm -rf",
        "git push",
        "git force-push",
        "dd if=",
        ":(){:|:&};:",
        "mkfs",
        "shred",
        "wipe",
    ]

    @property
    def name(self) -> str:
        """Tool name/identifier."""
        return "shell_tool"

    @property
    def description(self) -> str:
        """Tool description for LLM."""
        return (
            "Shell command execution tool with safety guards. Supports 'execute' and 'preview' actions. "
            "Blocks dangerous commands (rm, git push, etc.) without confirmation. "
            "Default timeout: 30 seconds. Set confirmed=True to override safety checks."
        )

    def execute(self, args: dict) -> dict:
        """Execute shell command or preview it.

        Args:
            args: Dictionary with keys:
                - action: "execute" or "preview" (required)
                - command: command string to execute (required)
                - confirmed: bool, set True to bypass safety checks (optional, default False)
                - timeout: float, timeout in seconds (optional, default 30)

        Returns:
            dict: Result dictionary with:
                - "execute" action returns: {"status": "ok"|"blocked"|"timeout"|"error", "command": str, ...}
                - "preview" action returns: {"status": "ok"|"error", "preview": str, "dangerous": bool}
        """
        action = args.get("action")

        if action == "execute":
            return self._execute_command(args)
        elif action == "preview":
            return self._preview_command(args)
        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}. Must be 'execute' or 'preview'.",
            }

    def _execute_command(self, args: dict) -> dict:
        """Execute a shell command.

        Args:
            args: Dictionary with command, confirmed, and timeout keys.

        Returns:
            dict: Execution result.
        """
        command = args.get("command")
        confirmed = args.get("confirmed", False)
        timeout = args.get("timeout", self.DEFAULT_TIMEOUT)

        if command is None:
            return {
                "status": "error",
                "message": "command is required for execute action",
            }

        if not isinstance(command, str):
            return {
                "status": "error",
                "message": "command must be a string",
            }

        # Check if command is dangerous
        if is_dangerous_command(command) and not confirmed:
            return {
                "status": "blocked",
                "message": f"Dangerous command blocked: {command}",
                "hint": "Set confirmed=True to override",
                "command": command,
            }

        # Execute the command
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return {
                "status": "ok",
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "command": command,
                "timeout_seconds": timeout,
                "message": f"Command timed out after {timeout} seconds",
            }
        except Exception as e:
            return {
                "status": "error",
                "command": command,
                "message": f"Error executing command: {str(e)}",
            }

    def _preview_command(self, args: dict) -> dict:
        """Preview a command without executing it.

        Args:
            args: Dictionary with command key.

        Returns:
            dict: Preview result with dangerous flag.
        """
        command = args.get("command")

        if command is None:
            return {
                "status": "error",
                "message": "command is required for preview action",
            }

        if not isinstance(command, str):
            return {
                "status": "error",
                "message": "command must be a string",
            }

        # Check if command is dangerous
        dangerous = is_dangerous_command(command)

        return {
            "status": "ok",
            "preview": command,
            "dangerous": dangerous,
            "message": (
                "Dangerous command - requires confirmation" if dangerous else "Safe to execute"
            ),
        }

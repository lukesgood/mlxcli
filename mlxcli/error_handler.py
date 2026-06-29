"""ErrorHandler - centralized error handling with recovery strategies.

Provides consistent error handling across MLX-CLI with recovery strategies
for common failure modes.
"""

import json
import logging
from typing import Any, Optional

# Configure logging for error handler
logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling with recovery strategies.

    Provides methods to:
    - Handle errors with actionable recovery suggestions
    - Generate recovery suggestions for exceptions
    - Log errors with context

    Supports the following error types:
    - model_not_found: Model not available locally
    - oom: Out of memory
    - session_corrupted: Session file corrupted
    - timeout: Operation timed out
    - permission_denied: Access denied
    - disk_full: Not enough disk space
    """

    def __init__(self) -> None:
        """Initialize ErrorHandler."""
        self.error_types = {
            "model_not_found",
            "oom",
            "session_corrupted",
            "timeout",
            "permission_denied",
            "disk_full",
        }

    def handle_error(self, error_type: str, context: dict) -> dict:
        """Handle error and return recovery information.

        Provides consistent error handling with actionable recovery suggestions.

        Args:
            error_type: Type of error (one of known error types or custom string).
            context: Dictionary with error context (e.g., model_name, available_memory).

        Returns:
            Dictionary with keys:
            - status: "handled"
            - error: Human-readable error message
            - suggestion: Detailed recovery steps
            - next_step: What user should do next
            - Additional context fields as needed
        """
        if error_type == "model_not_found":
            return self._handle_model_not_found(context)
        elif error_type == "oom":
            return self._handle_oom(context)
        elif error_type == "session_corrupted":
            return self._handle_session_corrupted(context)
        elif error_type == "timeout":
            return self._handle_timeout(context)
        elif error_type == "permission_denied":
            return self._handle_permission_denied(context)
        elif error_type == "disk_full":
            return self._handle_disk_full(context)
        else:
            return self._handle_unknown_error(error_type, context)

    def suggest_recovery(self, error: Exception) -> str:
        """Generate recovery suggestion for an exception.

        Maps exception types to recovery strategies and returns actionable advice.

        Args:
            error: The exception to generate recovery for.

        Returns:
            str: Actionable recovery suggestion.
        """
        if isinstance(error, MemoryError):
            return (
                "Out of memory: Try simplifying your prompt, reducing the number of "
                "messages in context, or reducing max_tokens. If the issue persists, "
                "consider using a smaller model or increasing available system memory."
            )
        elif isinstance(error, TimeoutError):
            return (
                "Operation timed out: Try simplifying the prompt, reducing the model context, "
                "or increasing the timeout duration. If the model is too slow, consider using "
                "a smaller or faster model."
            )
        elif isinstance(error, PermissionError):
            return (
                "Permission denied: Check file/directory permissions. Ensure you have "
                "read/write access to the required paths. Try running 'chmod 755' on the "
                "directory or contacting your system administrator."
            )
        elif isinstance(error, FileNotFoundError):
            return (
                "File or resource not found: Verify the path exists and is correct. "
                "Check that all required dependencies are installed. "
                "Ensure the file hasn't been moved or deleted."
            )
        elif isinstance(error, json.JSONDecodeError):
            return (
                "Invalid JSON format: Check the JSON file for syntax errors. "
                "Verify that the file hasn't been corrupted. You may need to recover "
                "from a backup or recreate the configuration."
            )
        else:
            return (
                "An unexpected error occurred. Check the error message above for details. "
                "If the problem persists, try restarting the application or checking logs."
            )

    def log_error(self, error: Exception, context: dict) -> None:
        """Log error with context information.

        Args:
            error: The exception to log.
            context: Dictionary with additional context information.
        """
        context_str = json.dumps(context) if context else ""
        logger.error(f"{type(error).__name__}: {str(error)}", extra={"context": context_str})

    # Private methods for handling specific error types

    def _handle_model_not_found(self, context: dict) -> dict:
        """Handle model_not_found error."""
        model_name = context.get("model_name", "unknown")
        return {
            "status": "handled",
            "error": f"Model '{model_name}' not found locally",
            "suggestion": (
                f"The model '{model_name}' is not available on your system. "
                "You can download it using the MLX model downloader. "
                "Run: mlxcli download-model --model {model_name} "
                "or manually download from Hugging Face Model Hub."
            ),
            "next_step": (
                "Download the model or choose a different available model. "
                "Use 'mlxcli list-models' to see available models."
            ),
            "model_name": model_name,
        }

    def _handle_oom(self, context: dict) -> dict:
        """Handle out of memory error."""
        available = context.get("available_memory", "unknown")
        required = context.get("required_memory", "unknown")
        return {
            "status": "handled",
            "error": f"Out of memory (available: {available}, required: {required})",
            "suggestion": (
                "The model requires more memory than available. Try: "
                "1. Reduce max_tokens parameter, "
                "2. Reduce number of messages in context, "
                "3. Use a smaller model, "
                "4. Close other applications to free memory, "
                "5. Increase system RAM or enable swap memory."
            ),
            "next_step": "Simplify your request or use a smaller model.",
            "available_memory": available,
            "required_memory": required,
        }

    def _handle_session_corrupted(self, context: dict) -> dict:
        """Handle session_corrupted error."""
        session_id = context.get("session_id", "unknown")
        error_detail = context.get("error_detail", "unknown")
        return {
            "status": "handled",
            "error": f"Session '{session_id}' corrupted: {error_detail}",
            "suggestion": (
                "The session file is corrupted and cannot be loaded. "
                "You can recover by creating a new session with the same ID using "
                "Session.recover_corrupted(), or manually delete the corrupted file "
                "and start a new session. The corrupted file is saved in "
                ".mlxcli/sessions/session_{session_id}.json"
            ),
            "next_step": ("Create a new session or recover using recover_corrupted() method."),
            "session_id": session_id,
            "error_detail": error_detail,
        }

    def _handle_timeout(self, context: dict) -> dict:
        """Handle timeout error."""
        timeout_seconds = context.get("timeout_seconds", "unknown")
        operation = context.get("operation", "operation")
        return {
            "status": "handled",
            "error": f"Operation '{operation}' timed out after {timeout_seconds}s",
            "suggestion": (
                "The operation took too long. Try: "
                "1. Simplify your prompt or query, "
                "2. Reduce the number of messages in context, "
                "3. Lower max_tokens, "
                "4. Use a faster model, "
                "5. Increase timeout duration if appropriate."
            ),
            "next_step": "Simplify your request and try again.",
            "timeout_seconds": timeout_seconds,
            "operation": operation,
        }

    def _handle_permission_denied(self, context: dict) -> dict:
        """Handle permission_denied error."""
        path = context.get("path", "unknown")
        operation = context.get("operation", "access")
        return {
            "status": "handled",
            "error": f"Permission denied for {operation} at '{path}'",
            "suggestion": (
                f"You don't have permission to {operation} at '{path}'. "
                "Try: 1. Check file/directory permissions with 'ls -la {path}', "
                "2. Change permissions with 'chmod' if you own the file, "
                "3. Ensure the path is correct and accessible, "
                "4. Contact system administrator if needed."
            ),
            "next_step": f"Fix permissions at '{path}' and try again.",
            "path": path,
            "operation": operation,
        }

    def _handle_disk_full(self, context: dict) -> dict:
        """Handle disk_full error."""
        available = context.get("available_space", "unknown")
        required = context.get("required_space", "unknown")
        return {
            "status": "handled",
            "error": f"Disk full (available: {available}, required: {required})",
            "suggestion": (
                "Not enough disk space available. Try: "
                "1. Delete unnecessary files or old models, "
                "2. Clear cache files in ~/.cache or .mlxcli/cache, "
                "3. Remove old session files from .mlxcli/sessions, "
                "4. Move to a different disk with more space, "
                "5. Archive old projects to external storage."
            ),
            "next_step": "Free up disk space and try again.",
            "available_space": available,
            "required_space": required,
        }

    def _handle_unknown_error(self, error_type: str, context: dict) -> dict:
        """Handle unknown error type gracefully."""
        return {
            "status": "handled",
            "error": f"Unknown error type: {error_type}",
            "suggestion": (
                "An unexpected error occurred. Check the error details above. "
                "If the problem persists, enable debug logging or check the logs "
                "at .mlxcli/logs/ for more information."
            ),
            "next_step": "Review the error details and check logs for more information.",
            "error_type": error_type,
            "context": context,
        }

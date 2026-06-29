"""CodeExecutionTool - sandboxed code execution with security constraints."""

import ast
import io
import signal
import subprocess
import sys
import threading
import traceback
from contextlib import redirect_stderr, redirect_stdout
from typing import Tuple

from mlxcli.tools.base import Tool


class CodeExecutionTool(Tool):
    """Execute code safely with restrictions.

    Provides sandboxed code execution for Python and shell with:
    - Security checks for dangerous imports and builtins (Python)
    - Security checks for dangerous commands (shell)
    - 10-second default timeout (configurable 1-30 seconds)
    - Output capture (stdout, stderr)
    - Comprehensive error reporting
    """

    DEFAULT_TIMEOUT = 10
    MAX_TIMEOUT = 30

    # Blocked Python imports
    BLOCKED_IMPORTS = {
        "os",
        "sys",
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "http",
        "platform",
        "pwd",
        "grp",
        "__import__",
        "importlib",
        "imp",
    }

    # Blocked Python builtins
    BLOCKED_BUILTINS = {
        "open",
        "file",
        "execfile",
        "exec",
        "eval",
        "__import__",
        "compile",
        "breakpoint",
        "globals",
        "locals",
        "vars",
        "dir",
    }

    # Blocked shell commands
    BLOCKED_SHELL_PATTERNS = [
        "nc ",
        "ncat ",
        "telnet ",
        "ssh ",
        "scp ",
        "sftp ",
        "rm -rf",
        "rm ",
        "rmdir ",
        "mkfs ",
        "shred ",
        "wipe ",
        "dd ",
        "chmod ",
        "chown ",
        "curl ",
        "wget ",
    ]

    @property
    def name(self) -> str:
        """Tool name/identifier."""
        return "CodeExecutionTool"

    @property
    def description(self) -> str:
        """Tool description for LLM."""
        return (
            "Execute Python or shell code with restrictions. 10s timeout, "
            "no network/arbitrary file access. Supports 'python' and 'shell' languages."
        )

    def execute(self, args: dict) -> dict:
        """Execute code safely.

        Args:
            args: Dictionary with keys:
                - code: str (code to execute, required)
                - language: "python" | "shell" (required)
                - timeout: int (seconds, default 10, max 30, optional)

        Returns:
            dict with:
                - status: "ok" | "error" | "timeout" | "security_violation"
                - language: str
                - code: str
                - stdout: str
                - stderr: str
                - returncode: int (for shell only)
                - message: str (on error/security_violation)
        """
        # Validate required parameters
        code = args.get("code")
        language = args.get("language")
        timeout = args.get("timeout", self.DEFAULT_TIMEOUT)

        if code is None:
            return {
                "status": "error",
                "message": "code parameter is required",
            }

        if not isinstance(code, str):
            return {
                "status": "error",
                "message": "code must be a string",
            }

        if language is None:
            return {
                "status": "error",
                "message": "language parameter is required",
            }

        if language not in ("python", "shell"):
            return {
                "status": "error",
                "message": f"language must be 'python' or 'shell', got '{language}'",
            }

        if not isinstance(timeout, int) or timeout < 1 or timeout > self.MAX_TIMEOUT:
            return {
                "status": "error",
                "message": f"timeout must be integer between 1 and {self.MAX_TIMEOUT}",
            }

        # Execute based on language
        if language == "python":
            return self._execute_python(code, timeout)
        else:  # shell
            return self._execute_shell(code, timeout)

    def _execute_python(self, code: str, timeout: int) -> dict:
        """Execute Python code safely.

        Args:
            code: Python code to execute
            timeout: Timeout in seconds

        Returns:
            dict with execution result
        """
        # Check security first
        is_safe, error_msg = self._check_python_security(code)
        if not is_safe:
            return {
                "status": "security_violation",
                "language": "python",
                "code": code,
                "message": error_msg,
            }

        # Prepare execution environment
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        # Create safe namespace
        safe_builtins = {
            "print": print,
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "frozenset": frozenset,
            "range": range,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "sorted": sorted,
            "reversed": reversed,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "all": all,
            "any": any,
            "type": type,
            "isinstance": isinstance,
            "ord": ord,
            "chr": chr,
            "hex": hex,
            "oct": oct,
            "bin": bin,
            "ascii": ascii,
            "repr": repr,
            "format": format,
            "hash": hash,
            "id": id,
        }

        safe_namespace = {"__builtins__": safe_builtins}

        # Execute with timeout
        has_error = False
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec_with_timeout(code, safe_namespace, timeout)
        except TimeoutError:
            return {
                "status": "timeout",
                "language": "python",
                "code": code,
                "message": f"Code execution timed out after {timeout} seconds",
            }
        except Exception as e:
            stderr_capture.write(traceback.format_exc())
            has_error = True

        status = "error" if has_error else "ok"
        return {
            "status": status,
            "language": "python",
            "code": code,
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
        }

    def _execute_shell(self, code: str, timeout: int) -> dict:
        """Execute shell code safely.

        Args:
            code: Shell code to execute
            timeout: Timeout in seconds

        Returns:
            dict with execution result
        """
        # Check security first
        is_safe, error_msg = self._check_shell_security(code)
        if not is_safe:
            return {
                "status": "security_violation",
                "language": "shell",
                "code": code,
                "message": error_msg,
            }

        # Execute with timeout
        try:
            result = subprocess.run(
                code,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return {
                "status": "ok",
                "language": "shell",
                "code": code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "language": "shell",
                "code": code,
                "message": f"Code execution timed out after {timeout} seconds",
            }
        except Exception as e:
            return {
                "status": "error",
                "language": "shell",
                "code": code,
                "stderr": str(e),
                "message": f"Error executing shell code: {str(e)}",
            }

    def _check_python_security(self, code: str) -> Tuple[bool, str]:
        """Check Python code for security issues.

        Args:
            code: Python code to check

        Returns:
            Tuple of (is_safe, error_message)
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Syntax errors are ok, they'll be caught at execution
            return True, ""

        # Check for dangerous imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split(".")[0]
                    if module_name in self.BLOCKED_IMPORTS or module_name.startswith("_"):
                        return False, f"Import of '{module_name}' is not allowed"

            elif isinstance(node, ast.ImportFrom):
                module_name = (node.module or "").split(".")[0]
                if module_name in self.BLOCKED_IMPORTS or module_name.startswith("_"):
                    return False, f"Import from '{module_name}' is not allowed"

            elif isinstance(node, ast.Name):
                # Check for use of blocked builtins like open, eval, exec
                if node.id in self.BLOCKED_BUILTINS:
                    return False, f"Use of '{node.id}' builtin is not allowed"

            elif isinstance(node, ast.Call):
                # Check for __import__ calls
                if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                    return False, "Use of '__import__' is not allowed"

        return True, ""

    def _check_shell_security(self, code: str) -> Tuple[bool, str]:
        """Check shell code for security issues.

        Args:
            code: Shell code to check

        Returns:
            Tuple of (is_safe, error_message)
        """
        code_lower = code.lower()

        for pattern in self.BLOCKED_SHELL_PATTERNS:
            if pattern.lower() in code_lower:
                return False, f"Command pattern '{pattern.strip()}' is not allowed"

        return True, ""


def exec_with_timeout(code: str, namespace: dict, timeout: int) -> None:
    """Execute code with timeout using threading.

    Args:
        code: Code to execute
        namespace: Namespace for execution
        timeout: Timeout in seconds

    Raises:
        TimeoutError: If code execution exceeds timeout
    """
    result_container = {"exception": None}

    def run_code():
        try:
            exec(code, namespace)
        except Exception as e:
            result_container["exception"] = e

    thread = threading.Thread(target=run_code, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        # Thread is still running, we've timed out
        raise TimeoutError(f"Code execution timed out after {timeout} seconds")

    if result_container["exception"] is not None:
        raise result_container["exception"]

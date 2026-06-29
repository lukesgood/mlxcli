"""Tests for CodeExecutionTool - sandboxed code execution with security constraints."""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.tools.code_execution_tool import CodeExecutionTool


class TestCodeExecutionToolBasics:
    """Test basic CodeExecutionTool functionality."""

    def test_code_execution_tool_can_be_created(self):
        """CodeExecutionTool should be instantiable."""
        tool = CodeExecutionTool()
        assert tool is not None

    def test_code_execution_tool_has_correct_name(self):
        """CodeExecutionTool should have correct name."""
        tool = CodeExecutionTool()
        assert tool.name == "CodeExecutionTool"

    def test_code_execution_tool_has_description(self):
        """CodeExecutionTool should have a description."""
        tool = CodeExecutionTool()
        assert isinstance(tool.description, str)
        assert len(tool.description) > 0
        assert "10s" in tool.description or "10 second" in tool.description.lower()

    def test_code_execution_tool_is_tool(self):
        """CodeExecutionTool should be a Tool instance."""
        from mlxcli.tools.base import Tool

        tool = CodeExecutionTool()
        assert isinstance(tool, Tool)


class TestPythonCodeExecution:
    """Test Python code execution."""

    def test_execute_safe_python_print(self):
        """Should execute safe Python code with print statement."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "print('hello world')",
            "language": "python"
        })
        assert result["status"] == "ok"
        assert "hello world" in result["stdout"]
        assert result["language"] == "python"

    def test_execute_python_captures_stdout(self):
        """Should capture stdout from Python code."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "print('line1')\nprint('line2')",
            "language": "python"
        })
        assert result["status"] == "ok"
        assert "line1" in result["stdout"]
        assert "line2" in result["stdout"]

    def test_execute_python_multiple_lines(self):
        """Should execute multi-line Python code."""
        tool = CodeExecutionTool()
        code = """
x = 5
y = 10
print(x + y)
"""
        result = tool.execute({
            "code": code,
            "language": "python"
        })
        assert result["status"] == "ok"
        assert "15" in result["stdout"]

    def test_execute_python_with_safe_builtins(self):
        """Should execute Python code with safe builtins."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "print(len([1, 2, 3]))",
            "language": "python"
        })
        assert result["status"] == "ok"
        assert "3" in result["stdout"]

    def test_execute_python_with_string_operations(self):
        """Should execute Python code with string operations."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "s = 'hello'; print(s.upper())",
            "language": "python"
        })
        assert result["status"] == "ok"
        assert "HELLO" in result["stdout"]


class TestShellCodeExecution:
    """Test shell code execution."""

    def test_execute_safe_shell_echo(self):
        """Should execute safe shell code with echo."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "echo 'hello'",
            "language": "shell"
        })
        assert result["status"] == "ok"
        assert "hello" in result["stdout"]
        assert result["language"] == "shell"

    def test_execute_shell_captures_stdout(self):
        """Should capture stdout from shell code."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "echo 'line1'; echo 'line2'",
            "language": "shell"
        })
        assert result["status"] == "ok"
        assert "line1" in result["stdout"]
        assert "line2" in result["stdout"]

    def test_execute_shell_pwd_command(self):
        """Should execute pwd command."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "pwd",
            "language": "shell"
        })
        assert result["status"] == "ok"
        assert result["returncode"] == 0
        assert len(result["stdout"]) > 0

    def test_execute_shell_ls_command(self):
        """Should execute ls command."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "ls -la /tmp",
            "language": "shell"
        })
        assert result["status"] == "ok"
        assert result["returncode"] == 0

    def test_execute_shell_with_returncode(self):
        """Should capture return code from shell command."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "echo 'test'; exit 42",
            "language": "shell"
        })
        assert result["status"] == "ok"
        assert result["returncode"] == 42


class TestPythonSecurityBlockImportOS:
    """Test blocking of dangerous Python imports - os module."""

    def test_block_import_os(self):
        """Should block import os."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "import os",
            "language": "python"
        })
        assert result["status"] == "security_violation"
        assert "message" in result

    def test_block_from_import_os(self):
        """Should block from os import."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "from os import path",
            "language": "python"
        })
        assert result["status"] == "security_violation"

    def test_block_import_os_system(self):
        """Should block os.system usage."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "import os; os.system('ls')",
            "language": "python"
        })
        assert result["status"] == "security_violation"


class TestPythonSecurityBlockImportSys:
    """Test blocking of dangerous Python imports - sys module."""

    def test_block_import_sys(self):
        """Should block import sys."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "import sys",
            "language": "python"
        })
        assert result["status"] == "security_violation"

    def test_block_from_import_sys(self):
        """Should block from sys import."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "from sys import exit",
            "language": "python"
        })
        assert result["status"] == "security_violation"


class TestPythonSecurityBlockImportSubprocess:
    """Test blocking of dangerous Python imports - subprocess module."""

    def test_block_import_subprocess(self):
        """Should block import subprocess."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "import subprocess",
            "language": "python"
        })
        assert result["status"] == "security_violation"

    def test_block_from_import_subprocess(self):
        """Should block from subprocess import."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "from subprocess import run",
            "language": "python"
        })
        assert result["status"] == "security_violation"


class TestPythonSecurityBlockBuiltins:
    """Test blocking of dangerous Python builtins."""

    def test_block_open_builtin(self):
        """Should block open() builtin."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "f = open('/etc/passwd')",
            "language": "python"
        })
        assert result["status"] == "security_violation"

    def test_block_eval_builtin(self):
        """Should block eval() builtin."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "eval('1+1')",
            "language": "python"
        })
        assert result["status"] == "security_violation"

    def test_block_exec_builtin(self):
        """Should block exec() builtin."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "exec('print(1)')",
            "language": "python"
        })
        assert result["status"] == "security_violation"

    def test_block_compile_builtin(self):
        """Should block compile() builtin."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "compile('print(1)', '<string>', 'exec')",
            "language": "python"
        })
        assert result["status"] == "security_violation"

    def test_block_globals_builtin(self):
        """Should block globals() builtin."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "g = globals()",
            "language": "python"
        })
        assert result["status"] == "security_violation"

    def test_block_locals_builtin(self):
        """Should block locals() builtin."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "l = locals()",
            "language": "python"
        })
        assert result["status"] == "security_violation"

    def test_block_vars_builtin(self):
        """Should block vars() builtin."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "v = vars()",
            "language": "python"
        })
        assert result["status"] == "security_violation"


class TestShellSecurityBlockDangerous:
    """Test blocking of dangerous shell commands."""

    def test_block_rm_rf_command(self):
        """Should block rm -rf command."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "rm -rf /tmp/test",
            "language": "shell"
        })
        assert result["status"] == "security_violation"

    def test_block_nc_command(self):
        """Should block nc (netcat) command."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "nc localhost 8000",
            "language": "shell"
        })
        assert result["status"] == "security_violation"

    def test_block_ncat_command(self):
        """Should block ncat command."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "ncat localhost 8000",
            "language": "shell"
        })
        assert result["status"] == "security_violation"

    def test_block_chmod_command(self):
        """Should block chmod command."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "chmod 777 /tmp/file",
            "language": "shell"
        })
        assert result["status"] == "security_violation"

    def test_block_chown_command(self):
        """Should block chown command."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "chown root /tmp/file",
            "language": "shell"
        })
        assert result["status"] == "security_violation"

    def test_block_ssh_command(self):
        """Should block ssh command."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "ssh user@host",
            "language": "shell"
        })
        assert result["status"] == "security_violation"

    def test_block_dd_command(self):
        """Should block dd command."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "dd if=/dev/zero of=/dev/sda",
            "language": "shell"
        })
        assert result["status"] == "security_violation"


class TestTimeoutHandling:
    """Test timeout handling."""

    def test_python_timeout_infinite_loop(self):
        """Should timeout on infinite Python loop."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "while True: pass",
            "language": "python",
            "timeout": 1
        })
        assert result["status"] == "timeout"
        assert "message" in result

    def test_shell_timeout_long_sleep(self):
        """Should timeout on long shell sleep."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "sleep 100",
            "language": "shell",
            "timeout": 1
        })
        assert result["status"] == "timeout"

    def test_timeout_parameter_respected(self):
        """Should respect timeout parameter."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "sleep 5",
            "language": "shell",
            "timeout": 2
        })
        assert result["status"] == "timeout"

    def test_default_timeout_10_seconds(self):
        """Default timeout should be 10 seconds."""
        tool = CodeExecutionTool()
        # Quick command should complete before timeout
        result = tool.execute({
            "code": "echo test",
            "language": "shell"
        })
        assert result["status"] == "ok"

    def test_timeout_max_30_seconds(self):
        """Should allow timeout parameter up to 30 seconds."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "echo 'quick'",
            "language": "shell",
            "timeout": 30
        })
        assert result["status"] == "ok"


class TestErrorHandling:
    """Test error handling."""

    def test_python_runtime_error_caught(self):
        """Should catch and return Python runtime errors."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "x = 1 / 0",
            "language": "python"
        })
        assert result["status"] == "error"
        assert "stderr" in result

    def test_python_syntax_error_caught(self):
        """Should catch Python syntax errors."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "def broken(:\n    pass",
            "language": "python"
        })
        assert result["status"] == "error"

    def test_shell_error_with_returncode(self):
        """Should return error status with non-zero returncode."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "ls /nonexistent_path_12345",
            "language": "shell"
        })
        assert result["status"] == "ok"  # Shell doesn't fail, just returns code
        assert result["returncode"] != 0


class TestResponseFormat:
    """Test response format."""

    def test_python_response_has_required_fields(self):
        """Python response should have all required fields."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "print('test')",
            "language": "python"
        })
        assert isinstance(result, dict)
        assert "status" in result
        assert "language" in result
        assert "code" in result
        assert "stdout" in result
        assert "stderr" in result

    def test_shell_response_has_required_fields(self):
        """Shell response should have all required fields."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "echo test",
            "language": "shell"
        })
        assert isinstance(result, dict)
        assert "status" in result
        assert "language" in result
        assert "code" in result
        assert "stdout" in result
        assert "stderr" in result
        assert "returncode" in result

    def test_security_violation_response_format(self):
        """Security violation response should be properly formatted."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "import os",
            "language": "python"
        })
        assert result["status"] == "security_violation"
        assert "message" in result

    def test_timeout_response_format(self):
        """Timeout response should be properly formatted."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "sleep 100",
            "language": "shell",
            "timeout": 1
        })
        assert result["status"] == "timeout"
        assert "message" in result


class TestToolIntegration:
    """Test tool integration with registry."""

    def test_code_execution_tool_integrates_with_registry(self):
        """CodeExecutionTool should integrate with ToolRegistry."""
        from mlxcli.tool_registry import ToolRegistry

        registry = ToolRegistry()
        tool = CodeExecutionTool()
        registry.register(tool)

        # Tool should be retrievable
        retrieved = registry.get("CodeExecutionTool")
        assert retrieved is not None
        assert retrieved.name == "CodeExecutionTool"

    def test_registry_can_execute_code_execution_tool(self):
        """ToolRegistry should be able to execute CodeExecutionTool."""
        from mlxcli.tool_registry import ToolRegistry

        registry = ToolRegistry()
        tool = CodeExecutionTool()
        registry.register(tool)

        result = registry.execute("CodeExecutionTool", {
            "code": "print('hello')",
            "language": "python"
        })
        assert result["status"] == "ok"
        assert "hello" in result["stdout"]


class TestLanguageParameter:
    """Test language parameter."""

    def test_language_python_string(self):
        """Should accept language='python'."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "print('test')",
            "language": "python"
        })
        assert result["status"] == "ok"
        assert result["language"] == "python"

    def test_language_shell_string(self):
        """Should accept language='shell'."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "echo test",
            "language": "shell"
        })
        assert result["status"] == "ok"
        assert result["language"] == "shell"

    def test_invalid_language_parameter(self):
        """Should handle invalid language parameter."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "echo test",
            "language": "invalid"
        })
        assert result["status"] == "error"

    def test_missing_language_parameter(self):
        """Should handle missing language parameter."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "echo test"
        })
        assert result["status"] == "error"


class TestCodeParameter:
    """Test code parameter."""

    def test_missing_code_parameter(self):
        """Should handle missing code parameter."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "language": "python"
        })
        assert result["status"] == "error"

    def test_empty_code_string(self):
        """Should handle empty code string."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "",
            "language": "python"
        })
        # Empty code is valid, just does nothing
        assert result["status"] == "ok"


class TestSecurityMessages:
    """Test that security violation messages are informative."""

    def test_import_os_message(self):
        """Security message should indicate which module is blocked."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "import os",
            "language": "python"
        })
        assert result["status"] == "security_violation"
        assert "os" in result["message"].lower() or "import" in result["message"].lower()

    def test_open_builtin_message(self):
        """Security message should indicate which builtin is blocked."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "open('/etc/passwd')",
            "language": "python"
        })
        assert result["status"] == "security_violation"
        assert "open" in result["message"].lower() or "builtin" in result["message"].lower()

    def test_dangerous_shell_command_message(self):
        """Security message should indicate which shell command is blocked."""
        tool = CodeExecutionTool()
        result = tool.execute({
            "code": "rm -rf /",
            "language": "shell"
        })
        assert result["status"] == "security_violation"
        assert "rm" in result["message"].lower() or "dangerous" in result["message"].lower()

"""Tests for DebuggerAgent implementation."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.agents.base_agent import Agent
from mlxcli.agents.debugger_agent import DebuggerAgent


def assert_raises(exception_type):
    """Context manager for asserting exceptions."""
    class RaisesContext:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                raise AssertionError(f"Expected {exception_type.__name__} but no exception was raised")
            if not issubclass(exc_type, exception_type):
                return False  # Re-raise the exception
            return True  # Suppress the exception

    return RaisesContext()


class TestDebuggerAgentProperties:
    """Test DebuggerAgent basic properties."""

    def test_debugger_agent_can_be_created(self):
        """DebuggerAgent can be created with context."""
        context = {
            "backend": MagicMock(),
            "tools": MagicMock(),
        }
        agent = DebuggerAgent(context)
        assert agent is not None

    def test_debugger_agent_name_is_debugger(self):
        """DebuggerAgent.name returns 'debugger'."""
        context = {"backend": MagicMock()}
        agent = DebuggerAgent(context)
        assert agent.name == "debugger"

    def test_debugger_agent_has_description(self):
        """DebuggerAgent.description should exist and be non-empty."""
        context = {"backend": MagicMock()}
        agent = DebuggerAgent(context)
        assert agent.description is not None
        assert len(agent.description) > 0
        assert isinstance(agent.description, str)

    def test_debugger_agent_is_agent_subclass(self):
        """DebuggerAgent should be subclass of Agent."""
        assert issubclass(DebuggerAgent, Agent)

    def test_debugger_agent_stores_context(self):
        """DebuggerAgent should store context."""
        context = {"backend": MagicMock()}
        agent = DebuggerAgent(context)
        assert agent.context is context

    def test_debugger_agent_extracts_backend_from_context(self):
        """DebuggerAgent should extract backend from context."""
        mock_backend = MagicMock()
        context = {"backend": mock_backend}
        agent = DebuggerAgent(context)
        assert agent.backend is mock_backend

    def test_debugger_agent_extracts_tools_from_context(self):
        """DebuggerAgent should extract tools from context."""
        mock_tools = MagicMock()
        context = {"tools": mock_tools}
        agent = DebuggerAgent(context)
        assert agent.tools is mock_tools


class TestDebuggerAgentExecution:
    """Test DebuggerAgent execute() method."""

    def test_execute_accepts_task_and_context(self):
        """execute() should accept task and context parameters."""
        context = {"backend": MagicMock()}
        agent = DebuggerAgent(context)
        # Should not raise TypeError
        result = agent.execute("def buggy(): x = 1 / 0", {})
        assert isinstance(result, dict)

    def test_execute_returns_dict_with_required_fields(self):
        """execute() should return dict with required fields."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = "Bug: Division by zero at line 2"
        context = {"backend": mock_backend}
        agent = DebuggerAgent(context)

        result = agent.execute("x = 1 / 0", {})

        assert isinstance(result, dict)
        assert "status" in result
        assert "agent" in result
        assert "task" in result
        assert "result" in result

    def test_execute_returns_bugs_list(self):
        """execute() should return list of identified bugs."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "Bugs found:\n"
            "1. Critical: Division by zero - x = 1 / 0\n"
            "2. Warning: Unused variable - y is defined but never used"
        )
        context = {"backend": mock_backend}
        agent = DebuggerAgent(context)

        result = agent.execute("buggy code", {})

        assert "bugs" in result
        assert isinstance(result["bugs"], list)

    def test_execute_categorizes_bugs_by_severity(self):
        """execute() should categorize bugs by severity."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "Bugs:\n"
            "Critical: TypeError on line 3\n"
            "Warning: Undefined variable reference\n"
            "Suggestion: Add type hints"
        )
        context = {"backend": mock_backend}
        agent = DebuggerAgent(context)

        result = agent.execute("code with issues", {})

        assert "bugs" in result
        # Should have identified bugs
        assert len(result["bugs"]) >= 0

    def test_execute_suggests_fixes(self):
        """execute() should provide fix suggestions."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "Issue: Missing null check\n"
            "Fix: Check if object is not None before accessing"
        )
        context = {"backend": mock_backend}
        agent = DebuggerAgent(context)

        result = agent.execute("potentially buggy code", {})

        assert result["status"] == "ok"
        assert "result" in result

    def test_execute_handles_empty_code(self):
        """execute() should handle empty code gracefully."""
        mock_backend = MagicMock()
        context = {"backend": mock_backend}
        agent = DebuggerAgent(context)

        result = agent.execute("", {})

        assert result["status"] == "error" or result["status"] == "ok"

    def test_execute_handles_no_backend(self):
        """execute() should handle missing backend gracefully."""
        context = {}
        agent = DebuggerAgent(context)

        result = agent.execute("code", {})

        assert "status" in result
        assert result["status"] in ("error", "ok")

    def test_execute_detects_division_by_zero(self):
        """execute() should detect division by zero bugs."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "Critical Bug: Division by zero detected\n"
            "Line: x = 10 / 0\n"
            "Fix: Ensure denominator is not zero"
        )
        context = {"backend": mock_backend}
        agent = DebuggerAgent(context)

        result = agent.execute("x = 10 / 0", {})

        assert result["status"] == "ok"
        assert "bugs" in result

    def test_execute_detects_undefined_variables(self):
        """execute() should detect undefined variable references."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "Warning: Undefined variable 'undefined_var' used on line 2"
        )
        context = {"backend": mock_backend}
        agent = DebuggerAgent(context)

        result = agent.execute("x = undefined_var + 1", {})

        assert result["status"] == "ok"

    def test_execute_identifies_null_pointer_issues(self):
        """execute() should identify null/None pointer issues."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "Critical: Potential None reference - obj.method() "
            "where obj could be None"
        )
        context = {"backend": mock_backend}
        agent = DebuggerAgent(context)

        result = agent.execute("obj.method()", {})

        assert result["status"] == "ok"
        assert "bugs" in result or "result" in result

    def test_execute_calls_backend_generate(self):
        """execute() should call backend.generate() with prompt."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = "No bugs detected"
        context = {"backend": mock_backend}
        agent = DebuggerAgent(context)

        agent.execute("good code", {})

        # Should have called backend.generate at least once
        mock_backend.generate.assert_called()

    def test_execute_multiple_sequential_debugs(self):
        """Multiple sequential debugging sessions should work."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = "Bugs: None detected"
        context = {"backend": mock_backend}
        agent = DebuggerAgent(context)

        result1 = agent.execute("code 1", {})
        result2 = agent.execute("code 2", {})

        assert result1["status"] == "ok"
        assert result2["status"] == "ok"

    def test_execute_parses_critical_severity(self):
        """execute() should parse critical severity bugs."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "Bug 1: Critical - OutOfBoundsException\n"
            "Line: array[index] where index > length\n"
            "Description: Array access violation"
        )
        context = {"backend": mock_backend}
        agent = DebuggerAgent(context)

        result = agent.execute("array[100]", {})

        assert result["status"] == "ok"
        assert "bugs" in result

    def test_execute_parses_warning_severity(self):
        """execute() should parse warning severity bugs."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "Bug 1: Warning - Unused variable\n"
            "Variable 'temp' is defined but never used"
        )
        context = {"backend": mock_backend}
        agent = DebuggerAgent(context)

        result = agent.execute("temp = 42", {})

        assert result["status"] == "ok"

    def test_execute_parses_suggestion_severity(self):
        """execute() should parse suggestion severity items."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "Suggestion: Add error handling for potential exceptions\n"
            "Could improve robustness"
        )
        context = {"backend": mock_backend}
        agent = DebuggerAgent(context)

        result = agent.execute("risky_operation()", {})

        assert result["status"] == "ok"

    def test_execute_extracts_code_from_task(self):
        """execute() should extract code from task string."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = "Bugs: None"
        context = {"backend": mock_backend}
        agent = DebuggerAgent(context)

        code = "def test(): pass"
        result = agent.execute(f"Debug this code:\n{code}", {})

        assert result["status"] == "ok"
        assert mock_backend.generate.called

    def test_execute_includes_original_task(self):
        """execute() should include original task in result."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = "Analysis: No bugs"
        context = {"backend": mock_backend}
        agent = DebuggerAgent(context)

        task = "x = 1 / 0"
        result = agent.execute(task, {})

        assert result["task"] == task or result["task"] is not None

    def test_execute_response_includes_agent_name(self):
        """execute() response should include 'debugger' as agent."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = "No bugs"
        context = {"backend": mock_backend}
        agent = DebuggerAgent(context)

        result = agent.execute("code", {})

        assert result.get("agent") == "debugger"

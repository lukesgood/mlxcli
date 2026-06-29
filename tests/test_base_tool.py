"""Tests for abstract Tool base class."""

import pytest
from abc import ABC, abstractmethod
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.tools.base import Tool


class TestToolIsAbstractBase:
    """Test that Tool is an abstract base class."""

    def test_tool_is_abstract_base_class(self):
        """Tool should be an ABC (abstract base class)."""
        assert issubclass(Tool, ABC), "Tool should inherit from ABC"

    def test_cannot_instantiate_tool_directly(self):
        """Should not be able to instantiate Tool directly."""
        with pytest.raises(TypeError, match="abstract"):
            Tool()


class TestToolRequiredProperties:
    """Test that Tool requires implementing name and description properties."""

    def test_tool_requires_name_property(self):
        """Tool should require implementing name property."""
        with pytest.raises(TypeError):
            class IncompleteToolNoName(Tool):
                @property
                def description(self) -> str:
                    return "A tool"

                def execute(self, args: dict) -> dict:
                    return {"status": "ok"}

            IncompleteToolNoName()

    def test_tool_requires_description_property(self):
        """Tool should require implementing description property."""
        with pytest.raises(TypeError):
            class IncompleteToolNoDescription(Tool):
                @property
                def name(self) -> str:
                    return "test_tool"

                def execute(self, args: dict) -> dict:
                    return {"status": "ok"}

            IncompleteToolNoDescription()


class TestToolRequiredMethods:
    """Test that Tool requires implementing execute method."""

    def test_tool_requires_execute_method(self):
        """Tool should require implementing execute method."""
        with pytest.raises(TypeError):
            class IncompleteToolNoExecute(Tool):
                @property
                def name(self) -> str:
                    return "test_tool"

                @property
                def description(self) -> str:
                    return "A test tool"

            IncompleteToolNoExecute()


class TestConcreteToolImplementation:
    """Test that a concrete Tool implementation can be created."""

    def test_can_create_concrete_tool(self):
        """Should be able to create a concrete Tool implementation."""
        class SimpleTool(Tool):
            @property
            def name(self) -> str:
                return "simple_tool"

            @property
            def description(self) -> str:
                return "A simple test tool"

            def execute(self, args: dict) -> dict:
                return {"status": "ok"}

        tool = SimpleTool()
        assert tool is not None
        assert isinstance(tool, Tool)

    def test_concrete_tool_has_name_property(self):
        """Concrete tool should have accessible name property."""
        class SimpleTool(Tool):
            @property
            def name(self) -> str:
                return "simple_tool"

            @property
            def description(self) -> str:
                return "A simple test tool"

            def execute(self, args: dict) -> dict:
                return {"status": "ok"}

        tool = SimpleTool()
        assert tool.name == "simple_tool"
        assert isinstance(tool.name, str)

    def test_concrete_tool_has_description_property(self):
        """Concrete tool should have accessible description property."""
        class SimpleTool(Tool):
            @property
            def name(self) -> str:
                return "simple_tool"

            @property
            def description(self) -> str:
                return "A simple test tool"

            def execute(self, args: dict) -> dict:
                return {"status": "ok"}

        tool = SimpleTool()
        assert tool.description == "A simple test tool"
        assert isinstance(tool.description, str)


class TestConcreteToolExecute:
    """Test that execute method works on concrete implementations."""

    def test_concrete_tool_execute_works(self):
        """Concrete tool execute should work and return dict with status."""
        class SimpleTool(Tool):
            @property
            def name(self) -> str:
                return "simple_tool"

            @property
            def description(self) -> str:
                return "A simple test tool"

            def execute(self, args: dict) -> dict:
                return {"status": "ok"}

        tool = SimpleTool()
        result = tool.execute({})
        assert isinstance(result, dict), "execute should return dict"
        assert "status" in result, "result should have 'status' key"
        assert result["status"] == "ok"

    def test_concrete_tool_execute_with_arguments(self):
        """Concrete tool execute should receive and process arguments."""
        class EchoTool(Tool):
            @property
            def name(self) -> str:
                return "echo_tool"

            @property
            def description(self) -> str:
                return "Echo the input message"

            def execute(self, args: dict) -> dict:
                message = args.get("message", "")
                return {"status": "ok", "message": message}

        tool = EchoTool()
        result = tool.execute({"message": "hello"})
        assert result["status"] == "ok"
        assert result["message"] == "hello"

    def test_concrete_tool_execute_error_status(self):
        """Concrete tool execute can return error status."""
        class ErrorTool(Tool):
            @property
            def name(self) -> str:
                return "error_tool"

            @property
            def description(self) -> str:
                return "A tool that returns errors"

            def execute(self, args: dict) -> dict:
                return {"status": "error", "error": "Something went wrong"}

        tool = ErrorTool()
        result = tool.execute({})
        assert result["status"] == "error"
        assert "error" in result


class TestMultipleToolImplementations:
    """Test multiple Tool implementations to ensure interface is flexible."""

    def test_two_different_tool_implementations(self):
        """Should be able to create multiple different Tool implementations."""
        class Tool1(Tool):
            @property
            def name(self) -> str:
                return "tool_1"

            @property
            def description(self) -> str:
                return "First tool"

            def execute(self, args: dict) -> dict:
                return {"status": "ok", "tool": 1}

        class Tool2(Tool):
            @property
            def name(self) -> str:
                return "tool_2"

            @property
            def description(self) -> str:
                return "Second tool"

            def execute(self, args: dict) -> dict:
                return {"status": "ok", "tool": 2}

        t1 = Tool1()
        t2 = Tool2()

        assert t1.name == "tool_1"
        assert t2.name == "tool_2"
        assert t1.execute({})["tool"] == 1
        assert t2.execute({})["tool"] == 2

    def test_tool_implementation_with_state(self):
        """Tool implementation can maintain state."""
        class StatefulTool(Tool):
            def __init__(self):
                self._call_count = 0

            @property
            def name(self) -> str:
                return "stateful_tool"

            @property
            def description(self) -> str:
                return "Tool that maintains state"

            def execute(self, args: dict) -> dict:
                self._call_count += 1
                return {"status": "ok", "call_count": self._call_count}

        tool = StatefulTool()
        result1 = tool.execute({})
        result2 = tool.execute({})
        result3 = tool.execute({})

        assert result1["call_count"] == 1
        assert result2["call_count"] == 2
        assert result3["call_count"] == 3

    def test_tool_implementation_with_initialization(self):
        """Tool implementation can have custom initialization."""
        class ConfigurableTool(Tool):
            def __init__(self, prefix: str = "tool"):
                self._prefix = prefix

            @property
            def name(self) -> str:
                return f"{self._prefix}_name"

            @property
            def description(self) -> str:
                return f"{self._prefix} tool"

            def execute(self, args: dict) -> dict:
                return {"status": "ok", "prefix": self._prefix}

        tool_a = ConfigurableTool("alpha")
        tool_b = ConfigurableTool("beta")

        assert tool_a.name == "alpha_name"
        assert tool_b.name == "beta_name"
        assert tool_a.execute({})["prefix"] == "alpha"
        assert tool_b.execute({})["prefix"] == "beta"


class TestToolInterface:
    """Test the Tool interface properties and contracts."""

    def test_name_is_property_not_method(self):
        """name should be a property, not a method."""
        class TestTool(Tool):
            @property
            def name(self) -> str:
                return "test"

            @property
            def description(self) -> str:
                return "test"

            def execute(self, args: dict) -> dict:
                return {"status": "ok"}

        tool = TestTool()
        # Should be accessible without calling as method
        assert isinstance(tool.name, str)

    def test_description_is_property_not_method(self):
        """description should be a property, not a method."""
        class TestTool(Tool):
            @property
            def name(self) -> str:
                return "test"

            @property
            def description(self) -> str:
                return "test"

            def execute(self, args: dict) -> dict:
                return {"status": "ok"}

        tool = TestTool()
        # Should be accessible without calling as method
        assert isinstance(tool.description, str)

    def test_execute_takes_dict_argument(self):
        """execute should accept dict argument."""
        class TestTool(Tool):
            @property
            def name(self) -> str:
                return "test"

            @property
            def description(self) -> str:
                return "test"

            def execute(self, args: dict) -> dict:
                return {"status": "ok", "received": type(args).__name__}

        tool = TestTool()
        result = tool.execute({})
        assert result["received"] == "dict"

    def test_execute_returns_dict(self):
        """execute should return dict."""
        class TestTool(Tool):
            @property
            def name(self) -> str:
                return "test"

            @property
            def description(self) -> str:
                return "test"

            def execute(self, args: dict) -> dict:
                return {"status": "ok"}

        tool = TestTool()
        result = tool.execute({})
        assert isinstance(result, dict)

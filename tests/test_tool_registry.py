"""Tests for ToolRegistry - central tool registration and dispatch system."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.tool_registry import ToolRegistry
from mlxcli.tools.base import Tool


class SimpleTool(Tool):
    """Simple test tool implementation."""

    def __init__(
        self, name: str = "simple_tool", description: str = "A simple test tool"
    ):
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def execute(self, args: dict) -> dict:
        return {"status": "ok", "message": "Tool executed"}


class ErrorTool(Tool):
    """Tool that raises an exception when executed."""

    @property
    def name(self) -> str:
        return "error_tool"

    @property
    def description(self) -> str:
        return "A tool that raises exceptions"

    def execute(self, args: dict) -> dict:
        raise ValueError("Tool execution failed")


class TestToolRegistryRegistration:
    """Test tool registration functionality."""

    def test_can_register_tool(self):
        """Should be able to register a tool."""
        registry = ToolRegistry()
        tool = SimpleTool()
        registry.register(tool)
        # Should not raise

    def test_can_register_and_retrieve_tool(self):
        """Should be able to register and retrieve a tool."""
        registry = ToolRegistry()
        tool = SimpleTool("my_tool", "My test tool")
        registry.register(tool)

        retrieved = registry.get("my_tool")
        assert retrieved is not None
        assert retrieved is tool
        assert retrieved.name == "my_tool"
        assert retrieved.description == "My test tool"

    def test_get_returns_none_for_nonexistent_tool(self):
        """get() should return None for non-existent tool."""
        registry = ToolRegistry()
        result = registry.get("nonexistent")
        assert result is None

    def test_can_register_multiple_different_tools(self):
        """Should be able to register multiple different tools."""
        registry = ToolRegistry()
        tool1 = SimpleTool("tool_1", "First tool")
        tool2 = SimpleTool("tool_2", "Second tool")
        tool3 = SimpleTool("tool_3", "Third tool")

        registry.register(tool1)
        registry.register(tool2)
        registry.register(tool3)

        assert registry.get("tool_1") is tool1
        assert registry.get("tool_2") is tool2
        assert registry.get("tool_3") is tool3

    def test_duplicate_registration_overwrites(self):
        """Registering a tool with same name should overwrite previous one."""
        registry = ToolRegistry()
        tool1 = SimpleTool("my_tool", "First version")
        tool2 = SimpleTool("my_tool", "Second version")

        registry.register(tool1)
        registry.register(tool2)

        retrieved = registry.get("my_tool")
        assert retrieved is tool2
        assert retrieved.description == "Second version"

    def test_tool_names_are_case_sensitive(self):
        """Tool names should be case-sensitive."""
        registry = ToolRegistry()
        tool_lower = SimpleTool("mytool", "Lower case")
        tool_upper = SimpleTool("MyTool", "Upper case")

        registry.register(tool_lower)
        registry.register(tool_upper)

        assert registry.get("mytool") is tool_lower
        assert registry.get("MyTool") is tool_upper
        assert registry.get("mytool") is not tool_upper


class TestToolRegistryExecution:
    """Test tool execution through registry."""

    def test_can_execute_registered_tool_with_args(self):
        """Should be able to execute a registered tool with arguments."""
        registry = ToolRegistry()
        tool = SimpleTool()
        registry.register(tool)

        result = registry.execute("simple_tool", {"key": "value"})
        assert result is not None
        assert isinstance(result, dict)
        assert result["status"] == "ok"

    def test_execute_returns_tool_result_dict(self):
        """execute() should return the tool's result dict."""
        registry = ToolRegistry()

        class CustomResultTool(Tool):
            @property
            def name(self) -> str:
                return "custom_tool"

            @property
            def description(self) -> str:
                return "Custom result tool"

            def execute(self, args: dict) -> dict:
                return {
                    "status": "ok",
                    "result": "custom_result",
                    "custom_field": args.get("custom_key"),
                }

        registry.register(CustomResultTool())
        result = registry.execute("custom_tool", {"custom_key": "custom_value"})

        assert result["status"] == "ok"
        assert result["result"] == "custom_result"
        assert result["custom_field"] == "custom_value"

    def test_execute_nonexistent_tool_returns_error_dict(self):
        """execute() on non-existent tool should return error dict."""
        registry = ToolRegistry()
        result = registry.execute("nonexistent", {})

        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert "message" in result
        assert "nonexistent" in result["message"]
        assert "not found" in result["message"].lower()

    def test_execute_catches_tool_exceptions(self):
        """execute() should catch tool exceptions and return error dict."""
        registry = ToolRegistry()
        registry.register(ErrorTool())

        result = registry.execute("error_tool", {})

        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert "message" in result
        assert (
            "failed" in result["message"].lower()
            or "execution" in result["message"].lower()
        )

    def test_execute_passes_args_to_tool(self):
        """execute() should pass args dict to tool's execute method."""
        registry = ToolRegistry()

        class ArgEchoTool(Tool):
            @property
            def name(self) -> str:
                return "echo_tool"

            @property
            def description(self) -> str:
                return "Echo tool"

            def execute(self, args: dict) -> dict:
                return {"status": "ok", "received_args": args}

        registry.register(ArgEchoTool())
        test_args = {"key1": "value1", "key2": "value2"}
        result = registry.execute("echo_tool", test_args)

        assert result["received_args"] == test_args

    def test_execute_with_empty_args(self):
        """execute() should work with empty args dict."""
        registry = ToolRegistry()
        registry.register(SimpleTool())

        result = registry.execute("simple_tool", {})
        assert result["status"] == "ok"

    def test_execute_error_message_format(self):
        """execute() error message should include tool name and reason."""
        registry = ToolRegistry()
        result = registry.execute("missing_tool", {})

        assert "missing_tool" in result["message"]


class TestToolRegistryListing:
    """Test listing tools in registry."""

    def test_list_tools_empty_registry(self):
        """list_tools() should return empty list for empty registry."""
        registry = ToolRegistry()
        tools = registry.list_tools()

        assert isinstance(tools, list)
        assert len(tools) == 0

    def test_list_tools_returns_sorted_names(self):
        """list_tools() should return sorted list of tool names."""
        registry = ToolRegistry()
        registry.register(SimpleTool("zebra", "Z tool"))
        registry.register(SimpleTool("alpha", "A tool"))
        registry.register(SimpleTool("beta", "B tool"))

        tools = registry.list_tools()

        assert tools == ["alpha", "beta", "zebra"]

    def test_list_tools_single_tool(self):
        """list_tools() should work with single tool."""
        registry = ToolRegistry()
        registry.register(SimpleTool("only_tool", "The only tool"))

        tools = registry.list_tools()
        assert tools == ["only_tool"]

    def test_list_tools_returns_names_not_objects(self):
        """list_tools() should return names (strings), not tool objects."""
        registry = ToolRegistry()
        registry.register(SimpleTool("tool1", "Tool 1"))
        registry.register(SimpleTool("tool2", "Tool 2"))

        tools = registry.list_tools()
        assert all(isinstance(t, str) for t in tools)


class TestToolRegistryDescriptions:
    """Test getting tool descriptions for LLM."""

    def test_get_tools_description_empty_registry(self):
        """get_tools_description() should handle empty registry."""
        registry = ToolRegistry()
        description = registry.get_tools_description()

        assert isinstance(description, str)

    def test_get_tools_description_includes_tool_names(self):
        """get_tools_description() should include all tool names."""
        registry = ToolRegistry()
        registry.register(SimpleTool("calculator", "Math tool"))
        registry.register(SimpleTool("file_reader", "Read files"))

        description = registry.get_tools_description()

        assert "calculator" in description
        assert "file_reader" in description

    def test_get_tools_description_includes_descriptions(self):
        """get_tools_description() should include all tool descriptions."""
        registry = ToolRegistry()
        registry.register(SimpleTool("tool1", "This is tool one"))
        registry.register(SimpleTool("tool2", "This is tool two"))

        description = registry.get_tools_description()

        assert "This is tool one" in description
        assert "This is tool two" in description

    def test_get_tools_description_formatted_for_llm(self):
        """get_tools_description() should be formatted for LLM consumption."""
        registry = ToolRegistry()
        registry.register(SimpleTool("test_tool", "Test description"))

        description = registry.get_tools_description()

        # Should be a formatted string, readable by LLM
        assert isinstance(description, str)
        assert len(description) > 0

    def test_get_tools_description_single_tool(self):
        """get_tools_description() should work with single tool."""
        registry = ToolRegistry()
        registry.register(SimpleTool("only", "Only tool"))

        description = registry.get_tools_description()

        assert "only" in description
        assert "Only tool" in description

    def test_get_tools_description_multiple_tools_readable(self):
        """get_tools_description() output should be readable with multiple tools."""
        registry = ToolRegistry()
        registry.register(SimpleTool("tool1", "First tool"))
        registry.register(SimpleTool("tool2", "Second tool"))
        registry.register(SimpleTool("tool3", "Third tool"))

        description = registry.get_tools_description()

        # All tools should be present
        assert "tool1" in description
        assert "tool2" in description
        assert "tool3" in description
        assert "First tool" in description
        assert "Second tool" in description
        assert "Third tool" in description
        # Should have some structure
        assert len(description) > 20

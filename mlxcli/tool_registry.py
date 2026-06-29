"""ToolRegistry - central tool registration and dispatch system."""

from typing import Optional, Dict
from mlxcli.tools.base import Tool


class ToolRegistry:
    """Central registry for tools with registration and dispatch capabilities.

    Manages tool registration, retrieval, and execution with error handling.
    Tools are registered by their unique name and can be executed through
    the registry with automatic error handling and formatting.

    Attributes:
        _tools: Dictionary mapping tool names to Tool instances.
    """

    def __init__(self):
        """Initialize an empty tool registry."""
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool in the registry.

        Tools are indexed by their name property. If a tool with the same
        name is already registered, it will be overwritten.

        Args:
            tool: Tool instance to register. Must implement the Tool interface.

        Raises:
            None - silently overwrites existing registrations.
        """
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """Retrieve a tool by name.

        Args:
            name: The name of the tool to retrieve. Names are case-sensitive.

        Returns:
            Tool instance if found, None otherwise.
        """
        return self._tools.get(name)

    def execute(self, tool_name: str, args: dict) -> dict:
        """Execute a registered tool with error handling.

        Looks up the tool by name and executes it with the provided arguments.
        Handles errors gracefully with a standard error response format.

        Args:
            tool_name: Name of the tool to execute. Case-sensitive.
            args: Dictionary of arguments to pass to the tool.

        Returns:
            dict: The tool's result dictionary on success:
                - Contains all keys returned by tool.execute()
                - Should include "status" key (usually "ok" or "error")

              On error returns dict with:
                - "status": "error"
                - "message": Error description including tool name and reason
        """
        tool = self.get(tool_name)

        if tool is None:
            return {
                "status": "error",
                "message": f"Tool not found: {tool_name}",
            }

        try:
            return tool.execute(args)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Tool execution failed: {str(e)}",
            }

    def list_tools(self) -> list[str]:
        """Get a sorted list of all registered tool names.

        Returns:
            list[str]: Alphabetically sorted list of tool names.
                      Returns empty list if no tools are registered.
        """
        return sorted(self._tools.keys())

    def get_tools_description(self) -> str:
        """Get formatted descriptions of all registered tools for LLM.

        Generates a human-readable description of all available tools,
        suitable for providing to an LLM to understand what tools are
        available and what they do.

        Returns:
            str: Formatted description string. For empty registry, returns
                 an empty string or placeholder message.
        """
        if not self._tools:
            return ""

        lines = []
        for tool_name in self.list_tools():
            tool = self._tools[tool_name]
            lines.append(f"- {tool_name}: {tool.description}")

        return "\n".join(lines)

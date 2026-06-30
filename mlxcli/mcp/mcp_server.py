"""MCP Server integration for external tool discovery and registration.

Implements the MCPServer class that discovers and registers MCP-compatible
external tools with the central tool registry system.
"""

from typing import Callable, Dict, Optional

from mlxcli.tool_registry import ToolRegistry
from mlxcli.tools.base import Tool


class MCPTool(Tool):
    """Wrapper for MCP tools to implement Tool interface."""

    def __init__(self, name: str, description: str, execute_fn: Callable):
        """Initialize MCPTool wrapper.

        Args:
            name: str - Tool name/identifier
            description: str - Human-readable description for LLM
            execute_fn: Callable - Function to execute the tool
        """
        self._name = name
        self._description = description
        self._execute_fn = execute_fn

    @property
    def name(self) -> str:
        """Tool name.

        Returns:
            str: Tool name/identifier
        """
        return self._name

    @property
    def description(self) -> str:
        """Tool description for LLM.

        Returns:
            str: Human-readable description
        """
        return self._description

    def execute(self, args: dict) -> dict:
        """Execute the MCP tool.

        Args:
            args: dict - Arguments to pass to the tool

        Returns:
            dict: Result with status and output
        """
        try:
            result = self._execute_fn(args)
            if isinstance(result, dict):
                # Ensure status field exists
                if "status" not in result:
                    result["status"] = "ok"
                return result
            else:
                # Wrap non-dict results
                return {
                    "status": "ok",
                    "result": result,
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"MCP tool execution failed: {str(e)}",
            }


class MCPServer:
    """MCP (Model Context Protocol) integration server.

    Manages MCP-compatible tools, handles discovery and registration
    with the central tool registry for integration with agents and
    workflow engine.

    Attributes:
        tool_registry: ToolRegistry - Central registry for tools
        mcp_tools: dict - Dictionary of registered MCP tools
    """

    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        """Initialize MCPServer.

        Args:
            tool_registry: Optional[ToolRegistry] - Central tool registry
                          (optional; tools can be discovered without it)
        """
        self.tool_registry = tool_registry
        self.mcp_tools: Dict[str, dict] = {}

    def discover_tools(self) -> list[str]:
        """Discover available MCP tools.

        Currently returns manually registered tools. In future versions,
        this could perform auto-discovery from external MCP sources.

        Returns:
            list[str]: Sorted list of available MCP tool names
        """
        return sorted(self.mcp_tools.keys())

    def register_mcp_tool(
        self, name: str, description: str, execute_fn: Callable
    ) -> bool:
        """Register an MCP tool with the server.

        Registers a new MCP tool and optionally integrates it with the
        tool registry if one is available. The tool becomes immediately
        available for discovery and execution.

        Args:
            name: str - Tool name/identifier (should be unique)
            description: str - Human-readable description for LLM
            execute_fn: Callable - Function that executes the tool.
                       Should accept dict args and return dict result

        Returns:
            bool: True if registration successful, False otherwise
        """
        try:
            # Create MCP tool wrapper
            mcp_tool = {
                "name": name,
                "description": description,
                "execute": execute_fn,
            }

            # Store in MCP tools registry
            self.mcp_tools[name] = mcp_tool

            # Register with tool registry if available
            if self.tool_registry:
                tool_wrapper = MCPTool(name, description, execute_fn)
                self._register_with_registry(tool_wrapper)

            return True
        except Exception:
            return False

    def _register_with_registry(self, tool: Tool) -> bool:
        """Register MCP tool with ToolRegistry.

        Internal method to wrap MCP tool in Tool interface and register
        with the central tool registry.

        Args:
            tool: Tool - Tool wrapper implementing Tool interface

        Returns:
            bool: True if registration successful, False otherwise
        """
        try:
            if self.tool_registry:
                self.tool_registry.register(tool)
                return True
            return False
        except Exception:
            return False

    def get_tool(self, name: str) -> Optional[dict]:
        """Get MCP tool metadata by name.

        Retrieves tool metadata (name, description, execute function)
        for a registered MCP tool.

        Args:
            name: str - Tool name to retrieve

        Returns:
            Optional[dict]: Tool metadata dict if found, None otherwise
        """
        return self.mcp_tools.get(name)

    def execute_tool(self, name: str, args: dict) -> dict:
        """Execute an MCP tool directly.

        Executes a registered MCP tool with provided arguments.
        Returns error dict if tool not found or execution fails.

        Args:
            name: str - Tool name to execute
            args: dict - Arguments to pass to tool

        Returns:
            dict: Result dict with status and output/error info
        """
        tool_info = self.get_tool(name)

        if tool_info is None:
            return {
                "status": "error",
                "message": f"MCP tool not found: {name}",
            }

        try:
            execute_fn = tool_info["execute"]
            result = execute_fn(args)

            # Ensure result is dict with status
            if isinstance(result, dict):
                if "status" not in result:
                    result["status"] = "ok"
                return result
            else:
                return {
                    "status": "ok",
                    "result": result,
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Tool execution failed: {str(e)}",
            }

    def list_tools_info(self) -> list[dict]:
        """Get detailed information about all registered tools.

        Returns metadata for all MCP tools suitable for display
        or serialization.

        Returns:
            list[dict]: List of tool metadata dicts with keys:
                       - name: Tool name
                       - description: Tool description
        """
        return [
            {
                "name": tool_info["name"],
                "description": tool_info["description"],
            }
            for tool_info in self.mcp_tools.values()
        ]

    def unregister_tool(self, name: str) -> bool:
        """Unregister an MCP tool.

        Removes a tool from the MCP server registry. If the tool was
        registered with the central tool registry, that registration
        is NOT automatically removed (would require tool registry
        support for removal).

        Args:
            name: str - Tool name to unregister

        Returns:
            bool: True if tool was unregistered, False if not found
        """
        if name in self.mcp_tools:
            del self.mcp_tools[name]
            return True
        return False

    def clear_tools(self) -> None:
        """Clear all registered MCP tools.

        Removes all tools from the MCP server registry.
        Useful for testing or resetting tool state.
        """
        self.mcp_tools.clear()

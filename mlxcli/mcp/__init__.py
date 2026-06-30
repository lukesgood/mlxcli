"""MCP (Model Context Protocol) integration module.

Provides tools for discovering and registering MCP-compatible external tools
that can be integrated with the MLX-CLI tool registry and agent system.
"""

from mlxcli.mcp.mcp_server import MCPServer

__all__ = ["MCPServer"]

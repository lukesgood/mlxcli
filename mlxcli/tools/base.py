"""Abstract base class for all tools."""

from abc import ABC, abstractmethod


class Tool(ABC):
    """Abstract base class that all tools must inherit from.

    Defines the interface that all tool implementations must follow:
    - name: str property with the tool's identifier
    - description: str property with human-readable description for LLM
    - execute: method that performs the tool's action

    All tools must implement these three interface members to be usable.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name/identifier.

        Returns:
            str: A unique identifier for this tool.
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for LLM.

        Returns:
            str: A human-readable description of what this tool does.
                 Used by LLM to understand tool capabilities.
        """
        pass

    @abstractmethod
    def execute(self, args: dict) -> dict:
        """Execute the tool with given arguments.

        Args:
            args: Dictionary of arguments for the tool.

        Returns:
            dict: Result dictionary that must include at minimum:
                  - "status": "ok" or "error"
                  Other keys depend on tool implementation.
        """
        pass

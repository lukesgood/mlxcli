"""Abstract base class for specialized LLM agents."""

from abc import ABC, abstractmethod


class Agent(ABC):
    """Abstract base class for specialized LLM agents.

    Defines the interface that all agents must implement.
    Agents are specialized systems that use LLM backends to
    perform specific tasks like code analysis, debugging, research, etc.

    Subclasses must implement all abstract methods and properties.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name (analyzer, debugger, researcher, etc).

        Returns:
            str: Unique name identifying this agent.
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Agent description for CLI.

        Returns:
            str: Human-readable description of what this agent does.
        """
        pass

    @abstractmethod
    def execute(self, task: str, context: dict) -> dict:
        """Execute agent task.

        Executes the agent's primary function based on the task
        and provided context.

        Args:
            task: str - Task description or code to analyze/process.
            context: dict - Context with optional keys:
                - "backend": LLMBackend instance for generating responses
                - "tools": ToolRegistry instance for available tools
                - "session": Session instance (optional)
                - "language": str (optional, for code-specific analysis)

        Returns:
            dict: Response dictionary with keys:
                - "status": "ok" | "error" - Execution status
                - "agent": str - Agent name
                - "task": str - Original task/code
                - "result": str - Main result text
                - "analysis": str (optional) - Detailed analysis
                - "suggestions": list[str] (optional) - List of suggestions
                - "message": str (on error) - Error message

        Raises:
            This method should not raise exceptions; instead return
            error status in the result dict.
        """
        pass

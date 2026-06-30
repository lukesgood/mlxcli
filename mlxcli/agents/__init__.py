"""Agent framework with registry for specialized LLM agents."""

from typing import Optional, Dict, Type

from mlxcli.agents.base_agent import Agent
from mlxcli.agents.analyzer_agent import AnalyzerAgent
from mlxcli.agents.debugger_agent import DebuggerAgent
from mlxcli.agents.researcher_agent import ResearcherAgent

# Agent registry
AGENTS: Dict[str, Type[Agent]] = {}


def register_agent(name: str, agent_class: Type[Agent]) -> None:
    """Register an agent in the global registry.

    Args:
        name: str - Unique agent name (e.g., "analyzer", "debugger")
        agent_class: Type[Agent] - Agent class (not instance)
    """
    AGENTS[name] = agent_class


def get_agent(name: str, context: dict) -> Optional[Agent]:
    """Get agent instance by name.

    Args:
        name: str - Agent name to retrieve
        context: dict - Context dict to pass to agent constructor
                 Should contain "backend", "tools", etc.

    Returns:
        Agent instance if found, None otherwise.
    """
    if name not in AGENTS:
        return None
    agent_class = AGENTS[name]
    return agent_class(context)


def list_agents() -> list:
    """List available agent names.

    Returns:
        list: Sorted list of registered agent names.
    """
    return sorted(list(AGENTS.keys()))


# Register built-in agents
register_agent("analyzer", AnalyzerAgent)
register_agent("debugger", DebuggerAgent)
register_agent("researcher", ResearcherAgent)

__all__ = [
    "Agent",
    "AnalyzerAgent",
    "DebuggerAgent",
    "ResearcherAgent",
    "AGENTS",
    "register_agent",
    "get_agent",
    "list_agents",
]

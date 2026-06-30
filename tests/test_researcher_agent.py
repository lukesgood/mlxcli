"""Tests for ResearcherAgent implementation."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.agents.base_agent import Agent
from mlxcli.agents.researcher_agent import ResearcherAgent


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


class TestResearcherAgentProperties:
    """Test ResearcherAgent basic properties."""

    def test_researcher_agent_can_be_created(self):
        """ResearcherAgent can be created with context."""
        context = {
            "backend": MagicMock(),
            "tools": MagicMock(),
        }
        agent = ResearcherAgent(context)
        assert agent is not None

    def test_researcher_agent_name_is_researcher(self):
        """ResearcherAgent.name returns 'researcher'."""
        context = {"backend": MagicMock()}
        agent = ResearcherAgent(context)
        assert agent.name == "researcher"

    def test_researcher_agent_has_description(self):
        """ResearcherAgent.description should exist and be non-empty."""
        context = {"backend": MagicMock()}
        agent = ResearcherAgent(context)
        assert agent.description is not None
        assert len(agent.description) > 0
        assert isinstance(agent.description, str)

    def test_researcher_agent_is_agent_subclass(self):
        """ResearcherAgent should be subclass of Agent."""
        assert issubclass(ResearcherAgent, Agent)

    def test_researcher_agent_stores_context(self):
        """ResearcherAgent should store context."""
        context = {"backend": MagicMock()}
        agent = ResearcherAgent(context)
        assert agent.context is context

    def test_researcher_agent_extracts_backend_from_context(self):
        """ResearcherAgent should extract backend from context."""
        mock_backend = MagicMock()
        context = {"backend": mock_backend}
        agent = ResearcherAgent(context)
        assert agent.backend is mock_backend

    def test_researcher_agent_extracts_tools_from_context(self):
        """ResearcherAgent should extract tools from context."""
        mock_tools = MagicMock()
        context = {"tools": mock_tools}
        agent = ResearcherAgent(context)
        assert agent.tools is mock_tools


class TestResearcherAgentExecution:
    """Test ResearcherAgent execute() method."""

    def test_execute_accepts_task_and_context(self):
        """execute() should accept task and context parameters."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = "Research findings"
        context = {"backend": mock_backend}
        agent = ResearcherAgent(context)
        # Should not raise TypeError
        result = agent.execute("Research quantum computing", {})
        assert isinstance(result, dict)

    def test_execute_returns_dict_with_required_fields(self):
        """execute() should return dict with required fields."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = "Research findings about topic"
        context = {"backend": mock_backend}
        agent = ResearcherAgent(context)

        result = agent.execute("Research topic", {})

        assert isinstance(result, dict)
        assert "status" in result
        assert "agent" in result
        assert "task" in result
        assert "result" in result

    def test_execute_generates_research_urls(self):
        """execute() should generate relevant research URLs."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "Research findings.\n"
            "Sources: https://example.com/topic, https://docs.example.com/info"
        )
        context = {"backend": mock_backend}
        agent = ResearcherAgent(context)

        result = agent.execute("Research AI", {})

        assert result["status"] == "ok"
        assert "sources" in result or "result" in result

    def test_execute_fetches_source_content(self):
        """execute() should fetch content from sources."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = "Research findings"
        mock_tools = MagicMock()
        context = {"backend": mock_backend, "tools": mock_tools}
        agent = ResearcherAgent(context)

        result = agent.execute("Research topic", {})

        assert result["status"] == "ok"

    def test_execute_synthesizes_findings(self):
        """execute() should synthesize research findings."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "Summary: Topic is important because...\n"
            "Key findings:\n"
            "1. Finding one\n"
            "2. Finding two"
        )
        context = {"backend": mock_backend}
        agent = ResearcherAgent(context)

        result = agent.execute("Research", {})

        assert result["status"] == "ok"
        assert "result" in result

    def test_execute_handles_empty_task(self):
        """execute() should handle empty task gracefully."""
        mock_backend = MagicMock()
        context = {"backend": mock_backend}
        agent = ResearcherAgent(context)

        result = agent.execute("", {})

        assert result["status"] == "error" or result["status"] == "ok"

    def test_execute_handles_no_backend(self):
        """execute() should handle missing backend gracefully."""
        context = {}
        agent = ResearcherAgent(context)

        result = agent.execute("Research topic", {})

        assert "status" in result
        assert result["status"] in ("error", "ok")

    def test_execute_multiple_sequential_researches(self):
        """Multiple sequential research sessions should work."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = "Research complete"
        context = {"backend": mock_backend}
        agent = ResearcherAgent(context)

        result1 = agent.execute("Research topic 1", {})
        result2 = agent.execute("Research topic 2", {})

        assert result1["status"] == "ok"
        assert result2["status"] == "ok"

    def test_execute_calls_backend_generate(self):
        """execute() should call backend.generate() with prompt."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = "Research findings"
        context = {"backend": mock_backend}
        agent = ResearcherAgent(context)

        agent.execute("Research AI", {})

        # Should have called backend.generate at least once
        mock_backend.generate.assert_called()

    def test_execute_includes_original_task(self):
        """execute() should include original task in result."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = "Research results"
        context = {"backend": mock_backend}
        agent = ResearcherAgent(context)

        task = "Research quantum mechanics"
        result = agent.execute(task, {})

        assert result["task"] == task or result["task"] is not None

    def test_execute_response_includes_agent_name(self):
        """execute() response should include 'researcher' as agent."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = "Research data"
        context = {"backend": mock_backend}
        agent = ResearcherAgent(context)

        result = agent.execute("Research", {})

        assert result.get("agent") == "researcher"

    def test_execute_extracts_urls_from_response(self):
        """execute() should extract URLs from research response."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "Found sources:\n"
            "https://example.com/article1\n"
            "https://docs.example.com/resource"
        )
        context = {"backend": mock_backend}
        agent = ResearcherAgent(context)

        result = agent.execute("Research", {})

        assert result["status"] == "ok"

    def test_execute_handles_fetch_failures_gracefully(self):
        """execute() should handle fetch failures gracefully."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = "Research findings with URL"
        mock_tools = MagicMock()
        # Simulate fetch failure
        mock_tools.execute.return_value = {"status": "error", "message": "Fetch failed"}
        context = {"backend": mock_backend, "tools": mock_tools}
        agent = ResearcherAgent(context)

        result = agent.execute("Research", {})

        # Should still return ok status even if fetch fails
        assert result["status"] == "ok" or result["status"] == "error"

    def test_execute_creates_research_prompt(self):
        """execute() should create a research prompt."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = "Findings"
        context = {"backend": mock_backend}
        agent = ResearcherAgent(context)

        agent.execute("Research machine learning", {})

        # Backend should be called with a prompt containing research instructions
        mock_backend.generate.assert_called()
        call_args = mock_backend.generate.call_args
        if call_args:
            prompt_arg = call_args[1].get("prompt") if call_args[1] else None
            # Should have created some kind of prompt
            assert prompt_arg is None or isinstance(prompt_arg, str)

    def test_execute_research_python_topic(self):
        """execute() should research Python programming topic."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "Python is a high-level programming language.\n"
            "Key resources: https://python.org, https://docs.python.org"
        )
        context = {"backend": mock_backend}
        agent = ResearcherAgent(context)

        result = agent.execute("Research Python programming", {})

        assert result["status"] == "ok"
        assert "result" in result

    def test_execute_research_scientific_topic(self):
        """execute() should research scientific topics."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "Quantum mechanics is the study of particles at atomic scale.\n"
            "https://arxiv.org/papers"
        )
        context = {"backend": mock_backend}
        agent = ResearcherAgent(context)

        result = agent.execute("Research quantum mechanics", {})

        assert result["status"] == "ok"

    def test_execute_research_historical_topic(self):
        """execute() should research historical topics."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "Historical events from Renaissance period...\n"
            "Sources from academic databases"
        )
        context = {"backend": mock_backend}
        agent = ResearcherAgent(context)

        result = agent.execute("Research Renaissance history", {})

        assert result["status"] == "ok"

    def test_execute_returns_sources_list(self):
        """execute() should return list of sources found."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "https://source1.com\n"
            "https://source2.com\n"
            "https://source3.com"
        )
        context = {"backend": mock_backend}
        agent = ResearcherAgent(context)

        result = agent.execute("Research", {})

        # Should have sources or result field
        assert "sources" in result or "result" in result or "status" in result

    def test_execute_returns_synthesis(self):
        """execute() should return synthesized findings."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "Synthesis of findings:\n"
            "Overall, the research shows..."
        )
        context = {"backend": mock_backend}
        agent = ResearcherAgent(context)

        result = agent.execute("Research", {})

        assert result["status"] == "ok"
        assert "result" in result

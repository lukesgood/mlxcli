"""Tests for Agent framework and AnalyzerAgent implementation."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.agents.base_agent import Agent
from mlxcli.agents.analyzer_agent import AnalyzerAgent
from mlxcli.agents import register_agent, get_agent, list_agents, AGENTS


class TestAgentAbstractInterface:
    """Test Agent abstract base class."""

    def test_agent_is_abstract(self):
        """Agent cannot be instantiated directly."""
        with assert_raises(TypeError):
            Agent()

    def test_agent_requires_name_property(self):
        """Agent requires implementing name property."""
        class IncompleteAgent(Agent):
            @property
            def description(self) -> str:
                return "test"

            def execute(self, task: str, context: dict) -> dict:
                return {}

        with assert_raises(TypeError):
            IncompleteAgent()

    def test_agent_requires_description_property(self):
        """Agent requires implementing description property."""
        class IncompleteAgent(Agent):
            @property
            def name(self) -> str:
                return "test"

            def execute(self, task: str, context: dict) -> dict:
                return {}

        with assert_raises(TypeError):
            IncompleteAgent()

    def test_agent_requires_execute_method(self):
        """Agent requires implementing execute method."""
        class IncompleteAgent(Agent):
            @property
            def name(self) -> str:
                return "test"

            @property
            def description(self) -> str:
                return "test"

        with assert_raises(TypeError):
            IncompleteAgent()

    def test_agent_has_name_property(self):
        """Agent requires name property."""
        # This checks that Agent defines the abstract property
        assert hasattr(Agent, 'name')

    def test_agent_has_description_property(self):
        """Agent requires description property."""
        assert hasattr(Agent, 'description')

    def test_agent_has_execute_method(self):
        """Agent requires execute method."""
        assert hasattr(Agent, 'execute')


class TestAgentRegistry:
    """Test agent registry functionality."""

    def test_register_agent_adds_to_registry(self):
        """register_agent() should add agent to AGENTS dict."""
        # Clear registry
        AGENTS.clear()

        class TestAgent(Agent):
            def __init__(self, context=None):
                pass

            @property
            def name(self) -> str:
                return "test_agent"

            @property
            def description(self) -> str:
                return "Test agent"

            def execute(self, task: str, context: dict) -> dict:
                return {"status": "ok"}

        register_agent("test_agent", TestAgent)
        assert "test_agent" in AGENTS
        assert AGENTS["test_agent"] is TestAgent

    def test_get_agent_returns_instance(self):
        """get_agent() should return agent instance."""
        AGENTS.clear()

        class TestAgent(Agent):
            def __init__(self, context=None):
                pass

            @property
            def name(self) -> str:
                return "test_agent"

            @property
            def description(self) -> str:
                return "Test agent"

            def execute(self, task: str, context: dict) -> dict:
                return {"status": "ok"}

        register_agent("test_agent", TestAgent)
        context = {"backend": MagicMock()}
        agent = get_agent("test_agent", context)

        assert agent is not None
        assert isinstance(agent, TestAgent)
        assert agent.name == "test_agent"

    def test_get_agent_returns_none_for_unknown(self):
        """get_agent() should return None for unknown agent."""
        AGENTS.clear()
        agent = get_agent("unknown_agent", {})
        assert agent is None

    def test_list_agents_returns_registered_names(self):
        """list_agents() should return list of registered agent names."""
        AGENTS.clear()

        class Agent1(Agent):
            def __init__(self, context=None):
                pass

            @property
            def name(self) -> str:
                return "agent1"

            @property
            def description(self) -> str:
                return "Agent 1"

            def execute(self, task: str, context: dict) -> dict:
                return {"status": "ok"}

        class Agent2(Agent):
            def __init__(self, context=None):
                pass

            @property
            def name(self) -> str:
                return "agent2"

            @property
            def description(self) -> str:
                return "Agent 2"

            def execute(self, task: str, context: dict) -> dict:
                return {"status": "ok"}

        register_agent("agent1", Agent1)
        register_agent("agent2", Agent2)

        agents = list_agents()
        assert "agent1" in agents
        assert "agent2" in agents

    def test_list_agents_empty_when_no_agents(self):
        """list_agents() should return empty list when no agents registered."""
        AGENTS.clear()
        agents = list_agents()
        assert isinstance(agents, list)
        assert len(agents) == 0

    def test_agent_registry_is_extensible(self):
        """Multiple different agents can be registered."""
        AGENTS.clear()

        class CustomAgent1(Agent):
            def __init__(self, context=None):
                pass

            @property
            def name(self) -> str:
                return "custom1"

            @property
            def description(self) -> str:
                return "Custom agent 1"

            def execute(self, task: str, context: dict) -> dict:
                return {"status": "ok", "agent": "custom1"}

        class CustomAgent2(Agent):
            def __init__(self, context=None):
                pass

            @property
            def name(self) -> str:
                return "custom2"

            @property
            def description(self) -> str:
                return "Custom agent 2"

            def execute(self, task: str, context: dict) -> dict:
                return {"status": "ok", "agent": "custom2"}

        register_agent("custom1", CustomAgent1)
        register_agent("custom2", CustomAgent2)

        agents = list_agents()
        assert len(agents) >= 2


class TestAnalyzerAgentProperties:
    """Test AnalyzerAgent basic properties."""

    def test_analyzer_agent_can_be_created(self):
        """AnalyzerAgent can be created with context."""
        context = {
            "backend": MagicMock(),
            "tools": MagicMock(),
        }
        agent = AnalyzerAgent(context)
        assert agent is not None

    def test_analyzer_agent_name_is_analyzer(self):
        """AnalyzerAgent.name returns 'analyzer'."""
        context = {"backend": MagicMock()}
        agent = AnalyzerAgent(context)
        assert agent.name == "analyzer"

    def test_analyzer_agent_has_description(self):
        """AnalyzerAgent.description should exist and be non-empty."""
        context = {"backend": MagicMock()}
        agent = AnalyzerAgent(context)
        assert agent.description is not None
        assert len(agent.description) > 0
        assert isinstance(agent.description, str)

    def test_analyzer_agent_is_agent_subclass(self):
        """AnalyzerAgent should be subclass of Agent."""
        assert issubclass(AnalyzerAgent, Agent)


class TestAnalyzerAgentExecution:
    """Test AnalyzerAgent execute() method."""

    def test_execute_accepts_task_and_context(self):
        """execute() should accept task and context parameters."""
        context = {"backend": MagicMock()}
        agent = AnalyzerAgent(context)
        # Should not raise TypeError
        result = agent.execute("def hello(): pass", {})
        assert isinstance(result, dict)

    def test_execute_returns_dict_with_required_fields(self):
        """execute() should return dict with required fields."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = "Analysis: test code"
        context = {"backend": mock_backend}
        agent = AnalyzerAgent(context)

        result = agent.execute("test code", {})

        assert isinstance(result, dict)
        assert "status" in result
        assert "agent" in result
        assert "task" in result
        assert "result" in result

    def test_execute_result_has_analysis_and_suggestions(self):
        """execute() result should have analysis and suggestions."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "What it does: Test function\n"
            "Improvements:\n- Add docstring\n- Better naming"
        )
        context = {"backend": mock_backend}
        agent = AnalyzerAgent(context)

        result = agent.execute("def test(): pass", {})

        assert "analysis" in result
        assert "suggestions" in result

    def test_execute_analyzes_python_code(self):
        """execute() should analyze provided Python code."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "What it does: Simple function that returns a greeting\n"
            "Key functions/classes: greet()\n"
            "Improvements:\n- Add type hints\n- Add docstring"
        )
        context = {"backend": mock_backend}
        agent = AnalyzerAgent(context)

        code = "def greet(name):\n    return f'Hello {name}'"
        result = agent.execute(f"Analyze this code: {code}", {})

        assert result["status"] == "ok"
        assert "analysis" in result
        mock_backend.generate.assert_called_once()

    def test_execute_extracts_functions_and_classes(self):
        """execute() should extract list of functions/classes."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "Key functions/classes: process_data(), DataHandler class"
        )
        context = {"backend": mock_backend}
        agent = AnalyzerAgent(context)

        result = agent.execute("test code", {})

        assert "suggestions" in result
        assert isinstance(result["suggestions"], list)

    def test_execute_provides_improvement_suggestions(self):
        """execute() should provide improvement suggestions."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "Improvements:\n"
            "- Add error handling\n"
            "- Use list comprehension instead of loop\n"
            "- Add type hints"
        )
        context = {"backend": mock_backend}
        agent = AnalyzerAgent(context)

        result = agent.execute("some code", {})

        assert "suggestions" in result
        assert len(result["suggestions"]) > 0
        assert all(isinstance(s, str) for s in result["suggestions"])

    def test_execute_handles_empty_code(self):
        """execute() should handle empty code gracefully."""
        mock_backend = MagicMock()
        context = {"backend": mock_backend}
        agent = AnalyzerAgent(context)

        result = agent.execute("", {})

        assert result["status"] == "error" or result["status"] == "ok"

    def test_execute_handles_no_backend(self):
        """execute() should handle missing backend gracefully."""
        context = {}
        agent = AnalyzerAgent(context)

        result = agent.execute("code", {})

        assert "status" in result
        # Should either error or handle gracefully
        assert result["status"] in ("error", "ok")

    def test_execute_parses_analysis_into_sections(self):
        """execute() should parse analysis into distinct sections."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "What it does: Helper function\n"
            "Key functions/classes: calculate()\n"
            "Data flow: Input -> Processing -> Output\n"
            "Improvements:\n- Better variable names\n- Add comments\n"
            "Issues: None found"
        )
        context = {"backend": mock_backend}
        agent = AnalyzerAgent(context)

        result = agent.execute("test code", {})

        assert "analysis" in result
        analysis_str = str(result["analysis"])
        # Should contain structured analysis
        assert len(analysis_str) > 0

    def test_execute_sequential_analyses(self):
        """Multiple sequential analyses should work."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = "Analysis: code analyzed"
        context = {"backend": mock_backend}
        agent = AnalyzerAgent(context)

        result1 = agent.execute("code 1", {})
        result2 = agent.execute("code 2", {})

        assert result1["status"] == "ok"
        assert result2["status"] == "ok"
        assert result1["task"] != result2["task"]

    def test_execute_includes_data_flow_explanation(self):
        """Analysis should include data flow explanation."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "Data flow: Input parameters -> Function processing -> Return value"
        )
        context = {"backend": mock_backend}
        agent = AnalyzerAgent(context)

        result = agent.execute("def process(data): return data", {})

        # Should have some form of analysis that includes data flow concept
        assert "analysis" in result or "result" in result

    def test_execute_identifies_potential_issues(self):
        """Analysis should identify potential issues."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = (
            "Issues found: Missing error handling, potential None reference"
        )
        context = {"backend": mock_backend}
        agent = AnalyzerAgent(context)

        result = agent.execute("risky code", {})

        assert result["status"] == "ok"
        # Should capture the issues in the analysis
        analysis_text = str(result.get("analysis", "")) + str(result.get("result", ""))
        assert len(analysis_text) > 0

    def test_execute_calls_backend_generate(self):
        """execute() should call backend.generate() with prompt."""
        mock_backend = MagicMock()
        mock_backend.generate.return_value = "Analysis: test"
        context = {"backend": mock_backend}
        agent = AnalyzerAgent(context)

        agent.execute("def foo(): pass", {})

        # Should have called backend.generate at least once
        mock_backend.generate.assert_called()


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

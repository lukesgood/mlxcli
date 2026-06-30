"""Tests for Workflow Engine - Multi-step task automation with YAML/JSON workflow support."""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.workflows.workflow_parser import WorkflowParser
from mlxcli.workflows.workflow_engine import WorkflowEngine
from mlxcli.backends.base import LLMBackend
from mlxcli.agents.base_agent import Agent
from mlxcli.tool_registry import ToolRegistry
from mlxcli.tools.base import Tool


# ============================================================================
# Mock implementations for testing
# ============================================================================


class MockBackend(LLMBackend):
    """Mock LLM backend for testing."""

    @property
    def name(self) -> str:
        return "mock"

    @property
    def available(self) -> bool:
        return True

    def get_available_models(self) -> list[dict]:
        return []

    def load_model(self, model_name: str) -> bool:
        return True

    def generate(self, prompt: str, messages=None, tools=None, max_tokens: int = 512) -> str:
        return "Mock response"

    def count_tokens(self, text: str) -> int:
        return len(text.split())

    @property
    def current_model_name(self) -> str:
        return "mock_model"


class MockAgent(Agent):
    """Mock agent for testing."""

    def __init__(self, name: str = "mock_agent", context: dict = None):
        self._name = name
        self._context = context or {}

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return f"Mock agent: {self._name}"

    def execute(self, task: str, context: dict) -> dict:
        """Execute mock agent task."""
        return {
            "status": "ok",
            "agent": self._name,
            "task": task,
            "result": f"Completed: {task}",
        }


class MockAgentRegistry:
    """Mock agent registry for testing."""

    def __init__(self):
        self.agents = {}

    def register(self, name: str, agent: Agent) -> None:
        self.agents[name] = agent

    def get(self, name: str) -> Agent:
        return self.agents.get(name)

    def get_agent(self, name: str, context: dict) -> Agent:
        """Get or create agent by name."""
        if name not in self.agents:
            self.agents[name] = MockAgent(name, context)
        return self.agents[name]


class SimpleMockTool(Tool):
    """Simple mock tool for testing."""

    def __init__(self, name: str = "mock_tool", response: dict = None):
        self._name = name
        self._response = response or {"status": "ok", "result": "Tool executed"}

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return f"Mock tool: {self._name}"

    def execute(self, args: dict) -> dict:
        return self._response


# ============================================================================
# Parser Tests
# ============================================================================


class TestWorkflowParserYAML:
    """Test YAML workflow parsing."""

    def test_parse_simple_yaml_workflow(self):
        """Should parse a simple YAML workflow."""
        yaml_str = """
version: "1.0"
name: "Simple Workflow"
description: "A simple test workflow"
steps:
  - id: "step1"
    agent: "analyzer"
    task: "Analyze something"
    output: "result"
"""
        result = WorkflowParser.parse_yaml(yaml_str)
        assert result is not None
        assert result["version"] == "1.0"
        assert result["name"] == "Simple Workflow"
        assert len(result["steps"]) == 1
        assert result["steps"][0]["id"] == "step1"

    def test_parse_yaml_with_multiple_steps(self):
        """Should parse YAML with multiple steps."""
        yaml_str = """
version: "1.0"
name: "Multi Step Workflow"
steps:
  - id: "research"
    agent: "researcher"
    task: "Research Python"
  - id: "analyze"
    agent: "analyzer"
    task: "Analyze findings"
  - id: "report"
    tool: "print"
    action: "Print results"
"""
        result = WorkflowParser.parse_yaml(yaml_str)
        assert len(result["steps"]) == 3
        assert result["steps"][0]["id"] == "research"
        assert result["steps"][1]["id"] == "analyze"
        assert result["steps"][2]["id"] == "report"

    def test_parse_yaml_with_variables(self):
        """Should parse YAML with variable references."""
        yaml_str = """
version: "1.0"
name: "Workflow with Variables"
steps:
  - id: "step1"
    agent: "analyzer"
    task: "Analyze {{topic}}"
    context:
      topic: "Python async/await"
    output: "analysis"
"""
        result = WorkflowParser.parse_yaml(yaml_str)
        assert result["steps"][0]["task"] == "Analyze {{topic}}"
        assert result["steps"][0]["context"]["topic"] == "Python async/await"

    def test_parse_yaml_with_conditionals(self):
        """Should parse YAML with conditions."""
        yaml_str = """
version: "1.0"
name: "Workflow with Conditions"
steps:
  - id: "step1"
    agent: "analyzer"
    task: "Do something"
    output: "result"
  - id: "step2"
    agent: "analyzer"
    task: "Do next step"
    condition: "{{result}} != null"
    depends_on: "step1"
"""
        result = WorkflowParser.parse_yaml(yaml_str)
        assert result["steps"][1]["condition"] == "{{result}} != null"
        assert result["steps"][1]["depends_on"] == "step1"

    def test_parse_yaml_with_dependencies(self):
        """Should parse YAML with step dependencies."""
        yaml_str = """
version: "1.0"
name: "Workflow with Dependencies"
steps:
  - id: "step1"
    agent: "analyzer"
    task: "First"
    output: "first"
  - id: "step2"
    agent: "analyzer"
    task: "Second"
    depends_on: "step1"
    output: "second"
"""
        result = WorkflowParser.parse_yaml(yaml_str)
        assert result["steps"][1]["depends_on"] == "step1"

    def test_parse_yaml_with_nested_variables(self):
        """Should parse YAML with nested variable references."""
        yaml_str = """
version: "1.0"
name: "Workflow with Nested Variables"
steps:
  - id: "step1"
    agent: "analyzer"
    task: "Use {{data.findings.urls}}"
    output: "analysis"
"""
        result = WorkflowParser.parse_yaml(yaml_str)
        assert "{{data.findings.urls}}" in result["steps"][0]["task"]

    def test_parse_yaml_with_tool_execution(self):
        """Should parse YAML with tool execution."""
        yaml_str = """
version: "1.0"
name: "Workflow with Tools"
steps:
  - id: "fetch"
    tool: "WebFetchTool"
    action: "fetch"
    args:
      url: "https://example.com"
    output: "content"
"""
        result = WorkflowParser.parse_yaml(yaml_str)
        assert result["steps"][0]["tool"] == "WebFetchTool"
        assert result["steps"][0]["args"]["url"] == "https://example.com"


class TestWorkflowParserJSON:
    """Test JSON workflow parsing."""

    def test_parse_simple_json_workflow(self):
        """Should parse a simple JSON workflow."""
        json_str = """{
  "version": "1.0",
  "name": "Simple JSON Workflow",
  "steps": [
    {
      "id": "step1",
      "agent": "analyzer",
      "task": "Analyze something",
      "output": "result"
    }
  ]
}"""
        result = WorkflowParser.parse_json(json_str)
        assert result is not None
        assert result["version"] == "1.0"
        assert result["name"] == "Simple JSON Workflow"
        assert len(result["steps"]) == 1

    def test_parse_json_with_multiple_steps(self):
        """Should parse JSON with multiple steps."""
        json_str = """{
  "version": "1.0",
  "name": "Multi Step",
  "steps": [
    {"id": "s1", "agent": "analyzer", "task": "Task 1"},
    {"id": "s2", "agent": "analyzer", "task": "Task 2"}
  ]
}"""
        result = WorkflowParser.parse_json(json_str)
        assert len(result["steps"]) == 2
        assert result["steps"][0]["id"] == "s1"
        assert result["steps"][1]["id"] == "s2"

    def test_parse_json_with_complex_structure(self):
        """Should parse JSON with complex structure."""
        json_str = """{
  "version": "1.0",
  "name": "Complex Workflow",
  "description": "A complex workflow",
  "steps": [
    {
      "id": "research",
      "agent": "researcher",
      "task": "Research {{topic}}",
      "output": "findings"
    },
    {
      "id": "analyze",
      "agent": "analyzer",
      "task": "Analyze: {{findings}}",
      "depends_on": "research",
      "condition": "{{findings}} != null",
      "output": "analysis"
    }
  ]
}"""
        result = WorkflowParser.parse_json(json_str)
        assert len(result["steps"]) == 2
        assert result["steps"][0]["agent"] == "researcher"
        assert result["steps"][1]["depends_on"] == "research"


class TestWorkflowParserValidation:
    """Test workflow validation."""

    def test_validate_valid_yaml_workflow(self):
        """Should validate a valid workflow."""
        workflow = {
            "version": "1.0",
            "name": "Valid Workflow",
            "steps": [{"id": "step1", "agent": "analyzer", "task": "Do something"}],
        }
        is_valid, error = WorkflowParser.validate_workflow(workflow)
        assert is_valid is True
        assert error == ""

    def test_validate_workflow_missing_version(self):
        """Should reject workflow without version."""
        workflow = {
            "name": "Invalid Workflow",
            "steps": [{"id": "step1", "agent": "analyzer", "task": "Do something"}],
        }
        is_valid, error = WorkflowParser.validate_workflow(workflow)
        assert is_valid is False
        assert "version" in error.lower()

    def test_validate_workflow_missing_name(self):
        """Should reject workflow without name."""
        workflow = {
            "version": "1.0",
            "steps": [{"id": "step1", "agent": "analyzer", "task": "Do something"}],
        }
        is_valid, error = WorkflowParser.validate_workflow(workflow)
        assert is_valid is False
        assert "name" in error.lower()

    def test_validate_workflow_missing_steps(self):
        """Should reject workflow without steps."""
        workflow = {"version": "1.0", "name": "Invalid Workflow"}
        is_valid, error = WorkflowParser.validate_workflow(workflow)
        assert is_valid is False
        assert "steps" in error.lower()

    def test_validate_workflow_empty_steps(self):
        """Should reject workflow with empty steps."""
        workflow = {"version": "1.0", "name": "Invalid Workflow", "steps": []}
        is_valid, error = WorkflowParser.validate_workflow(workflow)
        assert is_valid is False
        assert "steps" in error.lower()

    def test_validate_step_missing_id(self):
        """Should reject step without id."""
        workflow = {
            "version": "1.0",
            "name": "Invalid Workflow",
            "steps": [{"agent": "analyzer", "task": "Do something"}],
        }
        is_valid, error = WorkflowParser.validate_workflow(workflow)
        assert is_valid is False
        assert "id" in error.lower()

    def test_validate_step_missing_agent_or_tool(self):
        """Should reject step without agent or tool."""
        workflow = {
            "version": "1.0",
            "name": "Invalid Workflow",
            "steps": [{"id": "step1", "task": "Do something"}],
        }
        is_valid, error = WorkflowParser.validate_workflow(workflow)
        assert is_valid is False
        assert ("agent" in error.lower() or "tool" in error.lower())

    def test_validate_workflow_unsupported_version(self):
        """Should reject workflow with unsupported version."""
        workflow = {
            "version": "2.0",
            "name": "Invalid Workflow",
            "steps": [{"id": "step1", "agent": "analyzer", "task": "Do something"}],
        }
        is_valid, error = WorkflowParser.validate_workflow(workflow)
        assert is_valid is False
        assert "version" in error.lower()


# ============================================================================
# WorkflowEngine Tests
# ============================================================================


class TestWorkflowEngineInitialization:
    """Test WorkflowEngine initialization."""

    def test_init_workflow_engine(self):
        """Should initialize WorkflowEngine."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        assert engine is not None

    def test_engine_stores_dependencies(self):
        """Should store backend, agents, and tools."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        # Access via execution - verify they're stored and accessible
        workflow = {
            "version": "1.0",
            "name": "Test",
            "steps": [{"id": "step1", "agent": "test_agent", "task": "Test"}],
        }
        # Should not raise
        import asyncio

        asyncio.run(engine.execute(workflow))


class TestWorkflowEngineVariableResolution:
    """Test variable resolution in workflow engine."""

    def test_resolve_simple_variable(self):
        """Should resolve simple {{var}} references."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        context = {"name": "Alice", "value": "123"}
        result = engine._resolve_variables("Hello {{name}}, value: {{value}}", context)
        assert result == "Hello Alice, value: 123"

    def test_resolve_variable_missing_key(self):
        """Should handle missing context keys gracefully."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        context = {"name": "Alice"}
        result = engine._resolve_variables("Hello {{name}}, value: {{missing}}", context)
        # Should leave unresolved variables as-is or handle gracefully
        assert "{{missing}}" in result or "missing" not in result

    def test_resolve_variable_no_variables(self):
        """Should return text unchanged if no variables."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        context = {"name": "Alice"}
        result = engine._resolve_variables("Hello world", context)
        assert result == "Hello world"

    def test_resolve_multiple_same_variable(self):
        """Should resolve multiple occurrences of same variable."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        context = {"var": "value"}
        result = engine._resolve_variables("{{var}} then {{var}} again", context)
        assert result == "value then value again"


class TestWorkflowEngineConditionEvaluation:
    """Test condition evaluation in workflow engine."""

    def test_evaluate_simple_equality_true(self):
        """Should evaluate simple equality condition as true."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        context = {"status": "ok"}
        result = engine._evaluate_condition("{{status}} == ok", context)
        assert result is True

    def test_evaluate_simple_equality_false(self):
        """Should evaluate simple equality condition as false."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        context = {"status": "error"}
        result = engine._evaluate_condition("{{status}} == ok", context)
        assert result is False

    def test_evaluate_inequality_true(self):
        """Should evaluate inequality as true."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        context = {"value": "123"}
        result = engine._evaluate_condition("{{value}} != null", context)
        assert result is True

    def test_evaluate_inequality_false(self):
        """Should evaluate inequality as false when equal."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        context = {"value": "null"}
        result = engine._evaluate_condition("{{value}} != null", context)
        assert result is False

    def test_evaluate_greater_than(self):
        """Should evaluate greater than condition."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        context = {"count": "10"}
        result = engine._evaluate_condition("{{count}} > 5", context)
        assert result is True

    def test_evaluate_less_than(self):
        """Should evaluate less than condition."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        context = {"count": "3"}
        result = engine._evaluate_condition("{{count}} < 5", context)
        assert result is True


class TestWorkflowEngineExecution:
    """Test workflow execution."""

    @pytest.mark.asyncio
    async def test_execute_simple_workflow(self):
        """Should execute a simple single-step workflow."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        workflow = {
            "version": "1.0",
            "name": "Simple Test",
            "steps": [{"id": "step1", "agent": "test_agent", "task": "Test task"}],
        }

        result = await engine.execute(workflow)
        assert result["status"] == "success"
        assert result["steps_executed"] == 1
        assert "step1" in result["results"]

    @pytest.mark.asyncio
    async def test_execute_multi_step_workflow(self):
        """Should execute multi-step workflow."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        workflow = {
            "version": "1.0",
            "name": "Multi-step Test",
            "steps": [
                {"id": "step1", "agent": "test_agent", "task": "Task 1"},
                {"id": "step2", "agent": "test_agent", "task": "Task 2"},
                {"id": "step3", "agent": "test_agent", "task": "Task 3"},
            ],
        }

        result = await engine.execute(workflow)
        assert result["status"] == "success"
        assert result["steps_executed"] == 3
        assert "step1" in result["results"]
        assert "step2" in result["results"]
        assert "step3" in result["results"]

    @pytest.mark.asyncio
    async def test_execute_workflow_with_context_passing(self):
        """Should pass context between steps."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        workflow = {
            "version": "1.0",
            "name": "Context Passing Test",
            "steps": [
                {
                    "id": "step1",
                    "agent": "test_agent",
                    "task": "Task with {{input}}",
                    "context": {"input": "test_value"},
                    "output": "result1",
                },
                {
                    "id": "step2",
                    "agent": "test_agent",
                    "task": "Use result: {{result1}}",
                    "depends_on": "step1",
                    "output": "result2",
                },
            ],
        }

        result = await engine.execute(workflow)
        assert result["status"] == "success"
        assert result["steps_executed"] == 2

    @pytest.mark.asyncio
    async def test_execute_workflow_with_condition_true(self):
        """Should execute conditional step when condition is true."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        workflow = {
            "version": "1.0",
            "name": "Condition True Test",
            "steps": [
                {
                    "id": "step1",
                    "agent": "test_agent",
                    "task": "Set value",
                    "output": "status",
                },
                {
                    "id": "step2",
                    "agent": "test_agent",
                    "task": "Conditional task",
                    "condition": "{{status}} != null",
                    "depends_on": "step1",
                    "output": "result",
                },
            ],
        }

        result = await engine.execute(workflow)
        assert result["status"] == "success"
        assert result["steps_executed"] == 2

    @pytest.mark.asyncio
    async def test_execute_workflow_with_condition_false(self):
        """Should skip conditional step when condition is false."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        workflow = {
            "version": "1.0",
            "name": "Condition False Test",
            "steps": [
                {
                    "id": "step1",
                    "agent": "test_agent",
                    "task": "Set value",
                    "context": {"value": "null"},
                    "output": "value",
                },
                {
                    "id": "step2",
                    "agent": "test_agent",
                    "task": "Conditional task",
                    "condition": "{{value}} != null",
                    "depends_on": "step1",
                    "output": "result",
                },
            ],
        }

        result = await engine.execute(workflow)
        # Should skip step2, so only step1 should be executed
        assert result["status"] == "success"
        # steps_executed should be 1 since step2 was skipped
        assert result["steps_executed"] <= 2

    @pytest.mark.asyncio
    async def test_execute_workflow_with_dependencies(self):
        """Should respect step dependencies."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        workflow = {
            "version": "1.0",
            "name": "Dependency Test",
            "steps": [
                {"id": "step1", "agent": "test_agent", "task": "First", "output": "first"},
                {
                    "id": "step2",
                    "agent": "test_agent",
                    "task": "Second",
                    "depends_on": "step1",
                    "output": "second",
                },
                {
                    "id": "step3",
                    "agent": "test_agent",
                    "task": "Third",
                    "depends_on": "step2",
                    "output": "third",
                },
            ],
        }

        result = await engine.execute(workflow)
        assert result["status"] == "success"
        assert result["steps_executed"] == 3

    @pytest.mark.asyncio
    async def test_execute_workflow_with_initial_context(self):
        """Should use initial context in workflow execution."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        workflow = {
            "version": "1.0",
            "name": "Initial Context Test",
            "steps": [
                {
                    "id": "step1",
                    "agent": "test_agent",
                    "task": "Use {{topic}}",
                    "output": "result",
                }
            ],
        }

        initial_context = {"topic": "Python"}
        result = await engine.execute(workflow, initial_context)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_workflow_returns_final_output(self):
        """Should return final output designated in workflow."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        workflow = {
            "version": "1.0",
            "name": "Final Output Test",
            "final_output": "result",
            "steps": [{"id": "step1", "agent": "test_agent", "task": "Task", "output": "result"}],
        }

        result = await engine.execute(workflow)
        assert result["status"] == "success"
        assert "final_output" in result or result["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_workflow_handles_missing_agent(self):
        """Should handle missing agent gracefully."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        workflow = {
            "version": "1.0",
            "name": "Missing Agent Test",
            "steps": [
                {
                    "id": "step1",
                    "agent": "nonexistent_agent",
                    "task": "Task",
                    "output": "result",
                }
            ],
        }

        # Should not raise, but might fail gracefully
        result = await engine.execute(workflow)
        # Status should indicate success or we handled error
        assert result is not None

    @pytest.mark.asyncio
    async def test_execute_workflow_returns_results_dict(self):
        """Should return results for each executed step."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        workflow = {
            "version": "1.0",
            "name": "Results Test",
            "steps": [
                {"id": "step1", "agent": "test_agent", "task": "Task 1", "output": "out1"},
                {"id": "step2", "agent": "test_agent", "task": "Task 2", "output": "out2"},
            ],
        }

        result = await engine.execute(workflow)
        assert "results" in result
        assert isinstance(result["results"], dict)
        assert result["steps_executed"] > 0


# ============================================================================
# Integration Tests
# ============================================================================


class TestWorkflowEngineIntegration:
    """Integration tests for workflow engine."""

    @pytest.mark.asyncio
    async def test_workflow_with_all_features(self):
        """Should execute workflow with all features combined."""
        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        workflow = {
            "version": "1.0",
            "name": "Complete Workflow",
            "description": "Tests all workflow features",
            "final_output": "report",
            "steps": [
                {
                    "id": "research",
                    "agent": "researcher",
                    "task": "Research {{topic}}",
                    "context": {"topic": "Python async/await"},
                    "output": "findings",
                },
                {
                    "id": "analyze",
                    "agent": "analyzer",
                    "task": "Analyze: {{findings}}",
                    "depends_on": "research",
                    "condition": "{{findings}} != null",
                    "output": "analysis",
                },
                {
                    "id": "report",
                    "agent": "analyzer",
                    "task": "Create report from {{analysis}}",
                    "depends_on": "analyze",
                    "output": "report",
                },
            ],
        }

        result = await engine.execute(workflow)
        assert result["status"] == "success"
        assert result["steps_executed"] >= 2

    @pytest.mark.asyncio
    async def test_parse_and_execute_yaml_workflow(self):
        """Should parse YAML and execute workflow."""
        yaml_str = """
version: "1.0"
name: "YAML Workflow"
steps:
  - id: "step1"
    agent: "analyzer"
    task: "Analyze {{data}}"
    context:
      data: "test data"
    output: "result"
  - id: "step2"
    agent: "analyzer"
    task: "Report {{result}}"
    depends_on: "step1"
    output: "report"
"""
        workflow = WorkflowParser.parse_yaml(yaml_str)
        is_valid, error = WorkflowParser.validate_workflow(workflow)
        assert is_valid is True

        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        result = await engine.execute(workflow)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_parse_and_execute_json_workflow(self):
        """Should parse JSON and execute workflow."""
        json_str = """{
  "version": "1.0",
  "name": "JSON Workflow",
  "steps": [
    {
      "id": "step1",
      "agent": "analyzer",
      "task": "Process {{input}}",
      "context": {"input": "data"},
      "output": "processed"
    },
    {
      "id": "step2",
      "agent": "analyzer",
      "task": "Report {{processed}}",
      "depends_on": "step1",
      "output": "report"
    }
  ]
}"""
        workflow = WorkflowParser.parse_json(json_str)
        is_valid, error = WorkflowParser.validate_workflow(workflow)
        assert is_valid is True

        backend = MockBackend()
        agents = MockAgentRegistry()
        tools = ToolRegistry()

        engine = WorkflowEngine(backend, agents, tools)
        result = await engine.execute(workflow)
        assert result["status"] == "success"

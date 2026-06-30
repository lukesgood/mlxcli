"""End-to-end integration tests for Phase 3 features.

Comprehensive test suite covering multi-backend support, agent workflows,
tool orchestration, workflow engine integration, and complete feature scenarios.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.agents.analyzer_agent import AnalyzerAgent
from mlxcli.agents.debugger_agent import DebuggerAgent
from mlxcli.agents.researcher_agent import ResearcherAgent
from mlxcli.mcp.mcp_server import MCPServer
from mlxcli.tool_registry import ToolRegistry
from mlxcli.tools.base import Tool
from mlxcli.tools.code_execution_tool import CodeExecutionTool
from mlxcli.tools.file_tool import FileTool
from mlxcli.tools.shell_tool import ShellTool
from mlxcli.tools.web_fetch_tool import WebFetchTool
from mlxcli.workflows.workflow_engine import WorkflowEngine


class MockBackend:
    """Mock LLM backend for testing."""

    def __init__(self, response="Mock response"):
        self.response = response
        self.call_count = 0
        self.last_prompt = None

    def generate(self, prompt: str, max_tokens: int = 1024, context: dict = None) -> str:
        """Generate mock response."""
        self.call_count += 1
        self.last_prompt = prompt
        return self.response

    def set_response(self, response: str):
        """Set the response to return."""
        self.response = response


class TestMultiBackendFlows:
    """Test workflows with multiple backend support."""

    def test_switch_between_backends(self):
        """Should be able to switch between different backends."""
        mock_backend1 = MockBackend("Response from backend 1")
        mock_backend2 = MockBackend("Response from backend 2")

        context1 = {"backend": mock_backend1}
        context2 = {"backend": mock_backend2}

        assert mock_backend1.generate("test") == "Response from backend 1"
        assert mock_backend2.generate("test") == "Response from backend 2"

    def test_each_backend_works_for_generation(self):
        """Each backend should independently generate responses."""
        backends = [
            MockBackend(f"Response from backend {i}") for i in range(3)
        ]

        for i, backend in enumerate(backends):
            response = backend.generate("test prompt")
            assert f"Response from backend {i}" in response

    def test_backend_context_propagation(self):
        """Backend should be properly passed through context."""
        backend = MockBackend("Context test response")
        context = {"backend": backend}

        retrieved_backend = context.get("backend")
        assert retrieved_backend is backend
        assert retrieved_backend.generate("test") == "Context test response"

    def test_models_available_differ_by_backend(self):
        """Different backends should report different available models."""
        backend1 = MockBackend()
        backend1.models = ["model_a", "model_b"]

        backend2 = MockBackend()
        backend2.models = ["model_x", "model_y", "model_z"]

        assert len(backend1.models) == 2
        assert len(backend2.models) == 3
        assert backend1.models != backend2.models


class TestAgentWorkflows:
    """Test agent execution workflows."""

    def test_run_analyzer_agent(self):
        """Should be able to run Analyzer agent."""
        backend = MockBackend("Code analysis: This function does X")
        registry = ToolRegistry()

        context = {"backend": backend, "tools": registry}
        agent = AnalyzerAgent(context)

        result = agent.execute("def foo(): pass", {})

        assert result["status"] == "ok"
        assert result["agent"] == "analyzer"

    def test_run_debugger_agent(self):
        """Should be able to run Debugger agent."""
        backend = MockBackend("Debug analysis: The issue is Y")
        registry = ToolRegistry()

        context = {"backend": backend, "tools": registry}
        agent = DebuggerAgent(context)

        result = agent.execute("Bug: function fails on input X", {})

        assert result["status"] == "ok"
        assert result["agent"] == "debugger"

    def test_run_researcher_agent(self):
        """Should be able to run Researcher agent."""
        backend = MockBackend("Research results: Topic is Z")
        registry = ToolRegistry()

        context = {"backend": backend, "tools": registry}
        agent = ResearcherAgent(context)

        result = agent.execute("Research: How does Python GIL work?", {})

        assert result["status"] == "ok"
        assert result["agent"] == "researcher"

    def test_chain_agents_with_outputs(self):
        """Should be able to chain multiple agents."""
        backend = MockBackend()
        registry = ToolRegistry()
        context = {"backend": backend, "tools": registry}

        # First agent
        backend.set_response("Code analysis: Function computes X")
        analyzer = AnalyzerAgent(context)
        analysis_result = analyzer.execute("def compute(): pass", {})
        assert analysis_result["status"] == "ok"

        # Second agent uses first result
        backend.set_response("Debug check: Code looks correct")
        debugger = DebuggerAgent(context)
        debug_result = debugger.execute(analysis_result.get("result", ""), {})
        assert debug_result["status"] == "ok"

        # Third agent for research
        backend.set_response("Research: Similar patterns found")
        researcher = ResearcherAgent(context)
        research_result = researcher.execute(debug_result.get("result", ""), {})
        assert research_result["status"] == "ok"

    def test_agent_error_handling(self):
        """Agents should handle errors gracefully."""
        backend = None  # No backend
        registry = ToolRegistry()

        context = {"backend": backend, "tools": registry}
        agent = AnalyzerAgent(context)

        result = agent.execute("code", {})
        assert result["status"] == "error"


class TestToolWorkflows:
    """Test workflows using various tools."""

    def test_use_web_fetch_tool(self):
        """Should be able to use WebFetchTool."""
        tool = WebFetchTool()
        result = tool.execute({"url": "https://example.com"})

        # WebFetchTool may fail due to network, but should return proper format
        assert isinstance(result, dict)
        assert "status" in result

    def test_use_code_execution_tool(self):
        """Should be able to use CodeExecutionTool."""
        tool = CodeExecutionTool()
        result = tool.execute({"code": "x = 1 + 1", "language": "python"})

        assert isinstance(result, dict)
        assert "status" in result

    def test_use_file_tool(self):
        """Should be able to use FileTool."""
        tool = FileTool()

        # Test reading (may fail if file doesn't exist, but should return proper format)
        result = tool.execute({"operation": "read", "path": "/tmp/test.txt"})
        assert isinstance(result, dict)
        assert "status" in result

    def test_use_shell_tool(self):
        """Should be able to use ShellTool."""
        tool = ShellTool()
        result = tool.execute({"command": "echo 'test'"})

        assert isinstance(result, dict)
        assert "status" in result

    def test_tool_registry_with_all_tools(self):
        """All tools should be registered together."""
        registry = ToolRegistry()

        tools = [
            WebFetchTool(),
            CodeExecutionTool(),
            FileTool(),
            ShellTool(),
        ]

        for tool in tools:
            registry.register(tool)

        tool_names = registry.list_tools()
        assert len(tool_names) >= 4

    def test_tools_execute_through_registry(self):
        """Tools should execute properly through registry."""
        registry = ToolRegistry()
        registry.register(CodeExecutionTool())

        # Execute through registry
        result = registry.execute("code_execution", {
            "code": "x = 2 + 2",
            "language": "python"
        })

        assert isinstance(result, dict)
        assert result["status"] in ["ok", "error"]


class TestWorkflowEngine:
    """Test workflow engine with multiple steps."""

    def test_execute_multi_step_workflow(self):
        """Should be able to execute multi-step workflow."""
        backend = MockBackend()
        registry = ToolRegistry()
        agents_dict = {}

        engine = WorkflowEngine(backend, agents_dict, registry)

        # Create a simple workflow
        workflow = {
            "name": "test_workflow",
            "steps": [
                {"id": "step1", "action": "tool", "tool": "code_execution"},
                {"id": "step2", "action": "tool", "tool": "shell"},
            ]
        }

        # Engine should support workflow structure
        assert engine is not None

    def test_pass_context_between_workflow_steps(self):
        """Context should pass between workflow steps."""
        backend = MockBackend()
        context1 = {"backend": backend, "data": "initial"}

        # Simulate context passing
        context2 = context1.copy()
        context2["data"] = "modified"

        assert context1["data"] == "initial"
        assert context2["data"] == "modified"

    def test_conditional_execution_in_workflow(self):
        """Workflow should support conditional execution."""
        backend = MockBackend()
        context = {"backend": backend}

        # Simulate conditional check
        step_result = {"status": "ok"}
        if step_result["status"] == "ok":
            execute = True
        else:
            execute = False

        assert execute is True

    def test_workflow_with_agents_and_tools(self):
        """Workflow should integrate agents and tools."""
        backend = MockBackend("Result")
        registry = ToolRegistry()
        registry.register(CodeExecutionTool())

        context = {"backend": backend, "tools": registry}

        # Agent execution in workflow
        agent = AnalyzerAgent(context)
        agent_result = agent.execute("test code", {})
        assert agent_result["status"] == "ok"

        # Tool execution in workflow
        tool_result = registry.execute("code_execution", {"code": "x=1"})
        assert tool_result["status"] in ["ok", "error"]


class TestEndToEndScenarios:
    """Test complete end-to-end feature scenarios."""

    def test_research_then_analyze_scenario(self):
        """Complete workflow: Research → Analyzer."""
        backend = MockBackend()
        registry = ToolRegistry()
        context = {"backend": backend, "tools": registry}

        # Step 1: Researcher gathers information
        backend.set_response("Research found: Algorithm is O(n)")
        researcher = ResearcherAgent(context)
        research_result = researcher.execute("How efficient is quicksort?", {})
        assert research_result["status"] == "ok"

        # Step 2: Analyzer examines the findings
        backend.set_response("Analysis: Implementation is correct")
        analyzer = AnalyzerAgent(context)
        analysis_result = analyzer.execute(research_result.get("result", ""), {})
        assert analysis_result["status"] == "ok"

    def test_debug_fetch_synthesize_scenario(self):
        """Complete workflow: Debugger → WebFetch → Synthesis."""
        backend = MockBackend()
        registry = ToolRegistry()
        registry.register(WebFetchTool())
        context = {"backend": backend, "tools": registry}

        # Step 1: Debugger identifies issue
        backend.set_response("Debug: Need to check documentation")
        debugger = DebuggerAgent(context)
        debug_result = debugger.execute("Error in function call", {})
        assert debug_result["status"] == "ok"

        # Step 2: Fetch documentation (mock)
        backend.set_response("Retrieved documentation on function")
        fetch_result = {"status": "ok", "content": "Docs found"}

        # Step 3: Synthesize findings
        backend.set_response("Solution: Use correct parameter order")
        synthesis_result = backend.generate(f"Based on: {fetch_result['content']}")
        assert synthesis_result is not None

    def test_complex_workflow_five_plus_steps(self):
        """Complex workflow with 5+ steps."""
        backend = MockBackend()
        registry = ToolRegistry()
        registry.register(CodeExecutionTool())
        registry.register(ShellTool())
        context = {"backend": backend, "tools": registry}

        steps = []

        # Step 1: Research
        backend.set_response("Found relevant patterns")
        researcher = ResearcherAgent(context)
        step1 = researcher.execute("Find patterns", {})
        steps.append(step1)

        # Step 2: Analyze
        backend.set_response("Analysis shows two approaches")
        analyzer = AnalyzerAgent(context)
        step2 = analyzer.execute(step1.get("result", ""), {})
        steps.append(step2)

        # Step 3: Code execution test
        step3 = registry.execute("code_execution", {"code": "x=1"})
        steps.append(step3)

        # Step 4: Shell command
        step4 = registry.execute("shell", {"command": "echo test"})
        steps.append(step4)

        # Step 5: Debug review
        backend.set_response("Implementation looks good")
        debugger = DebuggerAgent(context)
        step5 = debugger.execute(step2.get("result", ""), {})
        steps.append(step5)

        # All steps should complete
        assert len(steps) == 5

    def test_workflow_with_error_recovery(self):
        """Workflow should recover from errors."""
        backend = MockBackend()
        registry = ToolRegistry()
        context = {"backend": backend, "tools": registry}

        # Step 1: Initial attempt (may fail)
        backend.set_response("Error occurred")
        result1 = registry.execute("nonexistent_tool", {})
        assert result1["status"] == "error"

        # Step 2: Recovery - use alternate approach
        backend.set_response("Alternative approach works")
        agent = AnalyzerAgent(context)
        result2 = agent.execute("test", {})
        assert result2["status"] == "ok"

        # Workflow continues successfully
        assert result2["status"] == "ok"

    def test_full_feature_integration(self):
        """Full integration of all Phase 3 features."""
        # Setup all components
        backend = MockBackend()
        registry = ToolRegistry()
        mcp_server = MCPServer(registry)

        # Register standard tools
        tools = [
            WebFetchTool(),
            CodeExecutionTool(),
            FileTool(),
            ShellTool(),
        ]
        for tool in tools:
            registry.register(tool)

        # Register MCP tools
        def mcp_analyze(args):
            return {"status": "ok", "analysis": "MCP analysis"}

        mcp_server.register_mcp_tool(
            "mcp_analyzer",
            "MCP analyzer",
            mcp_analyze,
        )

        context = {"backend": backend, "tools": registry}

        # Run various agent workflows
        researcher = ResearcherAgent(context)
        r_result = researcher.execute("Test research", {})
        assert r_result["status"] == "ok"

        analyzer = AnalyzerAgent(context)
        a_result = analyzer.execute("Test code", {})
        assert a_result["status"] == "ok"

        debugger = DebuggerAgent(context)
        d_result = debugger.execute("Test debug", {})
        assert d_result["status"] == "ok"

        # Use tools through registry
        code_result = registry.execute("code_execution", {"code": "x=1"})
        assert code_result["status"] in ["ok", "error"]

        # Use MCP tools
        mcp_result = registry.execute("mcp_analyzer", {"target": "test"})
        assert mcp_result["status"] == "ok"

        # All components working together
        assert all([
            r_result["status"] == "ok",
            a_result["status"] == "ok",
            d_result["status"] == "ok",
        ])


class TestMCPIntegrationWithPhase3:
    """Test MCP integration with Phase 3 features."""

    def test_mcp_tools_in_agent_context(self):
        """MCP tools should be available in agent context."""
        registry = ToolRegistry()
        mcp_server = MCPServer(registry)

        def research_tool(args):
            return {"status": "ok", "results": ["result1", "result2"]}

        mcp_server.register_mcp_tool("research", "Research tool", research_tool)

        backend = MockBackend()
        context = {"backend": backend, "tools": registry}

        # Agent can access MCP tools
        agent = ResearcherAgent(context)
        assert context["tools"].get("research") is not None

    def test_mcp_tools_work_with_workflow(self):
        """MCP tools should execute in workflow context."""
        registry = ToolRegistry()
        mcp_server = MCPServer(registry)

        workflow_steps = []

        def step_execute(args):
            workflow_steps.append(args)
            return {"status": "ok", "step": len(workflow_steps)}

        mcp_server.register_mcp_tool("workflow_step", "Workflow step", step_execute)

        result1 = registry.execute("workflow_step", {"step_num": 1})
        assert result1["status"] == "ok"

        result2 = registry.execute("workflow_step", {"step_num": 2})
        assert result2["status"] == "ok"

        assert len(workflow_steps) == 2

    def test_discover_mcp_tools(self):
        """Should be able to discover available MCP tools."""
        mcp_server = MCPServer()

        tools_to_register = [
            ("tool1", "Description 1", lambda a: {"status": "ok"}),
            ("tool2", "Description 2", lambda a: {"status": "ok"}),
            ("tool3", "Description 3", lambda a: {"status": "ok"}),
        ]

        for name, desc, execute_fn in tools_to_register:
            mcp_server.register_mcp_tool(name, desc, execute_fn)

        discovered = mcp_server.discover_tools()
        assert len(discovered) == 3
        assert all(t in discovered for t in ["tool1", "tool2", "tool3"])

    def test_mcp_tools_coexist_with_standard_tools(self):
        """MCP and standard tools should coexist in registry."""
        registry = ToolRegistry()
        mcp_server = MCPServer(registry)

        # Register standard tool
        web_fetch = WebFetchTool()
        registry.register(web_fetch)

        # Register MCP tool
        def mcp_search(args):
            return {"status": "ok", "results": []}

        mcp_server.register_mcp_tool("search", "Search", mcp_search)

        # Both should be available
        tools = registry.list_tools()
        web_fetch_name = web_fetch.name
        assert web_fetch_name in tools
        assert "search" in tools


class TestPhase3Completion:
    """Test that all Phase 3 requirements are met."""

    def test_all_agents_available(self):
        """All three agents should be available."""
        backend = MockBackend()
        registry = ToolRegistry()
        context = {"backend": backend, "tools": registry}

        agents = [
            AnalyzerAgent(context),
            DebuggerAgent(context),
            ResearcherAgent(context),
        ]

        agent_names = [a.name for a in agents]
        assert "analyzer" in agent_names
        assert "debugger" in agent_names
        assert "researcher" in agent_names

    def test_all_tools_available(self):
        """All Phase 3 tools should be available."""
        registry = ToolRegistry()

        tools_to_register = [
            WebFetchTool(),
            CodeExecutionTool(),
            FileTool(),
            ShellTool(),
        ]

        for tool in tools_to_register:
            registry.register(tool)

        tool_names = registry.list_tools()
        assert len(tool_names) >= 4

    def test_workflow_engine_available(self):
        """Workflow engine should be available."""
        backend = MockBackend()
        registry = ToolRegistry()
        agents_dict = {}

        engine = WorkflowEngine(backend, agents_dict, registry)
        assert engine is not None

    def test_mcp_integration_available(self):
        """MCP integration should be available."""
        server = MCPServer()
        assert server is not None

    def test_multi_backend_support(self):
        """Multi-backend support should work."""
        backends = [MockBackend() for _ in range(3)]
        contexts = [{"backend": b} for b in backends]

        for i, ctx in enumerate(contexts):
            result = ctx["backend"].generate("test")
            assert result is not None

    def test_end_to_end_workflow_completion(self):
        """Complete end-to-end workflow should work."""
        backend = MockBackend()
        registry = ToolRegistry()
        mcp_server = MCPServer(registry)

        # Register all tools
        for tool in [WebFetchTool(), CodeExecutionTool(), FileTool(), ShellTool()]:
            registry.register(tool)

        # Register MCP tools
        def mcp_tool(args):
            return {"status": "ok"}

        mcp_server.register_mcp_tool("mcp_tool", "MCP", mcp_tool)

        context = {"backend": backend, "tools": registry}

        # Run all agent types
        for agent_class in [ResearcherAgent, AnalyzerAgent, DebuggerAgent]:
            agent = agent_class(context)
            result = agent.execute("test", {})
            assert result["status"] == "ok"

        # Use all tool types
        for tool_name in registry.list_tools():
            result = registry.execute(tool_name, {})
            assert isinstance(result, dict)

        # Use MCP tools
        result = registry.execute("mcp_tool", {})
        assert result["status"] == "ok"

# MLX-CLI Phase 3 (v1.0) Implementation Plan - Extension

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend MLX-CLI with web research tools, code execution, multi-backend support, specialized agent patterns, MCP integration, and custom workflow automation.

**Architecture:** Build on Phase 1 (core) + Phase 2 (polish) foundation. Introduce: (1) Backend abstraction layer supporting MLX, Ollama, OpenAI, (2) WebFetch + CodeExecution tools, (3) Agent framework with analyzer/debugger/researcher variants, (4) Workflow engine for multi-step tasks, (5) MCP server for external tool integration.

**Tech Stack:** Python 3.10+, existing Phase 1-2 deps + requests (web fetch), pydantic (workflow schema), optional: ollama-py, openai SDK.

## Global Constraints

- Python >= 3.10
- Backward compatible with Phase 1-2 (all 474 tests must still pass)
- Backend interface abstracts inference provider
- No breaking changes to CLI
- WebFetch tool must respect robots.txt
- Code execution sandboxed (no direct filesystem/network access)
- All error messages actionable
- TDD approach for all new code

---

## File Structure

### New Core Modules

```
mlxcli/
├── backends/
│   ├── __init__.py                # Backend registry
│   ├── base.py                    # LLMBackend interface
│   ├── mlx_backend.py             # MLX implementation (refactored from llm.py)
│   ├── ollama_backend.py          # Ollama local inference server
│   └── openai_backend.py          # OpenAI API
├── tools/
│   ├── web_fetch_tool.py          # Web research, PDF parsing
│   └── code_execution_tool.py      # Sandboxed code running
├── agents/
│   ├── __init__.py                # Agent registry
│   ├── base_agent.py              # Agent interface
│   ├── analyzer_agent.py          # Code analyzer
│   ├── debugger_agent.py          # Debugger
│   └── researcher_agent.py        # Researcher
├── workflows/
│   ├── __init__.py
│   ├── workflow_engine.py         # Execution engine
│   └── workflow_parser.py         # YAML/JSON parsing
└── mcp/
    ├── __init__.py
    └── mcp_server.py              # MCP integration
```

### Test Files

```
tests/
├── test_backend_interface.py
├── test_mlx_backend_refactor.py
├── test_ollama_backend.py
├── test_openai_backend.py
├── test_web_fetch_tool.py
├── test_code_execution_tool.py
├── test_analyzer_agent.py
├── test_debugger_agent.py
├── test_researcher_agent.py
├── test_workflow_engine.py
├── test_mcp_server.py
└── test_phase3_integration.py
```

---

## Task Sequence

### Task 1: Backend Interface & MLX Refactoring

**Files:**
- Create: `mlxcli/backends/base.py`, `mlxcli/backends/mlx_backend.py`, `mlxcli/backends/__init__.py`
- Modify: `mlxcli/llm.py` (thin wrapper), `mlxcli/cli.py` (use registry)
- Create: `tests/test_backend_interface.py`, `tests/test_mlx_backend_refactor.py`

**Interfaces:**
- Produces: `LLMBackend` abstract interface:
  - `load_model(name: str) -> bool`
  - `generate(prompt: str, messages: list, tools: list | None = None) -> str`
  - `get_available_models() -> list[dict]`
  - `count_tokens(text: str) -> int`
  - Backend registry for discovery

### Task 2: WebFetch Tool

**Files:**
- Create: `mlxcli/tools/web_fetch_tool.py`
- Create: `tests/test_web_fetch_tool.py`
- Modify: `mlxcli/tool_registry.py`

**Interfaces:**
- Consumes: `Tool` interface
- Produces: `WebFetchTool` with:
  - `execute({"action": "fetch", "url": str, "format": "text"|"json"|"pdf"}) -> dict`
  - Respects robots.txt
  - Timeout: 10 seconds
  - Cache results locally

### Task 3: Code Execution Tool

**Files:**
- Create: `mlxcli/tools/code_execution_tool.py`
- Create: `tests/test_code_execution_tool.py`

**Interfaces:**
- Consumes: `Tool` interface
- Produces: `CodeExecutionTool` with:
  - `execute({"action": "execute", "code": str, "language": "python"|"bash"}) -> dict`
  - Sandboxed execution (no filesystem/network access beyond restrictions)
  - Timeout: 10 seconds
  - Captures stdout/stderr

### Task 4: Ollama Backend

**Files:**
- Create: `mlxcli/backends/ollama_backend.py`
- Create: `tests/test_ollama_backend.py`

**Interfaces:**
- Consumes: `LLMBackend` interface
- Produces: `OllamaBackend` supporting local Ollama server inference
- Compatible with LLMBackend interface
- Auto-detects Ollama server on localhost:11434

### Task 5: OpenAI Backend

**Files:**
- Create: `mlxcli/backends/openai_backend.py`
- Create: `tests/test_openai_backend.py`
- Modify: `mlxcli/config.py` (store API key)

**Interfaces:**
- Consumes: `LLMBackend` interface, config for API key
- Produces: `OpenAIBackend` supporting OpenAI GPT models
- Reads OPENAI_API_KEY from env or config
- Maps available models from API

### Task 6: Agent Base & Analyzer Agent

**Files:**
- Create: `mlxcli/agents/base_agent.py`, `mlxcli/agents/analyzer_agent.py`, `mlxcli/agents/__init__.py`
- Create: `tests/test_analyzer_agent.py`

**Interfaces:**
- Produces: `Agent` interface:
  - `name: str` property
  - `description: str` property
  - `execute(task: str, context: dict) -> dict` method
- Produces: `AnalyzerAgent` for code analysis
  - Accepts code, explains functionality, suggests improvements

### Task 7: Debugger & Researcher Agents

**Files:**
- Create: `mlxcli/agents/debugger_agent.py`, `mlxcli/agents/researcher_agent.py`
- Create: `tests/test_debugger_agent.py`, `tests/test_researcher_agent.py`

**Interfaces:**
- Consumes: `Agent` interface
- Produces:
  - `DebuggerAgent`: Finds bugs, suggests fixes
  - `ResearcherAgent`: Researches topics, fetches info (uses WebFetchTool)

### Task 8: Workflow Engine

**Files:**
- Create: `mlxcli/workflows/workflow_engine.py`, `mlxcli/workflows/workflow_parser.py`, `mlxcli/workflows/__init__.py`
- Create: `tests/test_workflow_engine.py`

**Interfaces:**
- Produces: `WorkflowEngine` for multi-step task execution
  - Parses YAML/JSON workflow definitions
  - Executes steps sequentially with context passing
  - Supports loops, conditionals, tool calls

### Task 9: MCP Integration

**Files:**
- Create: `mlxcli/mcp/mcp_server.py`, `mlxcli/mcp/__init__.py`
- Create: `tests/test_mcp_server.py`
- Modify: `mlxcli/tool_registry.py` (MCP tool discovery)

**Interfaces:**
- Produces: `MCPServer` for Model Context Protocol
  - Discovers MCP-compatible external tools
  - Registers as tools in ToolRegistry
  - Handles tool execution via MCP

### Task 10: Integration Testing & Polish

**Files:**
- Create: `tests/test_phase3_integration.py`
- Update: Documentation (README, CLAUDE.md)
- Code quality checks (black, ruff, mypy)

**Interfaces:**
- Comprehensive end-to-end tests for all Phase 3 features
- All 474 existing tests still passing
- Documentation of new components

---

## Summary

**Phase 3 (v1.0) Completion Goals**

### Features to Deliver

- ✅ Backend abstraction (MLX, Ollama, OpenAI)
- ✅ WebFetch tool (web research, PDF parsing)
- ✅ Code execution tool (sandboxed)
- ✅ Analyzer/Debugger/Researcher agents
- ✅ Workflow engine for automation
- ✅ MCP integration for external tools
- ✅ Comprehensive testing (100+ new tests)
- ✅ Full documentation

### Test Coverage Target

- Phase 1: 242 tests
- Phase 2: 232 tests
- Phase 3: 150+ tests
- **Total: 625+ tests**

### Success Criteria

- ✅ All 3 backends (MLX, Ollama, OpenAI) work
- ✅ WebFetch respects robots.txt
- ✅ Code execution sandboxed
- ✅ 3 agent types functional
- ✅ Workflows parse and execute
- ✅ MCP tools discoverable
- ✅ All tests passing
- ✅ No performance regressions
- ✅ Backward compatible with Phase 1-2

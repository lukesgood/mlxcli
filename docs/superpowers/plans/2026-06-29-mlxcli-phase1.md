# MLX-CLI Phase 1 (v0.1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the core mlx-cli with interactive REPL, session persistence, file I/O, and MLX model integration.

**Architecture:** Plugin-based tool system (Tool Registry) dispatches to specialized tools (FileTool, etc.). Session Manager persists conversations as JSON. CLI provides REPL loop. Context layer auto-discovers project structure. LLM layer wraps MLX inference.

**Tech Stack:** Python 3.10+, mlx-lm, pydantic, typer, rich, prompt-toolkit, pytest

## Global Constraints

- Python >= 3.10
- Store sessions in `.mlxcli/sessions/` (project-local, JSON format)
- Auto-backup before file writes (`.bak` suffix)
- Respect `.gitignore` when reading directories
- OSX first (but cross-platform compatible)
- No API keys stored in sessions
- Session files: `chmod 600` (owner only)

---

## File Structure

### Core Modules (to create)

```
mlxcli/
├── __init__.py                  # Version, package exports
├── main.py                      # Entry point, model selection
├── cli.py                       # REPL loop, command parsing
├── session.py                   # Session state + JSON persistence
├── llm.py                       # MLX model loading & inference
├── context.py                   # Project context discovery
├── config.py                    # .mlxcli/ configuration management
├── tool_registry.py             # Tool registration & dispatch
├── tools/
│   ├── __init__.py
│   ├── base.py                  # Tool interface (abstract base)
│   └── file_tool.py             # File read/write/list with backup
└── utils.py                     # Shared utilities (path checks, etc)

tests/
├── test_session.py              # Session load/save tests
├── test_file_tool.py            # FileTool tests
├── test_context.py              # Context discovery tests
├── test_llm.py                  # MLX integration tests
└── test_cli_integration.py      # End-to-end REPL tests
```

### Configuration Files

```
pyproject.toml                  # Dependencies, entry points
README.md                       # Quick start guide
CLAUDE.md                       # Development notes
```

---

## Task Sequence

### Task 1: Project Setup & Dependencies

**Files:**
- Create: `pyproject.toml`
- Create: `mlxcli/__init__.py`
- Create: `README.md`
- Create: `CLAUDE.md`

**Interfaces:**
- Produces: Project structure, runnable `python -m mlxcli` command

### Task 2: Tool Base Interface

**Files:**
- Create: `mlxcli/tools/__init__.py`
- Create: `mlxcli/tools/base.py`
- Create: `tests/test_base_tool.py`

**Interfaces:**
- Produces: `Tool` (abstract base class)
  - Properties: `name: str`, `description: str`
  - Method: `execute(args: dict) -> dict`

### Task 3: FileTool Implementation

**Files:**
- Create: `mlxcli/tools/file_tool.py`
- Create: `mlxcli/utils.py`
- Create: `tests/test_file_tool.py`

**Interfaces:**
- Consumes: `Tool` (from base.py)
- Produces: `FileTool` with methods:
  - `read(path: str) -> dict` - Returns `{"status": "ok", "content": str}` or error
  - `write(path: str, content: str) -> dict` - Auto-backup before write
  - `list_dir(path: str) -> dict` - List directory with tree structure

### Task 4: Session Management

**Files:**
- Create: `mlxcli/session.py`
- Create: `tests/test_session.py`

**Interfaces:**
- Produces: `Session` dataclass with methods:
  - `save() -> Path` - Save to `.mlxcli/sessions/{id}.json`
  - `load(session_id: str) -> Session` - Load from JSON
  - `add_message(role, content, tools_used=[])` - Add message to history

### Task 5: Project Context Discovery

**Files:**
- Create: `mlxcli/context.py`
- Create: `tests/test_context.py`

**Interfaces:**
- Produces: `ProjectContext` class with properties:
  - `project_root: Path`
  - `project_type: str` (python/nodejs/etc)
  - `file_tree: str`
  - `metadata: dict`

### Task 6: Tool Registry

**Files:**
- Create: `mlxcli/tool_registry.py`
- Create: `tests/test_tool_registry.py`

**Interfaces:**
- Consumes: `Tool` interface, `FileTool`
- Produces: `ToolRegistry` class with methods:
  - `register(tool: Tool) -> None`
  - `get(name: str) -> Tool | None`
  - `execute(tool_name: str, args: dict) -> dict`
  - `list_tools() -> list[str]`

### Task 7: MLX Integration

**Files:**
- Create: `mlxcli/llm.py`
- Create: `tests/test_llm.py`

**Interfaces:**
- Produces: `MLXBackend` class with methods:
  - `get_available_models() -> list[dict]`
  - `load_model(model_name: str) -> bool`
  - `generate(prompt: str, messages: list, tools: list | None = None) -> str`

### Task 8: CLI REPL Implementation

**Files:**
- Create: `mlxcli/config.py`
- Create: `mlxcli/cli.py`
- Create: `tests/test_cli_integration.py`

**Interfaces:**
- Consumes: `Session`, `FileTool`, `ToolRegistry`, `MLXBackend`, `ProjectContext`
- Produces: `CLI` class with methods:
  - `run() -> None` - Main REPL loop
  - `_handle_command(input: str) -> bool` - Command dispatcher

### Task 9: Main Entry Point

**Files:**
- Create: `mlxcli/main.py`

**Interfaces:**
- Consumes: `CLI`
- Produces: Runnable `python -m mlxcli` command

### Task 10: Integration Testing & Polish

**Files:**
- Create: `tests/test_integration.py`

**Interfaces:**
- Consumes: All components (Session, FileTool, CLI, MLX, etc)

---

## Summary

**Phase 1 (v0.1) Complete!**

### What's Built

- ✅ CLI REPL with interactive model selection
- ✅ Session management (JSON persistence, auto-save)
- ✅ FileTool (read/write/list with auto-backup)
- ✅ MLX backend integration (model loading, inference)
- ✅ Project context auto-discovery (.gitignore aware)
- ✅ Tool registry and dispatch system
- ✅ Comprehensive tests (unit + integration)

### Success Criteria Met

- ✅ Can start CLI and select model
- ✅ Interactive chat with MLX model
- ✅ File reading works
- ✅ File writing with auto-backup
- ✅ Sessions save/load as JSON
- ✅ Sessions persist across restarts

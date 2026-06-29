# MLX-CLI Phase 2 (v0.2) Implementation Plan - Polish

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish MLX-CLI with ShellTool, comprehensive error handling, enhanced session/model management, auto-completion, and context optimization.

**Architecture:** Phase 1 foundation remains; Phase 2 adds: (1) ShellTool with command safety gates, (2) Error recovery with graceful degradation, (3) Enhanced CLI commands for model/session management, (4) Readline auto-completion, (5) Token-aware context pruning, (6) Better user feedback and recovery guidance.

**Tech Stack:** Python 3.10+, prompt-toolkit (already in Phase 1), mlx-lm, existing dependencies (no new external deps for Phase 2 core).

## Global Constraints

- Python >= 3.10
- No destructive commands without confirmation (rm, git push, etc.)
- Command execution timeout: 30 seconds default
- Auto-completion via prompt-toolkit readline
- Context trimming respects token budget
- All error messages are actionable (not just "error")
- Session recovery from corrupted files with fallback
- Backward compatible with Phase 1 sessions
- OSX first, cross-platform compatible

---

## File Structure

### Files to Create

```
mlxcli/
├── tools/
│   └── shell_tool.py              # Shell command execution with safety
├── error_handler.py               # Centralized error handling & recovery
├── completion.py                  # Readline auto-completion setup
├── context_manager.py             # Token-aware context pruning

tests/
├── test_shell_tool.py             # ShellTool tests
├── test_error_handler.py          # Error handling tests
├── test_completion.py             # Auto-completion tests
├── test_context_manager.py        # Context pruning tests
├── test_error_scenarios.py        # End-to-end error scenarios
├── test_model_commands.py         # Model command tests
├── test_session_commands.py       # Session command tests
```

### Files to Modify

```
mlxcli/
├── cli.py                         # Enhanced commands, better errors
├── llm.py                         # Better error messages
├── tool_registry.py               # Add ShellTool to registry
├── session.py                     # Recovery from corruption
├── utils.py                       # Add command validation

tests/
├── test_cli_integration.py        # Add new command tests
└── test_integration.py            # Add error scenario tests
```

---

## Task Sequence

### Task 1: ShellTool Implementation

**Files:**
- Create: `mlxcli/tools/shell_tool.py`
- Create: `tests/test_shell_tool.py`
- Modify: `mlxcli/utils.py` (add command validation)

**Interfaces:**
- Consumes: `Tool` interface from Phase 1
- Produces: `ShellTool` class with methods:
  - `execute(args: dict) -> dict` - Execute shell command with safety
  - `_is_destructive(cmd: str) -> bool` - Check if command is dangerous
  - `_preview_command(cmd: str) -> str` - Show what will run

### Task 2: Error Handler & Recovery System

**Files:**
- Create: `mlxcli/error_handler.py`
- Create: `tests/test_error_handler.py`
- Modify: `mlxcli/llm.py` (use error handler)
- Modify: `mlxcli/session.py` (recovery methods)

**Interfaces:**
- Consumes: Session, config
- Produces: `ErrorHandler` class with:
  - `handle_error(error_type: str, context: dict) -> dict` - Central error handling
  - `suggest_recovery(error: Exception) -> str` - Recovery suggestions
  - `log_error(error: Exception, context: dict) -> None` - Error logging

### Task 3: Enhanced Model Management Commands

**Files:**
- Modify: `mlxcli/cli.py` (new /model command)
- Modify: `mlxcli/llm.py` (add model info methods)
- Create: `tests/test_model_commands.py`

**Interfaces:**
- Consumes: MLXBackend, CLI
- Produces: Enhanced CLI commands:
  - `/model` - Show current model with details
  - `/model list` - List available models
  - `/model switch <name>` - Switch to different model

### Task 4: Session Management Enhancements

**Files:**
- Modify: `mlxcli/cli.py` (enhanced /sessions command)
- Modify: `mlxcli/session.py` (add metadata)
- Create: `tests/test_session_commands.py`

**Interfaces:**
- Consumes: Session, CLI
- Produces: Enhanced session commands:
  - `/sessions` - List with timestamps, message counts
  - `/load <id>` - Resume session
  - `/delete <id>` - Delete session
  - `/info <id>` - Show session details

### Task 5: Readline Auto-Completion

**Files:**
- Create: `mlxcli/completion.py`
- Modify: `mlxcli/cli.py` (integrate completion)
- Create: `tests/test_completion.py`

**Interfaces:**
- Consumes: prompt_toolkit
- Produces: `CompleterSetup` with word completers for:
  - Commands (/help, /model, /sessions, etc.)
  - File paths (@file, @dir)
  - Model names (after /model switch)

### Task 6: Token-Aware Context Manager

**Files:**
- Create: `mlxcli/context_manager.py`
- Modify: `mlxcli/llm.py` (use context manager)
- Create: `tests/test_context_manager.py`

**Interfaces:**
- Consumes: Session, MLXBackend
- Produces: `ContextManager` class with:
  - `trim_to_budget(messages: list, token_budget: int) -> list`
  - `get_context_size(text: str) -> int`

### Task 7: Error Scenarios Integration Testing

**Files:**
- Create: `tests/test_error_scenarios.py`
- Modify: test files for ShellTool integration

**Interfaces:**
- Consumes: All Phase 2 components
- Produces: End-to-end error scenario tests

### Task 8: Code Quality & Documentation

**Files:**
- Run code quality checks (black, ruff, mypy)
- Update README.md with Phase 2 features
- Update CLAUDE.md with new components

**Steps:**
- Format with black
- Lint with ruff
- Type check with mypy
- Run full test suite
- Update documentation

---

## Summary

**Phase 2 (v0.2) Completion Goals**

### Delivered

- ✅ ShellTool with command safety gates
- ✅ Centralized error handling with recovery strategies
- ✅ Enhanced model management commands
- ✅ Improved session management UI
- ✅ Readline auto-completion
- ✅ Token-aware context management
- ✅ Comprehensive error scenario tests
- ✅ Code quality (black, ruff, type hints)
- ✅ Updated documentation

### Test Coverage

- 8 new test files
- ~500+ new tests
- All existing tests still passing
- Error scenarios covered

### Success Criteria

- ✅ ShellTool works with safety guards
- ✅ `/model` command allows mid-session switching
- ✅ `/sessions` shows useful session info
- ✅ Error messages guide users to solutions
- ✅ Auto-completion works for commands, files, models
- ✅ Session recovery from corruption
- ✅ All tests passing
- ✅ No performance regressions

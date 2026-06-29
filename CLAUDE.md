# MLX-CLI Development Guide

**Last Updated**: 2026-06-29  
**Status**: Design Phase Complete, Implementation Underway  
**Language**: Python 3.10+  

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Development Setup](#development-setup)
4. [Core Modules](#core-modules)
5. [Testing Strategy](#testing-strategy)
6. [Session Management](#session-management)
7. [Tool System](#tool-system)
8. [MLX Integration](#mlx-integration)
9. [Error Handling](#error-handling)
10. [Contributing Guidelines](#contributing-guidelines)

---

## Architecture Overview

### System Design

MLX-CLI follows a layered architecture:

```
┌─────────────────────────────┐
│   CLI Interface Layer       │  User interaction (REPL, commands)
├─────────────────────────────┤
│   Session Manager           │  State persistence & recovery
├─────────────────────────────┤
│   Tool Registry             │  Plugin-like tool dispatch
├─────────────────────────────┤
│   LLM Integration (MLX)     │  Model inference & token management
└─────────────────────────────┘
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Local-First** | Full control over LLM, optimized for edge inference |
| **JSON Sessions** | Human-readable, Git-friendly, pure Python |
| **Plugin Tools** | Extensibility without core changes |
| **Pydantic Validation** | Type-safe data handling, automatic validation |
| **Async Support** | Ready for concurrent operations (Phase 2) |

---

## Project Structure

```
mlxcli/
├── mlxcli/
│   ├── __init__.py                 # Package initialization, version
│   ├── main.py                     # CLI entry point (Phase 1)
│   ├── cli.py                      # REPL loop & command handling (Phase 1)
│   ├── session.py                  # Session state & persistence (Phase 1)
│   ├── llm.py                      # MLX integration (Phase 1)
│   ├── context.py                  # Project context discovery (Phase 1)
│   ├── tool_registry.py            # Tool registration & dispatch (Phase 1)
│   ├── config.py                   # Configuration management (Phase 1)
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py                 # Tool interface (Phase 1)
│   │   ├── file_tool.py            # File operations (Phase 1)
│   │   └── shell_tool.py           # Shell execution (Phase 2)
│   └── utils.py                    # Utility functions
├── tests/
│   ├── test_project_setup.py       # Setup & structure tests (Phase 1)
│   ├── test_session.py             # Session management tests (Phase 1)
│   ├── test_cli.py                 # CLI tests (Phase 1)
│   └── test_tools.py               # Tool system tests (Phase 1)
├── docs/
│   └── superpowers/
│       └── specs/                  # Design documents
├── pyproject.toml                  # Project metadata & dependencies
├── README.md                       # User guide
├── CLAUDE.md                       # This file
└── .gitignore
```

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip or uv (recommended for speed)
- macOS 13+ (primary target), Linux supported
- Git (for version control)

### Environment Setup

```bash
# Clone repository
git clone https://github.com/mlx-cli/mlxcli.git
cd mlxcli

# Create virtual environment (recommended)
python3.10 -m venv venv
source venv/bin/activate

# Install with development dependencies
pip install -e ".[dev]"

# Or use uv for faster installs
uv pip install -e ".[dev]"
```

### First-Time Development

```bash
# Verify installation
python -c "import mlxcli; print(mlxcli.__version__)"

# Run tests
pytest tests/ -v

# Check code quality
black mlxcli tests --check
ruff check mlxcli tests
mypy mlxcli
```

---

## Core Modules

### 1. `__init__.py` - Package Initialization

**Responsibility**: Expose public API and version

```python
__version__ = "0.1.0"
__all__ = ["__version__", ...]
```

**To Do**:
- Export main CLI function
- Export core classes (Session, Tool, etc.)

---

### 2. `cli.py` - REPL Loop (Phase 1)

**Responsibility**: Interactive command loop and user input handling

**Key Functions**:
- `run_repl()` - Main REPL loop
- `parse_command(input_str)` - Parse `/cmd` commands
- `parse_references(input_str)` - Extract `@file` references
- `format_response(output)` - Pretty-print responses using `rich`

**Architecture**:
```python
class CLI:
    session: Session
    llm: LLMBackend
    tool_registry: ToolRegistry
    
    async def run(self):
        while True:
            user_input = prompt_user()
            await self.handle_input(user_input)
```

---

### 3. `session.py` - Session Management (Phase 1)

**Responsibility**: Conversation state, persistence, and recovery

**Data Model**:
```python
class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime
    tools_used: list[str] = []
    
class Session(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    model: str
    messages: list[Message]
    context: ProjectContext
```

**Key Methods**:
- `save()` - Persist to `.mlxcli/sessions/{id}.json`
- `load(id)` - Load from disk
- `add_message()` - Append message to history
- `get_context()` - Build system prompt from history

**File Permissions**: `chmod 600` (owner read/write only)

---

### 4. `llm.py` - MLX Integration (Phase 1)

**Responsibility**: Model loading, inference, and token management

**Key Functions**:
- `load_model(model_id)` - Load model from cache or download
- `count_tokens(text)` - Estimate tokens before inference
- `infer(prompt, tools)` - Run inference with tool definitions
- `parse_response(response)` - Extract text and tool calls

**Architecture**:
```python
class LLMBackend:
    model: mlx_lm.Model
    tokenizer: mlx_lm.Tokenizer
    
    async def infer(
        self,
        messages: list[Message],
        tools: list[Tool],
        max_tokens: int = 1000,
    ) -> str:
        """Run inference with tool definitions."""
```

**Token Management**:
- Warn if approaching context limit
- Trim oldest messages if necessary
- Respect per-model context windows

---

### 5. `tool_registry.py` - Tool Dispatch (Phase 1)

**Responsibility**: Tool registration, discovery, and execution

**Key Methods**:
- `register(tool)` - Register a new tool
- `get(name)` - Retrieve tool by name
- `execute(name, args)` - Execute tool with arguments
- `get_descriptions()` - Get JSON schema for LLM

**Architecture**:
```python
class ToolRegistry:
    tools: dict[str, Tool]
    
    async def execute(self, tool_name: str, args: dict) -> dict:
        """Execute tool and return result."""
```

---

### 6. `tools/base.py` - Tool Interface (Phase 1)

**Responsibility**: Base class for all tools

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel

class Tool(ABC):
    name: str
    description: str
    
    @abstractmethod
    async def execute(self, args: dict) -> dict:
        """Execute tool with arguments."""
        pass
    
    def schema(self) -> dict:
        """Return JSON schema for LLM."""
        pass
```

---

### 7. `tools/file_tool.py` - File Operations (Phase 1)

**Responsibility**: Safe file read/write with backups

**Operations**:
- `read(path)` - Read file content
- `write(path, content)` - Write with `.bak` backup
- `list_dir(path)` - List directory contents

**Safety**:
- Respects `.gitignore`
- Cannot write outside project
- Creates backups before writes
- Respects file permissions

**Example**:
```python
class FileTool(Tool):
    name = "FileTool"
    description = "Read/write files with auto-backup"
    
    async def execute(self, args: dict) -> dict:
        operation = args.get("operation")
        if operation == "read":
            return self.read(args["path"])
        elif operation == "write":
            return self.write(args["path"], args["content"])
```

---

### 8. `context.py` - Project Context (Phase 1)

**Responsibility**: Auto-discover and inject project context

**Discovery**:
- Read `README.md` for project purpose
- Parse `pyproject.toml` or `package.json`
- Respect `.gitignore`
- Build directory structure

**Injection**:
- Automatically included in system prompt
- Updated per session
- Cached for performance

**Data Model**:
```python
class ProjectContext(BaseModel):
    readme: str | None
    files_referenced: list[str]
    project_structure: list[str]
    project_info: dict
```

---

## Testing Strategy

### Test Organization

```
tests/
├── test_project_setup.py      # Verify structure (Phase 1)
├── test_session.py            # Session management (Phase 1)
├── test_cli.py                # CLI commands (Phase 1)
├── test_tools.py              # Tool execution (Phase 1)
└── conftest.py                # Fixtures & utilities
```

### Test-Driven Development

All features follow TDD:

1. **Write failing tests** - Define desired behavior
2. **Implement minimal code** - Make tests pass
3. **Refactor** - Improve without breaking tests
4. **Commit** - Clean git history

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_session.py -v

# Run with coverage
pytest tests/ --cov=mlxcli

# Run async tests
pytest tests/ -v -m asyncio
```

### Key Test Categories

| Category | Purpose |
|----------|---------|
| **Unit** | Test individual functions in isolation |
| **Integration** | Test module interactions |
| **Fixture** | Test with mock data and side effects |
| **Async** | Test async/await patterns |

---

## Session Management

### Session Lifecycle

```
1. Create Session
   └─ Assign unique ID
   └─ Set working directory
   └─ Initialize empty message list

2. Add Messages
   └─ User input → Message(role="user")
   └─ LLM response → Message(role="assistant")
   └─ Tool calls → Tracked in message metadata

3. Auto-Save
   └─ After each LLM response
   └─ Write to .mlxcli/sessions/session_{id}.json
   └─ Set permissions: chmod 600

4. Recover
   └─ On exit: Final state persisted
   └─ On restart: Can load previous sessions
```

### Session File Example

```json
{
  "id": "session_001",
  "created_at": "2026-06-29T10:30:00Z",
  "updated_at": "2026-06-29T10:45:00Z",
  "model": "meta-llama/Llama-2-7b-hf",
  "working_directory": "/Users/luke/myproject",
  "messages": [
    {
      "role": "user",
      "content": "Summarize the project",
      "timestamp": "2026-06-29T10:30:05Z"
    }
  ],
  "context": {
    "files_referenced": [],
    "project_structure": ["src/", "tests/"],
    "project_info": {"type": "python"}
  }
}
```

### Backup & Recovery

- **Automatic Backups**: `.mlxcli/sessions/session_{id}.json.bak`
- **Corruption Recovery**: Restore from `.bak` if JSON invalid
- **Disk Full**: Clear old sessions with user confirmation

---

## Tool System

### Tool Interface

All tools inherit from `Tool`:

```python
class Tool(ABC):
    name: str
    description: str
    
    @abstractmethod
    async def execute(self, args: dict) -> dict:
        """Execute tool."""
        pass
    
    def schema(self) -> dict:
        """JSON schema for LLM."""
        pass
```

### Tool Registration

```python
registry = ToolRegistry()
registry.register(FileTool())
registry.register(ShellTool())

# Get descriptions for LLM
tool_descriptions = registry.get_descriptions()
```

### Tool Execution

```python
# LLM requests tool execution
tool_result = await registry.execute("FileTool", {
    "operation": "read",
    "path": "README.md"
})
```

### Future Tools

**Phase 2**:
- `ShellTool` - Execute shell commands safely
- `WebFetch` - Fetch and parse web content

**Phase 3**:
- `CodeExecution` - Run Python in sandbox
- `CustomTools` - User-defined tool plugins
- `MCP Support` - Model Context Protocol integration

---

## MLX Integration

### Model Loading

```python
from mlx_lm import load

model, tokenizer = load("meta-llama/Llama-2-7b-hf")
```

### Inference Loop

```python
async def infer(prompt: str, tools: list[Tool]) -> str:
    # Count tokens
    token_count = count_tokens(prompt)
    
    # Warn if approaching limit
    if token_count > MODEL_CONTEXT_LIMIT * 0.8:
        warn("Approaching context limit")
    
    # Build tool definitions for LLM
    tool_defs = [tool.schema() for tool in tools]
    
    # Run inference
    response = model.generate(
        prompt,
        max_tokens=1000,
        tools=tool_defs,
    )
    
    # Parse and execute tool calls if any
    calls = parse_tool_calls(response)
    for call in calls:
        result = await registry.execute(call.name, call.args)
        # Feed result back for follow-up
    
    return response.text
```

### Token Management

- **Pre-Inference**: Count tokens in prompt + history
- **Context Limit**: Warn if >80% full
- **Trimming**: Remove oldest messages if necessary
- **Per-Model Config**: Different limits for different models

---

## Error Handling

### MLX Errors

| Error | Handling |
|-------|----------|
| Model not found | Suggest download with size |
| VRAM insufficient | Suggest smaller model |
| Load timeout | Check disk space |
| Inference timeout | Retry with simpler prompt |

### File Errors

| Error | Handling |
|-------|----------|
| Permission denied | Show clear message + suggest location |
| File not found | List similar files |
| Write failed | Confirm backup exists |
| Path outside project | Require explicit confirmation |

### Session Errors

| Error | Handling |
|-------|----------|
| Corrupted JSON | Restore from `.bak` |
| Session not found | List available sessions |
| Disk full | Clear old sessions (confirm) |

### Tool Errors

| Error | Handling |
|-------|----------|
| Tool not found | List available tools |
| Argument validation failed | Show schema |
| Execution failed | Return error to LLM + retry |

---

## Contributing Guidelines

### Code Style

- **Formatting**: Use `black` (line length: 88)
- **Linting**: Use `ruff` (see `pyproject.toml` for rules)
- **Type Hints**: Full type annotations (mypy)
- **Docstrings**: Google-style for all public functions

### Commit Guidelines

```bash
# Follow conventional commits
git commit -m "feat: add file read operation"
git commit -m "fix: handle permission errors in file tool"
git commit -m "test: add session persistence tests"
git commit -m "docs: update API reference"
```

### Branch Workflow

1. Create feature branch: `git checkout -b feat/feature-name`
2. Make changes and commit
3. Run tests: `pytest tests/ -v`
4. Check code quality: `black`, `ruff`, `mypy`
5. Create PR with clear description
6. Address review feedback
7. Merge when approved

### Pull Request Template

```markdown
## Description
Brief description of what this PR does

## Changes
- Bullet point of changes
- Another change

## Tests
- [x] Added tests for new feature
- [x] All tests passing

## Checklist
- [ ] Code formatted with black
- [ ] Linted with ruff
- [ ] Type checked with mypy
- [ ] Tests passing
```

### Adding New Modules

1. Create module file: `mlxcli/new_module.py`
2. Add docstring explaining purpose
3. Write failing tests first
4. Implement module
5. Update `__init__.py` exports
6. Add documentation in this file

---

## Implementation Phases

### Phase 1: Core (v0.1)

**Goals**: Working CLI with basic MLX integration

**Tasks**:
- [x] Project setup & dependencies
- [ ] CLI REPL loop
- [ ] Session management
- [ ] FileTool implementation
- [ ] MLX integration
- [ ] Project context discovery

**Completion**: All core features working, tests passing

---

### Phase 2: Polish (v0.2)

**Goals**: Shell integration, error handling, UI improvements

**Tasks**:
- [ ] ShellTool with safety guards
- [ ] Session switching UI
- [ ] Model management commands
- [ ] Command auto-completion
- [ ] Better error messages

**Completion**: Smooth user experience, robust error handling

---

### Phase 3: Extension (v1.0)

**Goals**: Advanced tools and multi-backend support

**Tasks**:
- [ ] WebFetch tool
- [ ] Code execution sandbox
- [ ] Plugin system
- [ ] MCP support
- [ ] Ollama backend
- [ ] OpenAI backend

**Completion**: Full feature set, extensible architecture

---

## Resources

### Official Documentation

- [MLX Documentation](https://ml-explore.github.io/mlx/)
- [Typer CLI Framework](https://typer.tiangolo.com/)
- [Pydantic v2](https://docs.pydantic.dev/)
- [Rich Terminal Formatting](https://rich.readthedocs.io/)

### Related Projects

- [kiro-cli](https://github.com/kiro-cli/kiro) - Inspiration for CLI design
- [opencli.co](https://opencli.co/) - Provider-agnostic CLI (contrast)
- [MLX Examples](https://github.com/ml-explore/mlx-examples) - MLX usage patterns

---

## Troubleshooting

### Common Issues

**Q: Tests fail with "No module named mlxcli"**  
A: Install in dev mode: `pip install -e .`

**Q: Type errors with mypy**  
A: Run `mypy mlxcli` to see detailed errors

**Q: Black formats code differently**  
A: Rerun `black mlxcli` to normalize formatting

**Q: pytest not finding tests**  
A: Ensure `tests/` has `__init__.py` if needed (usually not)

---

**Last updated**: 2026-06-29  
**Maintainers**: MLX CLI Contributors  
**Status**: Implementation in progress

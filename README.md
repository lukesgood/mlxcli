# MLX-CLI: Terminal LLM Chat with Local MLX Backend

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)

A terminal-based LLM CLI tool that runs MLX models locally on macOS, inspired by kiro-cli. Execute AI-assisted workflows directly from your terminal with interactive chat, file operations, and shell integration.

## Features

### Core Features
- **Local LLM Inference**: Run open-source models (Llama, Mistral, etc.) locally using MLX
- **Interactive Chat**: Real-time conversation with history and session persistence
- **File Operations**: Read/write files with automatic backups (`.bak` suffixes)
- **Shell Integration**: Execute shell commands directly within conversations
- **Project Context**: Automatic discovery and injection of README, .gitignore, and project structure
- **Session Management**: Save and restore conversations as JSON in `.mlxcli/sessions/`
- **Cross-platform**: Works on macOS and Linux (OSX-first development)
- **Type-Safe**: Full Python 3.10+ type hints with pydantic validation

### Phase 3 Features (v1.0)
- **Multi-Backend Support**: Switch seamlessly between MLX, Ollama, and OpenAI backends
- **Specialized Agents**: Analyzer (code analysis), Debugger (error diagnosis), Researcher (knowledge gathering)
- **Advanced Tools**: Web fetch, code execution, extended file operations, shell commands
- **Workflow Engine**: Multi-step workflow execution with context passing and conditionals
- **MCP Integration**: Model Context Protocol support for external tool discovery and registration
- **Agent Chains**: Compose multiple agents for complex reasoning tasks

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/mlx-cli/mlxcli.git
cd mlxcli

# Install in development mode
pip install -e ".[dev]"

# Or install production dependencies
pip install .
```

### First Run

```bash
# Start the CLI
python -m mlxcli

# Select a model from available options
mlx-cli> Select model (1-2) [default: 1]: 1

# Begin interactive chat
mlx-cli> Ask me anything!
```

## Usage Guide

### Starting an Interactive Session

```bash
# Default: start in current directory
python -m mlxcli

# Specify project root
python -m mlxcli --root /path/to/project
python -m mlxcli -r /path/to/project
```

### Basic Commands

```bash
mlx-cli> Hello! What can you help me with?
# Chat normally with the LLM

mlx-cli> /sessions
# List all saved sessions

mlx-cli> /load <session-id>
# Load and resume a previous session

mlx-cli> /model
# Show available models

mlx-cli> /save
# Manually save current session

mlx-cli> /exit
# Exit the CLI
```

### File Operations

Reference files in your project:

```bash
mlx-cli> @README.md Summarize this project
# Loads file content into context

mlx-cli> @src/ Show me the structure
# Show directory listing

mlx-cli> ! python -m pytest tests/ --tb=short
# Execute shell commands directly
```

### Example Workflows

#### 1. Code Review Workflow

```bash
mlx-cli> @src/main.py Review this code for bugs
# Specify file with @ prefix
# Assistant reviews and provides feedback

mlx-cli> @tests/test_main.py Are these tests comprehensive?
# Load related test file for reference
```

#### 2. Project Understanding

```bash
mlx-cli> @README.md @pyproject.toml Tell me about this project
# Load multiple files by repeating @

mlx-cli> @src/ List all Python files
# Works with directories too
```

#### 3. Safe Modifications with Backups

```bash
mlx-cli> @src/config.py Update this config for production
# Write operations automatically create .bak backups

mlx-cli> Revert that change
# You can recover from backups manually
```

### Session Management

Sessions automatically save to `.mlxcli/sessions/`:

```bash
# List sessions
mlx-cli> /sessions
Available sessions:
  abc12345 | claude-3-sonnet | 2024-06-29 10:30
  xyz67890 | claude-3-sonnet | 2024-06-28 14:15

# Resume session
mlx-cli> /load abc12345

# Each session maintains:
# - Conversation history
# - Tool usage logs  
# - Project context
# - Secure permissions (readable only by owner)
```

## Architecture

### v1.0 Multi-Layer Architecture

```
┌────────────────────────────────────────────┐
│        Workflow Engine (Orchestration)     │
├────────────────────────────────────────────┤
│   MCP Server    │   Agent Manager          │
│   (external     │   (Analyzer, Debugger,  │
│    tools)       │    Researcher)           │
├────────────────────────────────────────────┤
│            Multi-Backend Support           │
│   (MLX | Ollama | OpenAI)                  │
├────────────────────────────────────────────┤
│   Tool Registry (Web Fetch, Code Exec)     │
├────────────────────────────────────────────┤
│   CLI Interface | Session Manager | Config │
└────────────────────────────────────────────┘
```

### Phase 3 Additions
- **Agents Layer**: Specialized agents for different reasoning tasks
- **Workflow Engine**: Multi-step execution with context passing
- **MCP Integration**: External tool discovery and registration
- **Multi-Backend**: Seamless switching between different LLM providers

### Core Modules

**Phase 1-2 (Foundation)**

| Module | Purpose |
|--------|---------|
| `cli.py` | REPL loop and command parsing |
| `session.py` | Conversation state and persistence |
| `llm.py` | MLX model loading and inference |
| `tool_registry.py` | Tool registration and dispatch |
| `tools/base.py` | Tool interface and base classes |
| `tools/file_tool.py` | File read/write with auto-backup |
| `tools/shell_tool.py` | Shell command execution |
| `context.py` | Project context auto-discovery |

**Phase 3 (v1.0)**

| Module | Purpose |
|--------|---------|
| `backends/base.py` | Multi-backend abstraction layer |
| `backends/mlx_backend.py` | MLX backend implementation |
| `backends/ollama_backend.py` | Ollama backend implementation |
| `backends/openai_backend.py` | OpenAI backend implementation |
| `agents/base_agent.py` | Agent interface and base classes |
| `agents/analyzer_agent.py` | Code analysis specialized agent |
| `agents/debugger_agent.py` | Error diagnosis specialized agent |
| `agents/researcher_agent.py` | Knowledge gathering specialized agent |
| `tools/web_fetch_tool.py` | Web content fetching |
| `tools/code_execution_tool.py` | Safe code execution |
| `workflows/workflow_engine.py` | Multi-step workflow execution |
| `workflows/workflow_parser.py` | YAML/JSON workflow parsing |
| `mcp/mcp_server.py` | MCP protocol integration |

## Session Persistence

Sessions are stored in `.mlxcli/sessions/` as JSON files with:

- Conversation history
- Tool execution logs
- Project context
- Timestamps and metadata
- File permissions: `600` (owner read/write only)

No API keys are stored in sessions.

## Commands

| Command | Purpose |
|---------|---------|
| `/chat` | Start new conversation |
| `/model` | List or change models |
| `/save` | Explicitly save session |
| `/load <id>` | Load previous session |
| `/sessions` | List saved sessions |
| `/help` | Show help |
| `/exit` | Exit CLI |

### File References

- `@file_path` - Load file into context
- `@dir_path` - Show directory tree

### Shell Escape

- `! <cmd>` - Execute shell command

## Configuration

### Environment Variables

```bash
# Optional: Specify MLX cache directory
export MLX_CACHE_DIR=~/.cache/mlx_lm

# Optional: Set default model
export MLX_CLI_DEFAULT_MODEL="meta-llama/Llama-2-7b-hf"
```

### Project-Local Sessions

Sessions are stored in `.mlxcli/sessions/` relative to your project root.

## Security

- **File Access**: Read any file in project; write only within project with confirmation
- **Shell Commands**: Show command preview; require approval first time
- **Session Privacy**: Files readable only by owner (`chmod 600`)
- **No Secrets**: API keys never stored in sessions

## Development

See [CLAUDE.md](CLAUDE.md) for detailed architecture, design decisions, and contribution guidelines.

### Setup

```bash
# Clone and enter directory
git clone https://github.com/mlx-cli/mlxcli.git
cd mlxcli

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install in development mode with dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run integration tests only
pytest tests/test_integration.py -v

# Run with coverage
pytest tests/ -v --cov=mlxcli --cov-report=html

# Run specific test class
pytest tests/test_session.py::TestSessionPersistence -v
```

### Code Quality

The project follows strict code quality standards:

```bash
# Format code with black (100 char lines)
black mlxcli tests --line-length 100

# Lint and auto-fix issues
ruff check mlxcli tests --fix

# Type checking (note: run against local code only)
mypy mlxcli --ignore-missing-imports --python-version 3.10
```

### Project Structure

```
mlxcli/
├── mlxcli/
│   ├── __init__.py                # Package metadata
│   ├── main.py                    # Entry point
│   ├── cli.py                     # REPL interface
│   ├── session.py                 # State management
│   ├── context.py                 # Project context discovery
│   ├── tool_registry.py           # Tool dispatch system
│   ├── utils.py                   # Utilities and helpers
│   ├── config.py                  # Configuration
│   ├── backends/                  # Multi-backend support
│   │   ├── base.py                # Backend abstraction
│   │   ├── mlx_backend.py         # MLX implementation
│   │   ├── ollama_backend.py      # Ollama implementation
│   │   └── openai_backend.py      # OpenAI implementation
│   ├── agents/                    # Specialized agents
│   │   ├── base_agent.py          # Agent interface
│   │   ├── analyzer_agent.py      # Code analysis
│   │   ├── debugger_agent.py      # Error diagnosis
│   │   └── researcher_agent.py    # Knowledge gathering
│   ├── tools/
│   │   ├── base.py                # Tool interface
│   │   ├── file_tool.py           # File operations
│   │   ├── shell_tool.py          # Shell execution
│   │   ├── web_fetch_tool.py      # Web content
│   │   └── code_execution_tool.py # Code execution
│   ├── workflows/                 # Workflow engine
│   │   ├── workflow_engine.py     # Execution engine
│   │   └── workflow_parser.py     # YAML/JSON parser
│   └── mcp/                       # MCP integration
│       ├── __init__.py            # Package init
│       └── mcp_server.py          # MCP server
├── tests/
│   ├── test_*.py                  # Unit tests (800+ tests)
│   ├── test_phase3_integration.py # Phase 3 integration (34 tests)
│   └── test_mcp_server.py         # MCP tests (35 tests)
├── docs/                          # Documentation
├── pyproject.toml                 # Project config
├── README.md                      # This file
└── CLAUDE.md                      # Development guide
```

### Test Coverage

**v1.0 test suite: 870+ tests**

- **Phase 1**: 242 tests (core components)
- **Phase 2**: 232 tests (advanced features)
- **Phase 3**: 104 tests (agents, workflows, MCP)

**Coverage areas**:
  - Session persistence and recovery
  - Tool registry and execution
  - File operations with backups
  - Project context discovery
  - Shell command execution with safety gates
  - Error handling and recovery strategies
  - Model management and switching across backends
  - Multi-backend support (MLX, Ollama, OpenAI)
  - Specialized agents (Analyzer, Debugger, Researcher)
  - Workflow engine with multi-step execution
  - MCP tool discovery and registration
  - Agent chaining and composition
  - Complex multi-operation workflows
  - Full end-to-end scenarios

### Version Requirements

- **Python**: 3.10 or higher (3.10, 3.11, 3.12 tested)
- **Black**: 23.0+
- **Ruff**: 0.1.0+
- **MyPy**: 1.0+
- **Pytest**: 7.0+

## Requirements

- **Python**: 3.10 or higher
- **MLX**: Compatible with macOS 13+
- **Dependencies**: See `pyproject.toml`

## Advanced Features (v0.2)

### Shell Command Execution
Execute shell commands with auto-confirmation for dangerous operations:

```bash
mlx-cli> ! ls -la
mlx-cli> ! python script.py

# Dangerous commands require explicit confirmation:
mlx-cli> ! rm -rf /tmp
⚠️  Potentially dangerous command: rm -rf /tmp
Set confirmed=True to override
```

### Enhanced Model Management
Switch between models within the same session:

```bash
mlx-cli> /model list
📦 Available Models:
  1. meta-llama/Llama-2-7b-hf
     Llama 2 7B (good for most use cases)
     Size: ~7GB

mlx-cli> /model switch meta-llama/Llama-2-13b-hf
✓ Switched to meta-llama/Llama-2-13b-hf
```

### Improved Session Management
Better session organization and info:

```bash
mlx-cli> /sessions
📋 Saved Sessions:

  1. session_abc123
     Model: meta-llama/Llama-2-7b-hf
     Messages: 12
     Last: "How does machine learning work? ..."
     Updated: 2026-06-30T15:45:00

mlx-cli> /delete session_abc123
```

### Command Auto-Completion
Tab completion for commands, files, and models:

```bash
mlx-cli> /mod[TAB]
/model           /model list      /model switch

mlx-cli> @REA[TAB]
@README.md       @README.txt

History: Ctrl+R for command history search
```

### Context-Aware Conversations
Automatic trimming of long conversation history:
- Keeps most recent messages within token budget
- Preserves conversation coherence
- Prevents token limit errors

### Error Recovery
Graceful handling of common errors:
- Model not found → Download suggestions
- Out of memory → Model switching options
- Corrupted sessions → Automatic recovery
- Command timeouts → Simplified suggestions

## Development Guide

### Running Tests
```bash
# Run all tests
pytest -v

# Run specific test
pytest tests/test_error_scenarios.py -v

# Run with coverage
pytest --cov=mlxcli
```

### Code Quality
```bash
# Format code (100 char lines)
black mlxcli tests --line-length 100

# Lint code
ruff check mlxcli tests --fix

# Type check
mypy mlxcli --ignore-missing-imports --python-version 3.10
```

### Architecture
See CLAUDE.md for detailed component documentation and Phase 2 additions.

## Roadmap

### Phase 2 (v0.2) - Polish ✓
- [x] ShellTool with safety gates
- [x] Comprehensive error handling
- [x] Enhanced model and session management
- [x] Auto-completion support
- [x] Token-aware context management

### Phase 3 (v1.0) - Extension (Planned)
- WebFetch tool for web research
- Code execution tool (sandboxed)
- MCP (Model Context Protocol) support
- Multi-backend support (Ollama, OpenAI)
- Specialized agents (analyzer, debugger, researcher)
- Custom workflow definitions

## License

This project is licensed under the MIT License. See LICENSE for details.

## Contributing

Contributions welcome! Please follow the guidelines in CLAUDE.md.

## References

- [MLX Documentation](https://ml-explore.github.io/mlx/)
- [Typer CLI Framework](https://typer.tiangolo.com/)
- [Pydantic Validation](https://docs.pydantic.dev/)

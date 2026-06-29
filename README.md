# MLX-CLI: Terminal LLM Chat with Local MLX Backend

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)

A terminal-based LLM CLI tool that runs MLX models locally on macOS, inspired by kiro-cli. Execute AI-assisted workflows directly from your terminal with interactive chat, file operations, and shell integration.

## Features

- **Local LLM Inference**: Run open-source models (Llama, Mistral, etc.) locally using MLX
- **Interactive Chat**: Real-time conversation with history and session persistence
- **File Operations**: Read/write files with automatic backups (`.bak` suffixes)
- **Shell Integration**: Execute shell commands directly within conversations
- **Project Context**: Automatic discovery and injection of README, .gitignore, and project structure
- **Session Management**: Save and restore conversations as JSON in `.mlxcli/sessions/`
- **Cross-platform**: Works on macOS and Linux (OSX-first development)
- **Type-Safe**: Full Python 3.10+ type hints with pydantic validation

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

```
┌─────────────────────────────┐
│   CLI Interface Layer       │
│  (REPL, command parsing)    │
├─────────────────────────────┤
│   Session Manager           │
│  (state, JSON persistence)  │
├─────────────────────────────┤
│   Tool Registry             │
│  (file, shell operations)   │
├─────────────────────────────┤
│   LLM Integration (MLX)     │
│  (model inference)          │
└─────────────────────────────┘
```

### Core Modules

| Module | Purpose |
|--------|---------|
| `cli.py` | REPL loop and command parsing |
| `session.py` | Conversation state and persistence |
| `llm.py` | MLX model loading and inference |
| `tool_registry.py` | Tool registration and dispatch |
| `tools/file_tool.py` | File read/write with auto-backup |
| `tools/shell_tool.py` | Shell command execution |
| `context.py` | Project context auto-discovery |

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
# Format code with black (88 char lines)
black mlxcli tests

# Lint and auto-fix issues
ruff check mlxcli tests --fix

# Type checking (note: run against local code only)
mypy mlxcli --ignore-missing-imports --python-version 3.10
```

### Project Structure

```
mlxcli/
├── mlxcli/
│   ├── __init__.py           # Package metadata
│   ├── main.py               # Entry point
│   ├── cli.py                # REPL interface
│   ├── session.py            # State management
│   ├── context.py            # Project context discovery
│   ├── llm.py                # MLX integration
│   ├── tool_registry.py      # Tool dispatch system
│   ├── utils.py              # Utilities and helpers
│   ├── config.py             # Configuration
│   └── tools/
│       ├── base.py           # Tool interface
│       ├── file_tool.py      # File operations
│       └── shell_tool.py     # Shell execution
├── tests/
│   ├── test_*.py             # Unit tests (226 tests)
│   └── test_integration.py   # End-to-end tests (16 tests)
├── docs/                     # Documentation
├── pyproject.toml            # Project config
├── README.md                 # This file
└── CLAUDE.md                 # Development guide
```

### Test Coverage

Current test suite (242 tests):
- **Unit tests**: 226 tests covering all components
- **Integration tests**: 16 tests for end-to-end workflows
- **Areas covered**:
  - Session persistence and recovery
  - Tool registry and execution
  - File operations with backups
  - Project context discovery
  - Complex multi-operation workflows
  - Error handling and edge cases

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

## Roadmap

### Phase 1 (v0.1) - Core
- [x] Design complete
- [ ] CLI REPL setup
- [ ] Session management
- [ ] File operations with backup
- [ ] MLX integration
- [ ] Project context discovery

### Phase 2 (v0.2) - Polish
- [ ] Shell tool with safety guards
- [ ] Session switching UI
- [ ] Model management
- [ ] Command auto-completion

### Phase 3 (v1.0) - Extensions
- [ ] Web fetching tool
- [ ] Code execution sandbox
- [ ] Plugin system (MCP)
- [ ] Multi-backend support
- [ ] Specialized agents

## License

This project is licensed under the MIT License. See LICENSE for details.

## Contributing

Contributions welcome! Please follow the guidelines in CLAUDE.md.

## References

- [MLX Documentation](https://ml-explore.github.io/mlx/)
- [Typer CLI Framework](https://typer.tiangolo.com/)
- [Pydantic Validation](https://docs.pydantic.dev/)

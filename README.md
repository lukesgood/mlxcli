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

### Example Workflows

#### 1. Analyze a Project

```bash
mlx-cli> @README.md Summarize this project
```

The CLI automatically loads the file and includes it in the conversation.

#### 2. Modify Code with Backups

```bash
mlx-cli> @src/main.py Refactor this function for clarity
```

Write operations automatically create `.bak` backups before modifications.

#### 3. Execute Commands

```bash
mlx-cli> ! python -m pytest tests/
```

Run shell commands directly and include results in your conversation.

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

See [CLAUDE.md](CLAUDE.md) for development guide, architecture details, and contribution guidelines.

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Format code
black mlxcli tests

# Lint
ruff check mlxcli tests

# Type check
mypy mlxcli
```

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

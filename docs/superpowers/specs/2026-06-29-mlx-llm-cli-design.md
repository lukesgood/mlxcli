# MLX-Based LLM CLI Design Specification

**Date**: 2026-06-29  
**Project**: mlx-cli (MLX backend LLM CLI, kiro-cli inspired)  
**Status**: Design Approved  
**Language**: Python 3.10+  
**OSX First**: Yes

---

## 1. Executive Summary

This document specifies the architecture and implementation roadmap for **mlx-cli**, a terminal-based LLM CLI tool that:
- Runs MLX models locally on macOS
- Provides kiro-cli-like features (interactive chat, file I/O, context management)
- Implements a plugin-based tool system for extensibility
- Starts with core features, scales to advanced patterns

**Key Design Decision**: Build from scratch rather than use opencli.co, because:
- MLX requires full control over LLM backend and inference parameters
- Local-first architecture needs transparent design, not black-box routing
- Simpler, focused architecture than opencli's provider-agnostic router

---

## 2. Architecture Overview

### 2.1 System Architecture

```
┌─────────────────────────────────────┐
│     CLI Interface Layer             │
│  (readline REPL, command parsing)   │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│    Session Manager                  │
│  (conversation state, JSON storage) │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│    Tool Registry & Dispatcher       │
│  (routes tool requests)             │
├─────────────────────────────────────┤
│ FileTool │ ShellTool │ [Future]    │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│    LLM Integration (MLX)            │
│  (model loading & inference)        │
└─────────────────────────────────────┘
```

### 2.2 Core Modules

| Module | Responsibility |
|--------|-----------------|
| `cli.py` | REPL loop, command parsing, user input handling |
| `session.py` | Conversation state, JSON serialization, persistence |
| `tool_registry.py` | Tool registration, discovery, execution dispatch |
| `tools/file_tool.py` | File read/write with auto-backup |
| `tools/shell_tool.py` | Shell command execution |
| `llm.py` | MLX model loading, inference, token counting |
| `context.py` | Project context (README, structure, .gitignore) |
| `config.py` | Configuration management (.mlxcli/) |

---

## 3. User Workflow

### 3.1 First-Run Experience

```
$ python -m mlxcli

✓ MLX installation verified
✓ Available models scanned
  1. meta-llama/Llama-2-7b-hf (2GB)
  2. mistral-community/Mistral-7B-v0.1 (7GB)

Select model (1-2) [default: 1]: 1
✓ Loading model...
✓ Collecting project context...

mlx-cli> _
```

### 3.2 Interactive Session Flow

```
1. User inputs prompt (with optional @file reference)
2. CLI parses input, detects @references
3. Referenced files auto-loaded into context
4. Prompt + conversation history + tools sent to LLM
5. LLM processes and may call tools (FileTool, ShellTool, etc.)
6. Tool results fed back to LLM
7. Final response displayed and saved to session
```

### 3.3 Commands

**Interactive Commands:**
- `/chat` - Start new conversation (default)
- `/model` - List/change models
- `/save` - Explicitly save session
- `/load <id>` - Load previous session
- `/sessions` - List saved sessions
- `/help` - Show help
- `/exit` - Exit CLI

**Shell Escape:**
- `! <cmd>` - Execute shell command

**File References:**
- `@file_path` - Auto-load file into context
- `@dir_path` - Display directory tree

---

## 4. Session Persistence

### 4.1 Storage Location

- **Directory**: `.mlxcli/sessions/` (within project root)
- **Format**: JSON
- **File naming**: `session_{id}.json`
- **Permissions**: `600` (owner read/write only)

### 4.2 Session Schema

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
      "content": "@README.md를 읽고 프로젝트 요약해줄래?",
      "tools_used": ["FileTool.read"],
      "timestamp": "2026-06-29T10:30:05Z"
    },
    {
      "role": "assistant",
      "content": "프로젝트는 Python 웹 프레임워크입니다...",
      "tools_called": [
        {
          "name": "FileTool.read",
          "args": {"path": "README.md"},
          "result": "# My Project\nA Python web framework..."
        }
      ],
      "timestamp": "2026-06-29T10:30:15Z"
    }
  ],
  "context": {
    "files_referenced": ["README.md"],
    "project_structure": ["src/", "tests/", "docs/"],
    "project_info": {"type": "python", "frameworks": ["flask"]}
  }
}
```

### 4.3 Auto-Save Behavior

- Session auto-saved after every LLM response
- On exit, final session state persisted
- Interrupted sessions recoverable from last save point

---

## 5. Tool System

### 5.1 Tool Interface

```python
class Tool:
    name: str
    description: str
    
    async def execute(self, args: dict) -> dict:
        """Execute tool and return result."""
        pass
```

### 5.2 FileTool

**Operations:**
- `read(path)` - Read file content
- `write(path, content)` - Write with auto-backup (.bak)
- `list_dir(path)` - List directory contents

**Behavior:**
- Backup created before write: `file.txt.bak`
- Respects `.gitignore`
- Fails safely with clear error messages
- Cannot write outside project directory without explicit confirmation

### 5.3 ShellTool

**Operations:**
- `execute(cmd, timeout=30)` - Run shell command

**Behavior:**
- Captures stdout/stderr
- Respects 30-second timeout (configurable)
- First use shows warning about security
- Cannot run destructive commands (rm, git push, etc.) without confirmation

---

## 6. MLX Integration

### 6.1 Model Management

- Models stored in `~/.cache/mlx_lm/` (MLX standard)
- Model selection during initialization
- Model switching via `/model` command
- Automatic fallback to smaller models if VRAM insufficient

### 6.2 Inference

```
LLM Process:
1. Prepare prompt + conversation history
2. Include tool descriptions (JSON schema)
3. Send to MLX model
4. Parse response for tool calls (structured format)
5. Execute requested tools
6. Feed results back to LLM (multi-turn)
7. Return final response
```

### 6.3 Token Management

- Count tokens before sending to model
- Warn if approaching context limit
- Trim oldest messages if necessary
- Configurable context window per model

---

## 7. Project Context

### 7.1 Auto-Discovery

On startup, scan working directory for:
- `README.md` → Project purpose
- `package.json` / `pyproject.toml` → Project metadata
- `.gitignore` → Files to exclude
- Directory structure → File tree

### 7.2 Context Injection

- Automatically included in system prompt
- Updated each session
- Cached for performance

---

## 8. Error Handling

### 8.1 Model Loading Errors

| Error | Action |
|-------|--------|
| MLX not installed | Show installation guide |
| Model not found locally | Offer download with size info |
| VRAM insufficient | Suggest smaller model |
| Model load timeout | Suggest checking disk space |

### 8.2 File Operation Errors

| Error | Action |
|-------|--------|
| Permission denied | Clear message + suggest location |
| File not found | List similar files in directory |
| Write failed | Confirm backup exists, offer alternatives |
| Path outside project | Require explicit confirmation |

### 8.3 LLM Errors

| Error | Action |
|-------|--------|
| Token limit exceeded | Trim context + retry |
| Tool execution failed | Return error to LLM + retry |
| Inference timeout | Simplify prompt + retry once |
| Generation stop (max tokens) | Return partial response |

### 8.4 Session Errors

| Error | Action |
|-------|--------|
| Corrupted JSON | Restore from backup if available |
| Session not found | List available sessions |
| Disk full | Clear old sessions (with confirmation) |

---

## 9. Security

### 9.1 File Access

- Read: Any file in project directory or referenced explicitly
- Write: Only within project, with auto-backup
- Cannot follow symlinks outside project
- Respects file permissions (fail if no access)

### 9.2 Tool Permissions

- FileTool: Read free, write after confirmation
- ShellTool: Show command preview, require approval first time
- Future tools: Per-tool permission config

### 9.3 Session Privacy

- Session files owned by user only (`chmod 600`)
- No API keys stored in sessions
- Sensitive outputs warning if detected

---

## 10. Extension Points

### 10.1 Future Tools

**WebFetch Tool** (Phase 2)
- Fetch and parse web content
- Support for PDF extraction
- Rate limiting & caching

**Code Execution Tool** (Phase 2)
- Execute Python/shell scripts in sandboxed environment
- Capture output + errors

**Custom Tools** (Phase 3)
- Plugin system for user-defined tools
- MCP (Model Context Protocol) support

### 10.2 Multi-Backend Support (Phase 3)

- Ollama (local inference server)
- OpenAI API (cloud fallback)
- Plugin architecture for new backends

### 10.3 Agent Patterns (Phase 3)

- Specialized agents (code analyzer, debugger, researcher)
- Multi-step workflows
- Agent steering via config files

---

## 11. Technology Stack

### 11.1 Core Dependencies

```
mlx-lm>=0.15.0         # MLX LLM inference
pydantic>=2.0          # Data validation
typer>=0.9             # CLI framework
rich>=13.0             # Terminal formatting
prompt-toolkit>=3.0    # Advanced readline
pyyaml>=6.0            # Config files
```

### 11.2 Development Dependencies

```
pytest>=7.0            # Testing
black>=23.0            # Code formatting
ruff>=0.1.0            # Linting
mypy>=1.0              # Type checking
```

### 11.3 Python Version

- Minimum: Python 3.10
- Tested on: macOS 13+
- Target: Standard library first, minimal external deps

---

## 12. Project Structure

```
mlxcli/
├── mlxcli/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── cli.py                  # REPL & command handling
│   ├── session.py              # Session management
│   ├── llm.py                  # MLX integration
│   ├── context.py              # Project context
│   ├── tool_registry.py        # Tool system
│   ├── config.py               # Configuration
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py             # Tool interface
│   │   ├── file_tool.py        # File operations
│   │   └── shell_tool.py       # Shell execution
│   └── utils.py                # Utilities
├── tests/
│   ├── test_cli.py
│   ├── test_session.py
│   └── test_tools.py
├── docs/
│   └── superpowers/
│       └── specs/              # Design documents
├── pyproject.toml
├── README.md
├── .gitignore
└── CLAUDE.md                   # Development guide
```

---

## 13. Implementation Roadmap

### Phase 1: Core (v0.1)
- ✅ Design complete
- [ ] CLI REPL setup
- [ ] Session management (JSON)
- [ ] FileTool (read/write/backup)
- [ ] MLX integration (basic)
- [ ] Project context auto-discovery

### Phase 2: Polish (v0.2)
- [ ] ShellTool with safety guards
- [ ] Error handling & recovery
- [ ] Session list & switching
- [ ] Model management UI
- [ ] Command auto-completion

### Phase 3: Extension (v1.0)
- [ ] WebFetch tool
- [ ] Code execution tool
- [ ] Plugin system (MCP)
- [ ] Multi-backend support
- [ ] Agent patterns

---

## 14. Success Criteria

### For v0.1 (Core)
- ✓ Can start CLI and select model
- ✓ Can chat interactively with MLX model
- ✓ Can reference and read files via @file syntax
- ✓ Can modify files with auto-backup
- ✓ Can save/load sessions as JSON
- ✓ Sessions persist across restarts

### For v0.2 (Polish)
- ✓ Shell command execution with safety
- ✓ List and switch between saved sessions
- ✓ Error messages are clear and actionable
- ✓ Model switching mid-session works
- ✓ Auto-completion for commands and files

### For v1.0 (Extension)
- ✓ Web fetching & parsing
- ✓ Sandboxed code execution
- ✓ Custom tool registration
- ✓ Ollama/OpenAI backends work
- ✓ Specialized agents available

---

## 15. Notes & Decisions

### Why Build from Scratch vs. opencli.co?

1. **MLX Optimization**: Need full control over LLM backend, context windows, token limits
2. **Simplicity**: Focused architecture easier to maintain than opencli's provider-agnostic router
3. **Transparency**: Developers understand what's happening at each step
4. **Local-First**: Optimized for edge inference, not cloud agent routing
5. **Community Value**: Clear, maintainable code benefits future contributors

### Why Plugin-Based Architecture?

1. **Extensibility**: New tools added without core changes
2. **Testability**: Each tool tested independently
3. **Reusability**: Tools available across agent patterns
4. **Future-Proof**: Ready for MCP integration later

### Why JSON for Sessions?

1. **Transparency**: Human-readable, easily debugged
2. **Git-Friendly**: Diffs show exactly what changed
3. **No Extra Dependencies**: Pure Python, stdlib only
4. **Portability**: Easily exported/imported, backed up

---

## 16. Open Questions

- (None currently - design is complete)

---

**Design approved by user on 2026-06-29**. Ready for implementation planning.

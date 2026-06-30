"""CLI - Interactive REPL interface for MLX-CLI."""

import re
from pathlib import Path
from typing import Optional, Tuple

from prompt_toolkit import PromptSession

from mlxcli.completion import setup_completion
from mlxcli.config import Config
from mlxcli.context import ProjectContext
from mlxcli.llm import MLXBackend
from mlxcli.session import Session
from mlxcli.tool_registry import ToolRegistry
from mlxcli.utils import get_project_root


class CLI:
    """Interactive REPL command-line interface for MLX-CLI.

    Manages the main REPL loop, command parsing, and user interaction.
    Integrates with Session, ProjectContext, MLXBackend, and ToolRegistry.

    Attributes:
        project_root: Path to the project root directory.
        context: ProjectContext for project discovery and metadata.
        backend: MLXBackend for model loading and inference.
        registry: ToolRegistry for tool registration and execution.
        session: Current Session instance (created during run).
        config: Config instance for configuration management.
    """

    def __init__(self, project_root: Optional[Path] = None) -> None:
        """Initialize CLI with optional project root.

        Args:
            project_root: Path to project root. If None, auto-detects.

        Raises:
            RuntimeError: If project root cannot be determined.
        """
        if project_root is None:
            self.project_root = get_project_root()
        else:
            self.project_root = Path(project_root).resolve()

        self.context = ProjectContext(self.project_root)
        self.backend = MLXBackend()
        self.registry = ToolRegistry()
        self.config = Config()
        self.session: Optional[Session] = None

    def run(self) -> None:
        """Main entry point for the CLI.

        Orchestrates the complete workflow:
        1. Display available models and let user select
        2. Load selected model
        3. Create a new session
        4. Start REPL loop

        Returns:
            None
        """
        print("MLX-CLI - Interactive LLM Interface")
        print("=====================================\n")

        # Step 1: Model selection
        if not self._select_model():
            print("Model selection cancelled.")
            return

        # Step 2: Create session
        self._create_session()
        print(f"Session created: {self.session.id}\n")

        # Step 3: Start REPL loop
        self._repl_loop()

    def _select_model(self) -> bool:
        """Interactive model selection.

        Displays available models and prompts user to select one.
        Returns False if user cancels (enters 0).

        Returns:
            bool: True if model was selected, False if cancelled.
        """
        models = self.backend.get_available_models()

        if not models:
            print("No models available. Ensure MLX is installed.")
            return False

        print("Available Models:")
        print("-" * 50)
        for i, model in enumerate(models, 1):
            name = model.get("name", "Unknown")
            size = model.get("size", "Unknown")
            desc = model.get("description", "")
            print(f"{i}. {name} ({size})")
            print(f"   {desc}")

        print("\n0. Cancel")
        print("-" * 50)

        try:
            choice = input("Select model (0 to cancel): ").strip()
            choice_idx = int(choice) - 1

            if choice_idx < 0:
                return False

            if choice_idx >= len(models):
                print("Invalid selection.")
                return False

            selected_model = models[choice_idx]["name"]
            print(f"\nLoading {selected_model}...")

            if self.backend.load_model(selected_model):
                print(f"Successfully loaded {selected_model}\n")
                return True
            else:
                print(f"Failed to load {selected_model}")
                return False

        except (ValueError, KeyboardInterrupt):
            return False

    def _create_session(self) -> None:
        """Create a new session.

        Initializes a Session with the selected model and project context.
        """
        model = self.backend.current_model_name or "unknown"
        self.session = Session(
            model=model,
            working_directory=str(self.project_root),
            context=self.context.to_dict(),
        )

    def _repl_loop(self) -> None:
        """Main REPL loop.

        Continuously prompts for user input, parses commands,
        and handles conversation. Exits on /exit command or Ctrl+C.

        Handles:
        - Command parsing (/command syntax)
        - Regular conversation
        - KeyboardInterrupt (Ctrl+C)
        - Auto-save on exit
        - Tab completion for commands and files
        """
        print("Type '/help' for commands, or start typing to chat.")
        print("Press Ctrl+C or type '/exit' to quit.")
        print("Use Tab for completion of commands and files.\n")

        # Setup completion for REPL
        completer = setup_completion(self.project_root)
        session = PromptSession(completer=completer)

        try:
            while True:
                try:
                    user_input = session.prompt("mlx-cli> ").strip()

                    if not user_input:
                        continue

                    # Parse command or conversation
                    is_command, cmd_name, args = self._parse_command(user_input)

                    if is_command:
                        # Handle command
                        if not self._handle_command(cmd_name, args):
                            # Command returned False -> exit
                            break
                    else:
                        # Handle as conversation
                        self._handle_conversation(user_input)

                except KeyboardInterrupt:
                    print("\n")
                    break

        except EOFError:
            print("\n")

        finally:
            # Auto-save session on exit
            if self.session and self.config.get("auto_save"):
                self.session.save()
                print(f"Session saved: {self.session.id}")

    def _parse_command(self, text: str) -> Tuple[bool, str, str]:
        """Parse command syntax from input.

        Recognizes /command or /command args format.
        Returns tuple of (is_command, command_name, arguments).

        Args:
            text: Input text to parse.

        Returns:
            Tuple of (is_command: bool, cmd_name: str, args: str):
            - is_command: True if text starts with /
            - cmd_name: The command name (empty if not a command)
            - args: Arguments after command name (empty if no args)
        """
        if not text.startswith("/"):
            return False, "", ""

        # Remove leading /
        text = text[1:].strip()

        # Split on first space
        parts = text.split(maxsplit=1)
        cmd_name = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        return True, cmd_name, args

    def _handle_command(self, cmd: str, args: str = "") -> bool:
        """Execute a command.

        Supported commands:
        - help: Show help text
        - model: Show current model or subcommands (list, switch)
        - sessions: List saved sessions or subcommands (delete <id>)
        - delete: Delete a session
        - save: Manually save session
        - exit: Exit the CLI

        Args:
            cmd: Command name.
            args: Optional command arguments.

        Returns:
            bool: False to exit REPL loop, True to continue.
        """
        if cmd == "help":
            self._print_help()
            return True

        elif cmd == "model":
            return self._handle_model_command(args)

        elif cmd == "sessions":
            return self._handle_sessions_command(args)

        elif cmd == "delete":
            if not args:
                print("Usage: /delete <session_id>")
                return True
            self._delete_session_command(args)
            return True

        elif cmd == "save":
            if self.session:
                self.session.save()
                print(f"Session saved: {self.session.id}")
            else:
                print("No session to save.")
            return True

        elif cmd == "exit":
            return False

        else:
            print(f"Unknown command: /{cmd}. Type '/help' for available commands.")
            return True

    def _handle_model_command(self, args: str) -> bool:
        """Route /model subcommands.

        Supported subcommands:
        - (no args): Show current model info
        - list: List available models
        - switch <name>: Switch to different model

        Args:
            args: Subcommand and arguments.

        Returns:
            bool: True to continue REPL loop.
        """
        if not args or args.strip() == "":
            # No args - show current model info
            self._model_info_command()
            return True

        parts = args.split(maxsplit=1)
        subcommand = parts[0].lower()

        if subcommand == "list":
            self._list_models_command()
            return True

        elif subcommand == "switch":
            if len(parts) < 2:
                print("Usage: /model switch <model_name>")
                return True
            model_name = parts[1]
            self._switch_model_command(model_name)
            return True

        else:
            print(f"Unknown model subcommand: {subcommand}")
            print("Usage: /model [list|switch <name>]")
            return True

    def _model_info_command(self) -> None:
        """Show current model info.

        Displays information about the currently loaded model including
        its name, status, context window, and size.
        """
        model_info = self.backend.get_model_info()

        if model_info["status"] == "no_model":
            print("📊 No model loaded")
            return

        # Format and display model info
        name = model_info.get("name", "Unknown")
        context = model_info.get("context", 0)
        size = model_info.get("size", "Unknown")

        print(f"📊 Current Model: {name}")
        print(f"   Status: Loaded")
        print(f"   Context: {context} tokens")
        print(f"   Size: {size}")

    def _list_models_command(self) -> None:
        """List available models.

        Displays all available models with descriptions and sizes.
        """
        models = self.backend.get_available_models()

        if not models:
            print("📦 No models available")
            return

        print("📦 Available Models:")
        for i, model in enumerate(models, 1):
            name = model.get("name", "Unknown")
            description = model.get("description", "")
            size = model.get("size", "Unknown")

            print(f"  {i}. {name}")
            print(f"     {description}")
            print(f"     Size: {size}")

    def _switch_model_command(self, model_name: str) -> None:
        """Switch to different model.

        Attempts to load a new model and update the current session.
        Continues the session with the new model.

        Args:
            model_name: Name of the model to switch to.
        """
        if self.backend.load_model(model_name):
            if self.session:
                self.session.model = model_name
            print(f"✓ Switched to {model_name}")
        else:
            print(f"✗ Failed to load {model_name}")

    def _handle_sessions_command(self, args: str) -> bool:
        """Route /sessions subcommands.

        Supported subcommands:
        - (no args): List all sessions
        - delete <id>: Delete a session

        Args:
            args: Subcommand and arguments.

        Returns:
            bool: True to continue REPL loop.
        """
        if not args or args.strip() == "":
            # No args - list sessions
            self._list_sessions_command()
            return True

        parts = args.split(maxsplit=1)
        subcommand = parts[0].lower()

        if subcommand == "delete":
            if len(parts) < 2:
                print("Usage: /sessions delete <session_id>")
                return True
            session_id = parts[1]
            self._delete_session_command(session_id)
            return True

        else:
            print(f"Unknown sessions subcommand: {subcommand}")
            print("Usage: /sessions [delete <id>]")
            return True

    def _list_sessions_command(self) -> None:
        """List all sessions with summaries."""
        from pathlib import Path

        # Get the sessions directory
        sessions_dir = self.project_root / ".mlxcli" / "sessions"

        sessions = Session.list_sessions(sessions_dir)

        if not sessions:
            print("📋 No saved sessions.")
            return

        print("📋 Saved Sessions:\n")
        for i, session in enumerate(sessions, 1):
            summary = session.get_summary()
            print(f"  {i}. {summary['id']}")
            print(f"     Model: {summary['model']}")
            print(f"     Messages: {summary['message_count']}")
            if summary["last_message"]:
                print(f'     Last: "{summary["last_message"]}..."')
            print(f"     Updated: {summary['updated']}")
            print()

    def _delete_session_command(self, session_id: str) -> None:
        """Delete a session.

        Args:
            session_id: The session ID to delete.
        """
        from pathlib import Path

        # Get the sessions directory
        sessions_dir = self.project_root / ".mlxcli" / "sessions"

        result = Session.delete_session(session_id, sessions_dir)
        if result:
            print(f"✓ Session deleted: {session_id}")
        else:
            print(f"✗ Session not found: {session_id}")

    def _print_help(self) -> None:
        """Print help text with available commands."""
        help_text = """
MLX-CLI Commands:
================

  /help                    Show this help message
  /model                   Show current model info
  /model list              List available models
  /model switch NAME       Switch to different model
  /sessions                List saved sessions
  /sessions delete <id>    Delete a session
  /delete <id>             Delete a session (shorthand)
  /save                    Manually save the current session
  /exit                    Exit the CLI

Regular text will be sent to the AI model for response.
Use @filename syntax to reference files (phase 2 feature).
"""
        print(help_text)

    def _list_sessions(self) -> None:
        """List all saved sessions (deprecated - use _list_sessions_command)."""
        self._list_sessions_command()

    def _handle_conversation(self, user_input: str) -> None:
        """Handle user message for conversation.

        Processes user input and adds it to the session.
        In Phase 2, this will handle:
        - File reference resolution (@file syntax)
        - Model inference
        - Tool execution
        - Response formatting

        Args:
            user_input: User's message text.
        """
        if not self.session:
            print("No session active.")
            return

        # Add user message to session
        self.session.add_message(role="user", content=user_input)

        # Run model inference
        try:
            print("\n🤖 Thinking...\n")

            # Get tool definitions
            tools = self.registry.list_tools()

            # Generate response from model
            response = self.backend.generate(
                prompt=user_input,
                messages=self.session.messages[:-1] if len(self.session.messages) > 1 else None,
                tools=tools if tools else None,
                max_tokens=512
            )

            # Add assistant response to session
            self.session.add_message(role="assistant", content=response)

            # Display response
            print(f"{response}\n")

            # Auto-save session
            if self.config.get("auto_save", True):
                self.session.save()

        except Exception as e:
            print(f"\n✗ Error: {type(e).__name__}")
            print(f"  {str(e)}\n")

    def _parse_file_references(self, text: str) -> list[str]:
        """Parse @file reference syntax from text.

        Finds all @filename references in the text.
        Currently basic implementation for Phase 1.

        In Phase 2, will:
        - Resolve file paths
        - Validate file access
        - Handle @file with quoted paths

        Args:
            text: Text to parse for references.

        Returns:
            list[str]: List of referenced file names/paths.
        """
        # Find all @word patterns
        pattern = r"@(\w+)"
        matches = re.findall(pattern, text)
        return matches

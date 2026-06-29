"""CLI - Interactive REPL interface for MLX-CLI."""

import re
import sys
from pathlib import Path
from typing import Optional, Tuple

from mlxcli.config import Config
from mlxcli.session import Session
from mlxcli.context import ProjectContext
from mlxcli.llm import MLXBackend
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
        """
        print("Type '/help' for commands, or start typing to chat.")
        print("Press Ctrl+C or type '/exit' to quit.\n")

        try:
            while True:
                try:
                    user_input = input("mlx-cli> ").strip()

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
        - model: Show current model
        - sessions: List saved sessions
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
            if self.session:
                print(f"Current model: {self.session.model}")
            else:
                print("No session active.")
            return True

        elif cmd == "sessions":
            self._list_sessions()
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

    def _print_help(self) -> None:
        """Print help text with available commands."""
        help_text = """
MLX-CLI Commands:
================

  /help        Show this help message
  /model       Show current model
  /sessions    List saved sessions
  /save        Manually save the current session
  /exit        Exit the CLI

Regular text will be sent to the AI model for response.
Use @filename syntax to reference files (phase 2 feature).
"""
        print(help_text)

    def _list_sessions(self) -> None:
        """List all saved sessions."""
        sessions = Session.list_sessions()

        if not sessions:
            print("No saved sessions.")
            return

        print("\nSaved Sessions:")
        print("-" * 60)
        for session in sessions:
            created = session.created_at.strftime("%Y-%m-%d %H:%M:%S")
            print(f"  {session.id} | {session.model} | Created: {created}")
        print("-" * 60)

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

        # In Phase 2, here we would:
        # 1. Parse file references with _parse_file_references()
        # 2. Run model inference
        # 3. Handle tool calls
        # 4. Format and display response
        # 5. Add assistant message to session

        # For now, just acknowledge
        print("[Phase 2: Model inference and response handling]")

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

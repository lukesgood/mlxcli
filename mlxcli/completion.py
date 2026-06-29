"""Completion system - Tab completion for commands and files in REPL."""

from pathlib import Path
from typing import Iterator, Optional

from prompt_toolkit.completion import (
    Completer,
    Completion,
    NestedCompleter,
)
from prompt_toolkit.document import Document


class FileCompleter(Completer):
    """Complete file paths after @.

    Suggests file paths relative to the project root directory.
    Respects .gitignore patterns when available.

    Attributes:
        project_root: Root directory for file path completion.
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize FileCompleter.

        Args:
            project_root: Root directory for file completion scope.
        """
        self.project_root = Path(project_root).resolve()
        self._ignored_patterns = self._load_gitignore()

    def _load_gitignore(self) -> list[str]:
        """Load gitignore patterns from .gitignore file.

        Returns:
            List of gitignore patterns.
        """
        patterns = []
        gitignore_path = self.project_root / ".gitignore"
        if gitignore_path.exists():
            lines = gitignore_path.read_text().strip().split("\n")
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
        return patterns

    def _is_ignored(self, path: Path) -> bool:
        """Check if path should be ignored based on patterns.

        Args:
            path: Path to check.

        Returns:
            bool: True if path should be ignored, False otherwise.
        """
        import fnmatch

        filename = path.name

        # Ignore hidden files except specific ones
        if filename.startswith(".") and filename not in [".env", ".gitignore"]:
            return True

        # Check against gitignore patterns
        for pattern in self._ignored_patterns:
            if "*" in pattern:
                if fnmatch.fnmatch(filename, pattern):
                    return True
            elif filename == pattern:
                return True

        return False

    def _get_matching_files(self, prefix: str) -> list[str]:
        """Get files matching the given prefix.

        Args:
            prefix: File name prefix to match.

        Returns:
            List of matching file names.
        """
        matches = []
        prefix_lower = prefix.lower()

        try:
            for item in self.project_root.iterdir():
                # Skip ignored files
                if self._is_ignored(item):
                    continue

                name = item.name
                if name.lower().startswith(prefix_lower):
                    matches.append(name)
        except (OSError, PermissionError):
            # Handle permission errors gracefully
            pass

        return sorted(matches)

    def get_completions(
        self, document: Document, complete_event
    ) -> Iterator[Completion]:
        """Get completions for file paths after @.

        Args:
            document: Current input document.
            complete_event: Completion event.

        Yields:
            Completion objects for matching files.
        """
        # Find @ symbol in text
        text = document.text_before_cursor
        if "@" not in text:
            return

        # Extract text after last @
        at_index = text.rfind("@")
        if at_index == -1:
            return

        # Get text after @
        after_at = text[at_index + 1 :]

        # Get matching files
        matches = self._get_matching_files(after_at)

        # Yield completions
        for match in matches:
            # Calculate how much of the typed prefix to replace
            completion_text = match[len(after_at) :]
            yield Completion(
                text=completion_text,
                start_position=-len(after_at),
                display=match,
            )


class CommandCompleter(Completer):
    """Complete slash commands in REPL.

    Provides completion for all available slash commands like /help, /model, etc.

    Attributes:
        COMMANDS: List of all available commands.
    """

    COMMANDS = [
        "/chat",
        "/help",
        "/model",
        "/model list",
        "/model switch",
        "/sessions",
        "/save",
        "/load",
        "/exit",
        "/delete",
    ]

    def get_completions(
        self, document: Document, complete_event
    ) -> Iterator[Completion]:
        """Get completions for slash commands.

        Args:
            document: Current input document.
            complete_event: Completion event.

        Yields:
            Completion objects for matching commands.
        """
        text = document.text_before_cursor

        # Only complete if we have a slash
        if "/" not in text:
            return

        # Find the last / and extract everything after it
        last_slash_idx = text.rfind("/")
        prefix = text[last_slash_idx:].lower()

        # Filter commands that match the prefix
        matches = [cmd for cmd in self.COMMANDS if cmd.lower().startswith(prefix)]

        # Calculate how much of the prefix to keep/replace
        # start_position is negative offset from cursor
        start_position = -len(prefix)

        # Yield completions
        for cmd in matches:
            # Remove the prefix that was already typed
            completion_text = cmd[len(prefix) :]
            yield Completion(
                text=completion_text,
                start_position=start_position,
                display=cmd,
            )


def get_command_completer() -> Completer:
    """Create NestedCompleter for slash commands with subcommands.

    Returns:
        NestedCompleter configured for command hierarchy.
    """
    # Create a nested completer for /model subcommands
    command_dict = {
        "/chat": None,
        "/help": None,
        "/model": {
            "list": None,
            "switch": None,
        },
        "/sessions": None,
        "/save": None,
        "/load": None,
        "/exit": None,
        "/delete": None,
    }

    return NestedCompleter(command_dict)


def setup_completion(project_root: Path) -> Completer:
    """Create combined completer for file + command completion.

    Sets up a completer that handles both file paths (after @) and
    slash commands (after /) with automatic switching based on context.

    Args:
        project_root: Root directory for file completion scope.

    Returns:
        Completer instance that handles both files and commands.
    """
    from prompt_toolkit.completion import ConditionalCompleter

    file_completer = FileCompleter(project_root)
    command_completer = CommandCompleter()

    # Create a combined completer that checks document context
    class CombinedCompleter(Completer):
        """Combined completer for files and commands."""

        def __init__(self, file_completer: Completer, command_completer: Completer):
            self.file_completer = file_completer
            self.command_completer = command_completer

        def get_completions(
            self, document: Document, complete_event
        ) -> Iterator[Completion]:
            """Route to appropriate completer based on context.

            Args:
                document: Current input document.
                complete_event: Completion event.

            Yields:
                Completion objects from appropriate completer.
            """
            text = document.text_before_cursor

            # Check which completer to use
            if "@" in text:
                # Prioritize file completion if @ is present
                at_index = text.rfind("@")
                slash_index = text.rfind("/")

                # Use file completer if @ comes after /
                if slash_index < at_index:
                    yield from self.file_completer.get_completions(
                        document, complete_event
                    )
                    return

            # Check for command completion
            if "/" in text:
                yield from self.command_completer.get_completions(
                    document, complete_event
                )
                return

    return CombinedCompleter(file_completer, command_completer)

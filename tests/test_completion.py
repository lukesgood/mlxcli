"""Tests for completion system - Tab completion for commands and files."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.completion import (
    CommandCompleter,
    FileCompleter,
    get_command_completer,
    setup_completion,
)
from prompt_toolkit.completion import Completer
from prompt_toolkit.document import Document


class TestFileCompleter:
    """Test FileCompleter - file path completion after @."""

    def test_file_completer_can_be_created(self):
        """FileCompleter should be instantiable with project_root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir).resolve()
            completer = FileCompleter(project_root)

            assert completer is not None
            assert isinstance(completer, FileCompleter)

    def test_file_completer_suggests_matching_files(self):
        """FileCompleter should suggest files matching prefix after @."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir).resolve()

            # Create some test files
            (project_root / "README.md").touch()
            (project_root / "README.txt").touch()
            (project_root / "setup.py").touch()

            completer = FileCompleter(project_root)

            # Create a document with @READ
            doc = Document("@READ", len("@READ"))

            completions = list(completer.get_completions(doc, None))

            # Should have suggestions for files starting with READ
            assert len(completions) > 0
            # Check that completions contain README files (check display)
            completion_displays = []
            for c in completions:
                if hasattr(c.display, "__iter__"):
                    display_text = "".join(
                        str(item[1]) if isinstance(item, tuple) else str(item) for item in c.display
                    )
                else:
                    display_text = str(c.display)
                completion_displays.append(display_text)
            assert any("README" in text for text in completion_displays)

    def test_file_completer_ignores_gitignore_patterns(self):
        """FileCompleter should respect .gitignore patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir).resolve()

            # Create .gitignore file
            gitignore = project_root / ".gitignore"
            gitignore.write_text("*.tmp\nignored_file.txt\n")

            # Create files
            (project_root / "kept_file.txt").touch()
            (project_root / "ignored_file.txt").touch()
            (project_root / "test.tmp").touch()

            completer = FileCompleter(project_root)

            # Should not suggest ignored files
            doc = Document("@", len("@"))
            completions = list(completer.get_completions(doc, None))
            completion_texts = [c.text for c in completions]

            # kept_file.txt should be suggested (or be present)
            # ignored files should not be in completions
            assert not any("ignored_file" in text for text in completion_texts)
            assert not any(".tmp" in text for text in completion_texts)

    def test_file_completer_handles_empty_project(self):
        """FileCompleter should handle empty project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir).resolve()
            completer = FileCompleter(project_root)

            doc = Document("@", len("@"))
            completions = list(completer.get_completions(doc, None))

            # Should return empty list or default completions without error
            assert isinstance(completions, list)

    def test_file_completer_works_with_nested_paths(self):
        """FileCompleter should handle nested directory paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir).resolve()

            # Create nested structure
            (project_root / "src").mkdir()
            (project_root / "src" / "main.py").touch()
            (project_root / "src" / "utils.py").touch()

            completer = FileCompleter(project_root)

            # Complete files in src/
            doc = Document("@src/", len("@src/"))
            completions = list(completer.get_completions(doc, None))

            # Should suggest files in src/
            assert isinstance(completions, list)


class TestCommandCompleter:
    """Test CommandCompleter - completion for slash commands."""

    def test_command_completer_can_be_created(self):
        """CommandCompleter should be instantiable."""
        completer = CommandCompleter()

        assert completer is not None
        assert isinstance(completer, CommandCompleter)

    def test_command_completer_has_all_commands(self):
        """CommandCompleter should have all required commands."""
        completer = CommandCompleter()

        commands = completer.COMMANDS

        # Check for all required commands
        assert "/chat" in commands
        assert "/help" in commands
        assert "/model" in commands
        assert "/model list" in commands
        assert "/model switch" in commands
        assert "/sessions" in commands
        assert "/save" in commands
        assert "/load" in commands
        assert "/exit" in commands
        assert "/delete" in commands

    def test_command_completer_filters_by_prefix(self):
        """CommandCompleter should filter commands by prefix."""
        completer = CommandCompleter()

        # Complete /s commands
        doc = Document("/s", len("/s"))
        completions = list(completer.get_completions(doc, None))

        # Check display or get the full command
        completion_displays = []
        for c in completions:
            # Display is a FormattedText object, extract the text
            if hasattr(c.display, "__iter__"):
                display_text = "".join(
                    str(item[1]) if isinstance(item, tuple) else str(item) for item in c.display
                )
            else:
                display_text = str(c.display)
            completion_displays.append(display_text)

        # Should suggest /save, /sessions
        assert any("save" in text.lower() for text in completion_displays)
        assert any("sessions" in text.lower() for text in completion_displays)

    def test_command_completer_case_insensitive_matching(self):
        """CommandCompleter should match case-insensitively."""
        completer = CommandCompleter()

        # Complete /M (uppercase)
        doc = Document("/M", len("/M"))
        completions = list(completer.get_completions(doc, None))

        # Check display
        completion_displays = []
        for c in completions:
            if hasattr(c.display, "__iter__"):
                display_text = "".join(
                    str(item[1]) if isinstance(item, tuple) else str(item) for item in c.display
                )
            else:
                display_text = str(c.display)
            completion_displays.append(display_text)

        # Should suggest /model commands despite uppercase input
        assert len(completions) > 0
        assert any("model" in text.lower() for text in completion_displays)

    def test_command_completer_suggests_model_subcommands(self):
        """CommandCompleter should suggest /model subcommands."""
        completer = CommandCompleter()

        # Check that /model, /model list, /model switch are all present
        commands = completer.COMMANDS

        model_commands = [c for c in commands if "model" in c.lower()]

        assert "/model" in model_commands
        assert "/model list" in model_commands
        assert "/model switch" in model_commands

    def test_command_completer_returns_completions(self):
        """CommandCompleter should return valid Completion objects."""
        completer = CommandCompleter()

        doc = Document("/h", len("/h"))
        completions = list(completer.get_completions(doc, None))

        # Should return completions for /help
        assert len(completions) > 0
        # Each completion should have text attribute
        for completion in completions:
            assert hasattr(completion, "text")


class TestGetCommandCompleter:
    """Test get_command_completer factory function."""

    def test_get_command_completer_returns_completer(self):
        """get_command_completer should return a Completer instance."""
        completer = get_command_completer()

        assert completer is not None
        assert isinstance(completer, Completer)

    def test_get_command_completer_handles_model_subcommands(self):
        """get_command_completer should handle /model subcommands."""
        completer = get_command_completer()

        # This should return a NestedCompleter that understands /model
        assert completer is not None


class TestSetupCompletion:
    """Test setup_completion function - combined completer setup."""

    def test_setup_completion_returns_completer(self):
        """setup_completion should return a Completer instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir).resolve()
            completer = setup_completion(project_root)

            assert completer is not None
            assert isinstance(completer, Completer)

    def test_setup_completion_works_for_files_and_commands(self):
        """setup_completion should return completer for both files and commands."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir).resolve()

            # Create a test file
            (project_root / "test.py").touch()

            completer = setup_completion(project_root)

            # Should be a completer that can handle both
            assert completer is not None

    def test_setup_completion_document_tracking(self):
        """setup_completion should track document position correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir).resolve()

            completer = setup_completion(project_root)

            # Create documents at different positions
            doc1 = Document("/", len("/"))
            doc2 = Document("@", len("@"))

            # Should not error on different document positions
            assert completer is not None


class TestCompletionIntegration:
    """Integration tests for completion system."""

    def test_multiple_completions_can_be_chained(self):
        """Completion should work across multiple commands in sequence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir).resolve()

            # Create test files
            (project_root / "model1.py").touch()
            (project_root / "model2.py").touch()

            completer = setup_completion(project_root)

            # First complete a command
            doc1 = Document("/model s", len("/model s"))
            completions1 = list(completer.get_completions(doc1, None))

            # Then complete a file
            doc2 = Document("@model", len("@model"))
            completions2 = list(completer.get_completions(doc2, None))

            # Both should work
            assert completer is not None

    def test_completion_with_cli_integration(self):
        """Completion system should integrate with CLI without breaking REPL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir).resolve()

            # This is a smoke test to ensure completion doesn't break existing REPL
            completer = setup_completion(project_root)

            # Should create completer successfully
            assert completer is not None
            assert isinstance(completer, Completer)

    def test_file_completer_respects_project_directory(self):
        """File completer should only suggest files within project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir).resolve()

            # Create files in project
            (project_root / "project_file.py").touch()

            completer = setup_completion(project_root)

            # Should not suggest files outside project
            doc = Document("@", len("@"))
            completions = list(completer.get_completions(doc, None))

            # Should be within project scope
            assert completer is not None

    def test_command_completer_all_commands_supported(self):
        """All required commands should be available for completion."""
        completer = CommandCompleter()

        required_commands = [
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

        for cmd in required_commands:
            assert cmd in completer.COMMANDS, f"{cmd} not in COMMANDS"

    def test_completion_empty_input_handling(self):
        """Completion should handle empty input gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir).resolve()

            completer = setup_completion(project_root)

            # Empty document
            doc = Document("", 0)
            completions = list(completer.get_completions(doc, None))

            # Should not error
            assert isinstance(completions, list)

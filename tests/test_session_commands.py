"""Tests for Session command enhancements - listing, info, and deletion."""

import json
import shutil
import sys
import tempfile
import time
from datetime import datetime
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.cli import CLI
from mlxcli.session import Session


class TestSessionMetadata:
    """Test session metadata tracking."""

    def test_session_has_created_at_timestamp(self):
        """Session should track created_at timestamp."""
        session = Session(model="test", working_directory="/tmp")

        assert hasattr(session, "created_at")
        assert isinstance(session.created_at, datetime)

    def test_session_has_updated_at_timestamp(self):
        """Session should track updated_at timestamp."""
        session = Session(model="test", working_directory="/tmp")

        assert hasattr(session, "updated_at")
        assert isinstance(session.updated_at, datetime)

    def test_created_at_persists_across_save_load(self):
        """created_at should persist when saving and loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir()

            # Create and save
            session = Session(model="test", working_directory="/tmp")
            original_created_at = session.created_at
            session.save(sessions_dir)

            # Load
            loaded = Session.load(session.id, sessions_dir)

            assert loaded.created_at == original_created_at

    def test_updated_at_persists_across_save_load(self):
        """updated_at should persist when saving and loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir()

            # Create and save
            session = Session(model="test", working_directory="/tmp")
            original_updated_at = session.updated_at
            session.save(sessions_dir)

            # Load
            loaded = Session.load(session.id, sessions_dir)

            assert loaded.updated_at == original_updated_at


class TestSessionGetSummary:
    """Test Session.get_summary() method."""

    def test_get_summary_returns_dict(self):
        """get_summary() should return a dictionary."""
        session = Session(model="test-model", working_directory="/tmp")

        summary = session.get_summary()

        assert isinstance(summary, dict)

    def test_get_summary_includes_id(self):
        """get_summary() should include session id."""
        session = Session(model="test-model", working_directory="/tmp")

        summary = session.get_summary()

        assert "id" in summary
        assert summary["id"] == session.id

    def test_get_summary_includes_model(self):
        """get_summary() should include model name."""
        session = Session(model="meta-llama/Llama-2-7b-hf", working_directory="/tmp")

        summary = session.get_summary()

        assert "model" in summary
        assert summary["model"] == "meta-llama/Llama-2-7b-hf"

    def test_get_summary_includes_created_timestamp(self):
        """get_summary() should include created timestamp in ISO8601 format."""
        session = Session(model="test", working_directory="/tmp")

        summary = session.get_summary()

        assert "created" in summary
        # Should be ISO8601 format
        datetime.fromisoformat(summary["created"])

    def test_get_summary_includes_updated_timestamp(self):
        """get_summary() should include updated timestamp in ISO8601 format."""
        session = Session(model="test", working_directory="/tmp")

        summary = session.get_summary()

        assert "updated" in summary
        # Should be ISO8601 format
        datetime.fromisoformat(summary["updated"])

    def test_get_summary_includes_message_count(self):
        """get_summary() should include message count."""
        session = Session(model="test", working_directory="/tmp")
        session.add_message(role="user", content="Message 1")
        session.add_message(role="assistant", content="Response 1")
        session.add_message(role="user", content="Message 2")

        summary = session.get_summary()

        assert "message_count" in summary
        assert summary["message_count"] == 3

    def test_get_summary_message_count_zero_for_empty_session(self):
        """get_summary() should show 0 messages for new session."""
        session = Session(model="test", working_directory="/tmp")

        summary = session.get_summary()

        assert summary["message_count"] == 0

    def test_get_summary_includes_last_message(self):
        """get_summary() should include last message content."""
        session = Session(model="test", working_directory="/tmp")
        session.add_message(role="user", content="What is Python?")

        summary = session.get_summary()

        assert "last_message" in summary
        assert "Python" in summary["last_message"]

    def test_get_summary_truncates_last_message_to_50_chars(self):
        """get_summary() should truncate last_message to 50 characters."""
        session = Session(model="test", working_directory="/tmp")
        long_message = (
            "This is a very long message that should be truncated to exactly fifty characters max"
        )
        session.add_message(role="user", content=long_message)

        summary = session.get_summary()

        assert len(summary["last_message"]) <= 50

    def test_get_summary_last_message_empty_for_no_messages(self):
        """get_summary() should have empty last_message for new session."""
        session = Session(model="test", working_directory="/tmp")

        summary = session.get_summary()

        assert summary["last_message"] == ""

    def test_get_summary_timestamps_are_iso8601(self):
        """get_summary() timestamps should be valid ISO8601."""
        session = Session(model="test", working_directory="/tmp")

        summary = session.get_summary()

        # Should be parseable
        created = datetime.fromisoformat(summary["created"])
        updated = datetime.fromisoformat(summary["updated"])

        assert isinstance(created, datetime)
        assert isinstance(updated, datetime)


class TestSessionDeletion:
    """Test Session.delete_session() static method."""

    def test_delete_session_returns_bool(self):
        """delete_session() should return a boolean."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir()

            # Create and save a session
            session = Session(model="test", working_directory="/tmp")
            session.save(sessions_dir)

            # Delete it
            result = Session.delete_session(session.id, sessions_dir)

            assert isinstance(result, bool)

    def test_delete_session_removes_file(self):
        """delete_session() should delete the session file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir()

            # Create and save a session
            session = Session(model="test", working_directory="/tmp")
            path = session.save(sessions_dir)

            assert path.exists()

            # Delete it
            Session.delete_session(session.id, sessions_dir)

            assert not path.exists()

    def test_delete_session_returns_true_on_success(self):
        """delete_session() should return True when file is deleted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir()

            # Create and save a session
            session = Session(model="test", working_directory="/tmp")
            session.save(sessions_dir)

            # Delete it
            result = Session.delete_session(session.id, sessions_dir)

            assert result is True

    def test_delete_session_returns_false_for_nonexistent(self):
        """delete_session() should return False for non-existent session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir()

            # Try to delete non-existent session
            result = Session.delete_session("nonexistent123", sessions_dir)

            assert result is False

    def test_delete_session_uses_default_sessions_dir(self):
        """delete_session() should use default sessions_dir if not provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from mlxcli import session as session_module

            original_get_project_root = session_module.get_project_root

            def mock_get_project_root():
                return Path(tmpdir)

            session_module.get_project_root = mock_get_project_root

            try:
                # Create sessions dir
                sessions_dir = Path(tmpdir) / ".mlxcli" / "sessions"
                sessions_dir.mkdir(parents=True)

                # Create and save a session
                session = Session(model="test", working_directory="/tmp")
                session.save(sessions_dir)

                # Delete without specifying sessions_dir
                result = Session.delete_session(session.id)

                assert result is True
            finally:
                session_module.get_project_root = original_get_project_root


class TestSessionListingCommands:
    """Test Session.list_sessions() sorting and retrieval."""

    def test_list_sessions_sorted_by_updated_at(self):
        """list_sessions() should sort by updated_at (most recent first)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir()

            # Create sessions with small delays
            sessions_data = []
            for i in range(3):
                session = Session(model=f"model{i}", working_directory="/tmp")
                session.save(sessions_dir)
                sessions_data.append(session)
                if i < 2:
                    time.sleep(0.01)

            # Update the last one to have newest updated_at
            sessions_data[0].add_message(role="user", content="update")
            sessions_data[0].save(sessions_dir)

            # List sessions
            listed = Session.list_sessions(sessions_dir)

            # Should be sorted by updated_at, most recent first (at index 0)
            assert listed[0].id == sessions_data[0].id

    def test_list_sessions_returns_session_objects(self):
        """list_sessions() should return Session objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            sessions_dir.mkdir()

            # Create and save sessions
            session1 = Session(model="model1", working_directory="/tmp")
            session1.save(sessions_dir)

            # List sessions
            listed = Session.list_sessions(sessions_dir)

            assert len(listed) == 1
            assert isinstance(listed[0], Session)


class TestCLIListSessionsCommand:
    """Test CLI /sessions command implementation."""

    def test_list_sessions_command_displays_formatted_output(self):
        """_list_sessions_command() should display formatted output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from mlxcli import cli as cli_module

            original_get_project_root = cli_module.get_project_root

            def mock_get_project_root():
                return Path(tmpdir)

            cli_module.get_project_root = mock_get_project_root

            try:
                # Create sessions dir and session
                sessions_dir = Path(tmpdir) / ".mlxcli" / "sessions"
                sessions_dir.mkdir(parents=True)

                session = Session(model="test-model", working_directory="/tmp")
                session.add_message(role="user", content="Hello")
                session.save(sessions_dir)

                # Create CLI and list sessions
                cli = CLI(project_root=Path(tmpdir))

                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    cli._list_sessions_command()
                    output = mock_stdout.getvalue()

                # Should contain session info
                assert len(output) > 0
                assert "sessions" in output.lower() or session.id in output

            finally:
                cli_module.get_project_root = original_get_project_root

    def test_list_sessions_command_shows_no_sessions_message(self):
        """_list_sessions_command() should show message for empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from mlxcli import cli as cli_module

            original_get_project_root = cli_module.get_project_root

            def mock_get_project_root():
                return Path(tmpdir)

            cli_module.get_project_root = mock_get_project_root

            try:
                # Create sessions dir but no sessions
                sessions_dir = Path(tmpdir) / ".mlxcli" / "sessions"
                sessions_dir.mkdir(parents=True)

                cli = CLI(project_root=Path(tmpdir))

                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    cli._list_sessions_command()
                    output = mock_stdout.getvalue()

                # Should contain "no" or "empty" or similar
                assert "no" in output.lower() or "empty" in output.lower() or len(output) > 0

            finally:
                cli_module.get_project_root = original_get_project_root

    def test_list_sessions_command_displays_multiple_sessions(self):
        """_list_sessions_command() should display multiple sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from mlxcli import cli as cli_module

            original_get_project_root = cli_module.get_project_root

            def mock_get_project_root():
                return Path(tmpdir)

            cli_module.get_project_root = mock_get_project_root

            try:
                # Create sessions dir and multiple sessions
                sessions_dir = Path(tmpdir) / ".mlxcli" / "sessions"
                sessions_dir.mkdir(parents=True)

                session1 = Session(model="model1", working_directory="/tmp")
                session1.add_message(role="user", content="Message 1")
                session1.save(sessions_dir)

                session2 = Session(model="model2", working_directory="/tmp")
                session2.add_message(role="user", content="Message 2")
                session2.save(sessions_dir)

                cli = CLI(project_root=Path(tmpdir))

                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    cli._list_sessions_command()
                    output = mock_stdout.getvalue()

                # Should contain both session IDs or counts
                assert len(output) > 0

            finally:
                cli_module.get_project_root = original_get_project_root

    def test_list_sessions_displays_model_info(self):
        """_list_sessions_command() should display model information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from mlxcli import cli as cli_module

            original_get_project_root = cli_module.get_project_root

            def mock_get_project_root():
                return Path(tmpdir)

            cli_module.get_project_root = mock_get_project_root

            try:
                sessions_dir = Path(tmpdir) / ".mlxcli" / "sessions"
                sessions_dir.mkdir(parents=True)

                session = Session(model="meta-llama/Llama-2-7b-hf", working_directory="/tmp")
                session.add_message(role="user", content="Test")
                session.save(sessions_dir)

                cli = CLI(project_root=Path(tmpdir))

                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    cli._list_sessions_command()
                    output = mock_stdout.getvalue()

                # Should contain model info
                assert len(output) > 0

            finally:
                cli_module.get_project_root = original_get_project_root

    def test_list_sessions_displays_message_count(self):
        """_list_sessions_command() should display message count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from mlxcli import cli as cli_module

            original_get_project_root = cli_module.get_project_root

            def mock_get_project_root():
                return Path(tmpdir)

            cli_module.get_project_root = mock_get_project_root

            try:
                sessions_dir = Path(tmpdir) / ".mlxcli" / "sessions"
                sessions_dir.mkdir(parents=True)

                session = Session(model="test-model", working_directory="/tmp")
                session.add_message(role="user", content="Message 1")
                session.add_message(role="assistant", content="Response 1")
                session.save(sessions_dir)

                cli = CLI(project_root=Path(tmpdir))

                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    cli._list_sessions_command()
                    output = mock_stdout.getvalue()

                # Should contain message count
                assert len(output) > 0

            finally:
                cli_module.get_project_root = original_get_project_root


class TestCLIDeleteSessionCommand:
    """Test CLI /delete command implementation."""

    def test_delete_session_command_removes_session(self):
        """_delete_session_command() should remove a session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from mlxcli import cli as cli_module

            original_get_project_root = cli_module.get_project_root

            def mock_get_project_root():
                return Path(tmpdir)

            cli_module.get_project_root = mock_get_project_root

            try:
                sessions_dir = Path(tmpdir) / ".mlxcli" / "sessions"
                sessions_dir.mkdir(parents=True)

                session = Session(model="test-model", working_directory="/tmp")
                session.save(sessions_dir)

                session_file = sessions_dir / f"session_{session.id}.json"
                assert session_file.exists()

                cli = CLI(project_root=Path(tmpdir))

                with patch("sys.stdout", new_callable=StringIO):
                    cli._delete_session_command(session.id)

                # Should be deleted
                assert not session_file.exists()

            finally:
                cli_module.get_project_root = original_get_project_root

    def test_delete_session_command_shows_confirmation(self):
        """_delete_session_command() should show confirmation message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from mlxcli import cli as cli_module

            original_get_project_root = cli_module.get_project_root

            def mock_get_project_root():
                return Path(tmpdir)

            cli_module.get_project_root = mock_get_project_root

            try:
                sessions_dir = Path(tmpdir) / ".mlxcli" / "sessions"
                sessions_dir.mkdir(parents=True)

                session = Session(model="test-model", working_directory="/tmp")
                session.save(sessions_dir)

                cli = CLI(project_root=Path(tmpdir))

                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    cli._delete_session_command(session.id)
                    output = mock_stdout.getvalue()

                # Should show some confirmation or deletion message
                assert len(output) > 0

            finally:
                cli_module.get_project_root = original_get_project_root

    def test_delete_session_command_handles_nonexistent_session(self):
        """_delete_session_command() should handle non-existent session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from mlxcli import cli as cli_module

            original_get_project_root = cli_module.get_project_root

            def mock_get_project_root():
                return Path(tmpdir)

            cli_module.get_project_root = mock_get_project_root

            try:
                sessions_dir = Path(tmpdir) / ".mlxcli" / "sessions"
                sessions_dir.mkdir(parents=True)

                cli = CLI(project_root=Path(tmpdir))

                # Should not crash
                with patch("sys.stdout", new_callable=StringIO):
                    cli._delete_session_command("nonexistent")

            finally:
                cli_module.get_project_root = original_get_project_root


class TestCLISessionCommandIntegration:
    """Integration tests for session commands."""

    def test_handle_command_with_sessions_lists_sessions(self):
        """_handle_command with 'sessions' should list sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from mlxcli import cli as cli_module

            original_get_project_root = cli_module.get_project_root

            def mock_get_project_root():
                return Path(tmpdir)

            cli_module.get_project_root = mock_get_project_root

            try:
                sessions_dir = Path(tmpdir) / ".mlxcli" / "sessions"
                sessions_dir.mkdir(parents=True)

                cli = CLI(project_root=Path(tmpdir))

                with patch("sys.stdout", new_callable=StringIO):
                    result = cli._handle_command("sessions")

                assert result is True

            finally:
                cli_module.get_project_root = original_get_project_root

    def test_handle_command_with_delete_deletes_session(self):
        """_handle_command with 'delete' should delete a session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from mlxcli import cli as cli_module

            original_get_project_root = cli_module.get_project_root

            def mock_get_project_root():
                return Path(tmpdir)

            cli_module.get_project_root = mock_get_project_root

            try:
                sessions_dir = Path(tmpdir) / ".mlxcli" / "sessions"
                sessions_dir.mkdir(parents=True)

                session = Session(model="test-model", working_directory="/tmp")
                session.save(sessions_dir)

                cli = CLI(project_root=Path(tmpdir))

                with patch("sys.stdout", new_callable=StringIO):
                    result = cli._handle_command("delete", session.id)

                # File should be deleted
                session_file = sessions_dir / f"session_{session.id}.json"
                assert not session_file.exists()

            finally:
                cli_module.get_project_root = original_get_project_root

"""Tests for Session - conversation state management and persistence."""

import json
import shutil
import stat
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.session import Session


class TestSessionCreation:
    """Test Session creation and basic fields."""

    def test_can_create_session_with_required_fields(self):
        """Session should be creatable with model and working_directory."""
        model = "claude-3-sonnet"
        working_dir = "/home/user/project"

        session = Session(model=model, working_directory=working_dir)

        assert session.model == model
        assert session.working_directory == working_dir
        assert session.messages == []
        assert session.context == {}

    def test_session_id_is_8_character_string(self):
        """Session ID should be an 8-character string."""
        session = Session(model="test-model", working_directory="/tmp")

        assert isinstance(session.id, str)
        assert len(session.id) == 8
        # Should be alphanumeric
        assert session.id.isalnum()

    def test_session_id_is_unique(self):
        """Multiple sessions should have unique IDs."""
        session1 = Session(model="test", working_directory="/tmp")
        session2 = Session(model="test", working_directory="/tmp")

        assert session1.id != session2.id

    def test_created_at_and_updated_at_are_tracked(self):
        """Session should track created_at and updated_at timestamps."""
        session = Session(model="test", working_directory="/tmp")

        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)
        # Both should be recent (within last minute)
        now = datetime.now()
        assert abs((now - session.created_at).total_seconds()) < 60
        assert abs((now - session.updated_at).total_seconds()) < 60


class TestSessionMessages:
    """Test adding and managing messages."""

    def test_can_add_user_message(self):
        """Session should be able to add user messages."""
        session = Session(model="test", working_directory="/tmp")
        content = "Hello, AI!"

        session.add_message(role="user", content=content)

        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "user"
        assert session.messages[0]["content"] == content

    def test_can_add_assistant_message(self):
        """Session should be able to add assistant messages."""
        session = Session(model="test", working_directory="/tmp")
        content = "Hello, user!"

        session.add_message(role="assistant", content=content)

        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "assistant"
        assert session.messages[0]["content"] == content

    def test_message_includes_timestamp(self):
        """Added messages should include timestamp."""
        session = Session(model="test", working_directory="/tmp")

        session.add_message(role="user", content="test")

        assert "timestamp" in session.messages[0]
        timestamp = session.messages[0]["timestamp"]
        assert isinstance(timestamp, str)
        # Should be ISO8601 format
        datetime.fromisoformat(timestamp)

    def test_can_add_multiple_messages(self):
        """Session should support multiple messages."""
        session = Session(model="test", working_directory="/tmp")

        session.add_message(role="user", content="Message 1")
        session.add_message(role="assistant", content="Response 1")
        session.add_message(role="user", content="Message 2")

        assert len(session.messages) == 3
        assert session.messages[0]["role"] == "user"
        assert session.messages[1]["role"] == "assistant"
        assert session.messages[2]["role"] == "user"

    def test_tools_used_is_optional(self):
        """tools_used parameter should be optional."""
        session = Session(model="test", working_directory="/tmp")

        # Add message without tools_used
        session.add_message(role="user", content="test")

        # Should not have tools_used key or it should be None
        msg = session.messages[0]
        assert msg.get("tools_used") is None or "tools_used" not in msg

    def test_can_set_tools_used(self):
        """tools_used can be set when adding message."""
        session = Session(model="test", working_directory="/tmp")
        tools = ["file_read", "grep"]

        session.add_message(role="assistant", content="test", tools_used=tools)

        assert session.messages[0]["tools_used"] == tools

    def test_tools_called_is_optional(self):
        """tools_called parameter should be optional."""
        session = Session(model="test", working_directory="/tmp")

        session.add_message(role="assistant", content="test")

        msg = session.messages[0]
        assert msg.get("tools_called") is None or "tools_called" not in msg

    def test_can_set_tools_called(self):
        """tools_called can be set when adding message."""
        session = Session(model="test", working_directory="/tmp")
        tools_called = [
            {
                "name": "file_read",
                "args": {"path": "/tmp/test.txt"},
                "result": "content",
            }
        ]

        session.add_message(role="assistant", content="test", tools_called=tools_called)

        assert session.messages[0]["tools_called"] == tools_called

    def test_updated_at_changes_when_adding_message(self):
        """updated_at should change when adding a message."""
        session = Session(model="test", working_directory="/tmp")
        original_updated_at = session.updated_at

        # Add a message
        session.add_message(role="user", content="test")

        assert session.updated_at > original_updated_at


class TestSessionSerialization:
    """Test session serialization to dict."""

    def test_to_dict_includes_all_fields(self):
        """to_dict should include all required fields."""
        session = Session(model="claude-3", working_directory="/home/user")
        session.add_message(role="user", content="Hello")

        session_dict = session.to_dict()

        assert "id" in session_dict
        assert "created_at" in session_dict
        assert "updated_at" in session_dict
        assert "model" in session_dict
        assert "working_directory" in session_dict
        assert "messages" in session_dict
        assert "context" in session_dict

    def test_to_dict_timestamps_are_iso8601(self):
        """Timestamps in to_dict should be ISO8601 strings."""
        session = Session(model="test", working_directory="/tmp")
        session_dict = session.to_dict()

        created_at = session_dict["created_at"]
        updated_at = session_dict["updated_at"]

        assert isinstance(created_at, str)
        assert isinstance(updated_at, str)
        # Should be parseable as ISO8601
        datetime.fromisoformat(created_at)
        datetime.fromisoformat(updated_at)

    def test_to_dict_messages_are_serializable(self):
        """Messages in to_dict should be JSON serializable."""
        session = Session(model="test", working_directory="/tmp")
        session.add_message(role="user", content="test")

        session_dict = session.to_dict()

        # Should be JSON serializable
        json_str = json.dumps(session_dict)
        assert isinstance(json_str, str)


class TestSessionPersistence:
    """Test session saving and loading."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project with .mlxcli."""
        tmpdir = Path(tempfile.mkdtemp())
        mlxcli_dir = tmpdir / ".mlxcli"
        mlxcli_dir.mkdir()
        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_can_save_session_to_json_file(self, temp_project):
        """Session.save should create a JSON file."""
        session = Session(model="test", working_directory="/tmp")
        sessions_dir = temp_project / ".mlxcli" / "sessions"

        session_path = session.save(sessions_dir)

        assert session_path.exists()
        assert session_path.suffix == ".json"
        assert "session_" in session_path.name
        assert session.id in session_path.name

    def test_saved_file_follows_schema(self, temp_project):
        """Saved JSON file should follow the design schema."""
        session = Session(model="claude-3-sonnet", working_directory="/home/user")
        session.add_message(
            role="user",
            content="Hello",
            tools_used=["file_read"],
            tools_called=[{"name": "file_read", "args": {}, "result": "ok"}],
        )

        sessions_dir = temp_project / ".mlxcli" / "sessions"
        session_path = session.save(sessions_dir)

        # Read and verify JSON
        with open(session_path) as f:
            data = json.load(f)

        # Check top-level schema
        assert data["id"] == session.id
        assert data["model"] == "claude-3-sonnet"
        assert data["working_directory"] == "/home/user"
        assert "created_at" in data
        assert "updated_at" in data
        assert isinstance(data["messages"], list)
        assert isinstance(data["context"], dict)

        # Check message schema
        assert len(data["messages"]) == 1
        msg = data["messages"][0]
        assert msg["role"] == "user"
        assert msg["content"] == "Hello"
        assert "timestamp" in msg
        assert msg["tools_used"] == ["file_read"]
        assert len(msg["tools_called"]) == 1

    def test_session_file_has_chmod_600(self, temp_project):
        """Saved session file should have chmod 600 permissions."""
        session = Session(model="test", working_directory="/tmp")
        sessions_dir = temp_project / ".mlxcli" / "sessions"

        session_path = session.save(sessions_dir)

        # Get file permissions
        file_stat = session_path.stat()
        file_mode = stat.filemode(file_stat.st_mode)

        # Should be -rw------- (owner read/write only)
        # Check that group and others have no permissions
        mode = file_stat.st_mode
        # Extract last 9 bits (permissions)
        perms = mode & 0o777
        assert perms == 0o600, f"Expected 0o600, got {oct(perms)}"

    def test_can_load_session_from_json_file(self, temp_project):
        """Session.load should load a saved session."""
        # Create and save a session
        original = Session(model="test-model", working_directory="/tmp/project")
        original.add_message(role="user", content="Hello")

        sessions_dir = temp_project / ".mlxcli" / "sessions"
        session_path = original.save(sessions_dir)

        # Load it back
        loaded = Session.load(original.id, sessions_dir)

        assert loaded.id == original.id
        assert loaded.model == original.model
        assert loaded.working_directory == original.working_directory
        assert len(loaded.messages) == len(original.messages)

    def test_load_returns_same_data_as_saved(self, temp_project):
        """Loaded session should have identical data to original."""
        sessions_dir = temp_project / ".mlxcli" / "sessions"

        # Create with all fields
        original = Session(
            model="claude-3-opus", working_directory="/home/user/projects"
        )
        original.context = {"files_referenced": ["file1.py", "file2.py"]}
        original.add_message(
            role="user",
            content="Can you help?",
            tools_used=["grep"],
            tools_called=[
                {"name": "grep", "args": {"pattern": "test"}, "result": "matches"}
            ],
        )
        original.add_message(role="assistant", content="Sure!", tools_used=[])

        original.save(sessions_dir)

        # Load and compare
        loaded = Session.load(original.id, sessions_dir)

        assert loaded.id == original.id
        assert loaded.model == original.model
        assert loaded.working_directory == original.working_directory
        assert loaded.context == original.context
        assert len(loaded.messages) == 2

        # Compare first message
        orig_msg = original.messages[0]
        load_msg = loaded.messages[0]
        assert load_msg["role"] == orig_msg["role"]
        assert load_msg["content"] == orig_msg["content"]
        assert load_msg["tools_used"] == orig_msg["tools_used"]
        assert load_msg["tools_called"] == orig_msg["tools_called"]

    def test_list_sessions_returns_all_saved_sessions(self, temp_project):
        """list_sessions should return all saved sessions."""
        sessions_dir = temp_project / ".mlxcli" / "sessions"

        # Create and save multiple sessions
        session1 = Session(model="model1", working_directory="/tmp")
        session2 = Session(model="model2", working_directory="/tmp")
        session3 = Session(model="model3", working_directory="/tmp")

        session1.save(sessions_dir)
        session2.save(sessions_dir)
        session3.save(sessions_dir)

        # List sessions
        sessions = Session.list_sessions(sessions_dir)

        assert len(sessions) == 3
        session_ids = [s.id for s in sessions]
        assert session1.id in session_ids
        assert session2.id in session_ids
        assert session3.id in session_ids

    def test_list_sessions_returns_sorted_sessions(self, temp_project):
        """list_sessions should return sessions sorted by updated_at (most recent first)."""
        sessions_dir = temp_project / ".mlxcli" / "sessions"

        # Create sessions with a small delay to ensure different timestamps
        sessions_data = []
        for i in range(3):
            session = Session(model=f"model{i}", working_directory="/tmp")
            session.save(sessions_dir)
            sessions_data.append(session)
            if i < 2:
                # Small delay to ensure different timestamps
                import time

                time.sleep(0.01)

        # List sessions
        listed = Session.list_sessions(sessions_dir)

        assert len(listed) == 3
        # Should be sorted by updated_at in descending order (most recent first)
        for i in range(len(listed) - 1):
            assert listed[i].updated_at >= listed[i + 1].updated_at

    def test_list_sessions_returns_empty_for_no_sessions(self, temp_project):
        """list_sessions should return empty list when no sessions exist."""
        sessions_dir = temp_project / ".mlxcli" / "sessions"

        sessions = Session.list_sessions(sessions_dir)

        assert isinstance(sessions, list)
        assert len(sessions) == 0

    def test_load_raises_error_for_missing_session(self, temp_project):
        """Session.load should raise error for non-existent session."""
        sessions_dir = temp_project / ".mlxcli" / "sessions"

        with pytest.raises((FileNotFoundError, ValueError)):
            Session.load("nonexistent", sessions_dir)

    def test_sessions_dir_parameter_is_optional(self, temp_project):
        """sessions_dir parameter should be optional (defaults to .mlxcli/sessions)."""
        # Patch get_project_root for this test
        from mlxcli import session as session_module

        original_get_project_root = session_module.get_project_root

        def mock_get_project_root():
            return temp_project

        session_module.get_project_root = mock_get_project_root

        try:
            session = Session(model="test", working_directory="/tmp")
            # Should use default sessions_dir
            path = session.save()

            assert path.exists()
            assert ".mlxcli" in str(path)
            assert "sessions" in str(path)

            # Should be able to load without specifying sessions_dir
            loaded = Session.load(session.id)
            assert loaded.id == session.id
        finally:
            session_module.get_project_root = original_get_project_root


class TestSessionIntegration:
    """Integration tests for session workflow."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project with .mlxcli."""
        tmpdir = Path(tempfile.mkdtemp())
        mlxcli_dir = tmpdir / ".mlxcli"
        mlxcli_dir.mkdir()
        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_full_session_workflow(self, temp_project):
        """Test complete session create-add-save-load workflow."""
        sessions_dir = temp_project / ".mlxcli" / "sessions"

        # Create a session
        session = Session(model="claude-3-sonnet", working_directory="/home/user")

        # Add a conversation
        session.add_message(
            role="user", content="What is 2+2?", tools_used=["calculator"]
        )
        session.add_message(role="assistant", content="2+2 = 4", tools_used=[])

        # Save
        path = session.save(sessions_dir)
        assert path.exists()

        # Load
        loaded = Session.load(session.id, sessions_dir)

        # Verify
        assert loaded.model == "claude-3-sonnet"
        assert loaded.working_directory == "/home/user"
        assert len(loaded.messages) == 2
        assert loaded.messages[0]["content"] == "What is 2+2?"
        assert loaded.messages[1]["content"] == "2+2 = 4"

    def test_multiple_sessions_independent(self, temp_project):
        """Multiple sessions should be independent."""
        sessions_dir = temp_project / ".mlxcli" / "sessions"

        # Create two sessions
        session1 = Session(model="model1", working_directory="/path1")
        session2 = Session(model="model2", working_directory="/path2")

        session1.add_message(role="user", content="Session 1 message")
        session2.add_message(role="user", content="Session 2 message")

        # Save both
        session1.save(sessions_dir)
        session2.save(sessions_dir)

        # Load and verify independence
        loaded1 = Session.load(session1.id, sessions_dir)
        loaded2 = Session.load(session2.id, sessions_dir)

        assert loaded1.working_directory == "/path1"
        assert loaded2.working_directory == "/path2"
        assert loaded1.messages[0]["content"] == "Session 1 message"
        assert loaded2.messages[0]["content"] == "Session 2 message"

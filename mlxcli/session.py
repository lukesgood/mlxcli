"""Session management for conversation state and persistence."""

import json
import random
import string
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from mlxcli.utils import get_project_root


@dataclass
class Session:
    """Manages conversation state and persists to JSON.

    Attributes:
        id: Auto-generated 8-character session identifier.
        model: LLM model being used.
        working_directory: Current working directory for the session.
        created_at: Timestamp when session was created.
        updated_at: Timestamp when session was last modified.
        messages: List of conversation messages.
        context: Dictionary for additional context (e.g., files referenced).
        sessions_dir: Path to sessions directory (not persisted to JSON).
    """

    model: str
    working_directory: str
    id: str = field(
        default_factory=lambda: "".join(
            random.choices(string.ascii_letters + string.digits, k=8)
        )
    )
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    messages: list = field(default_factory=list)
    context: dict = field(default_factory=dict)
    sessions_dir: Optional[Path] = field(default=None, repr=False, compare=False)

    def add_message(
        self,
        role: str,
        content: str,
        tools_used: Optional[list] = None,
        tools_called: Optional[list] = None,
    ) -> None:
        """Add a message to the conversation.

        Args:
            role: Either "user" or "assistant".
            content: Message content/text.
            tools_used: Optional list of tool names used in this message.
            tools_called: Optional list of tool call records with name, args, result.
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }

        if tools_used is not None:
            message["tools_used"] = tools_used

        if tools_called is not None:
            message["tools_called"] = tools_called

        self.messages.append(message)
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert session to dictionary suitable for JSON serialization.

        Returns:
            Dictionary representation of the session with ISO8601 timestamps.
        """
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "model": self.model,
            "working_directory": self.working_directory,
            "messages": self.messages,
            "context": self.context,
        }

    def save(self, sessions_dir: Optional[Path] = None) -> Path:
        """Save session to JSON file in .mlxcli/sessions/.

        Args:
            sessions_dir: Path to sessions directory. If None, uses default.

        Returns:
            Path to the saved session file.
        """
        if sessions_dir is None:
            sessions_dir = self._get_default_sessions_dir()

        # Ensure sessions directory exists
        sessions_dir.mkdir(parents=True, exist_ok=True)

        # Create session file path
        session_file = sessions_dir / f"session_{self.id}.json"

        # Write JSON file
        with open(session_file, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

        # Set permissions to 600 (owner read/write only)
        session_file.chmod(0o600)

        return session_file

    @staticmethod
    def load(session_id: str, sessions_dir: Optional[Path] = None) -> "Session":
        """Load a session from a JSON file.

        Args:
            session_id: The session ID to load.
            sessions_dir: Path to sessions directory. If None, uses default.

        Returns:
            Loaded Session instance.

        Raises:
            FileNotFoundError: If session file doesn't exist.
        """
        if sessions_dir is None:
            sessions_dir = Session._get_default_sessions_dir()

        session_file = sessions_dir / f"session_{session_id}.json"

        if not session_file.exists():
            raise FileNotFoundError(f"Session file not found: {session_file}")

        # Read and parse JSON
        with open(session_file, "r") as f:
            data = json.load(f)

        # Create Session instance
        session = Session(
            id=data["id"],
            model=data["model"],
            working_directory=data["working_directory"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            messages=data.get("messages", []),
            context=data.get("context", {}),
        )

        return session

    def get_summary(self) -> dict:
        """Get session summary for display.

        Returns:
            Dictionary with keys:
            - id: Session ID
            - model: Model name
            - created: ISO8601 created timestamp
            - updated: ISO8601 updated timestamp
            - message_count: Number of messages
            - last_message: First 50 chars of last message (empty if no messages)
        """
        # Get last message content, truncated to 50 chars
        last_message = ""
        if self.messages:
            last_msg_content = self.messages[-1].get("content", "")
            last_message = last_msg_content[:50]

        return {
            "id": self.id,
            "model": self.model,
            "created": self.created_at.isoformat(),
            "updated": self.updated_at.isoformat(),
            "message_count": len(self.messages),
            "last_message": last_message,
        }

    @staticmethod
    def delete_session(session_id: str, sessions_dir: Optional[Path] = None) -> bool:
        """Delete a session file.

        Args:
            session_id: The session ID to delete.
            sessions_dir: Path to sessions directory. If None, uses default.

        Returns:
            True if deleted, False if not found.
        """
        if sessions_dir is None:
            sessions_dir = Session._get_default_sessions_dir()

        session_file = sessions_dir / f"session_{session_id}.json"

        if not session_file.exists():
            return False

        session_file.unlink()
        return True

    @staticmethod
    def list_sessions(sessions_dir: Optional[Path] = None) -> list["Session"]:
        """List all saved sessions.

        Args:
            sessions_dir: Path to sessions directory. If None, uses default.

        Returns:
            List of Session instances sorted by updated_at (most recent first).
        """
        if sessions_dir is None:
            sessions_dir = Session._get_default_sessions_dir()

        if not sessions_dir.exists():
            return []

        sessions = []
        for session_file in sessions_dir.glob("session_*.json"):
            try:
                session_id = session_file.stem.replace("session_", "")
                session = Session.load(session_id, sessions_dir)
                sessions.append(session)
            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                # Skip corrupted session files
                pass

        # Sort by updated_at in ascending order, then reverse to get most recent first
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions

    @staticmethod
    def recover_corrupted(
        session_id: str, sessions_dir: Optional[Path] = None
    ) -> "Session":
        """Recover from a corrupted session by creating a new session.

        Creates a new session with the same session_id. The corrupted session
        file is not deleted, allowing manual recovery if needed. This method
        is useful when a session file is corrupted and cannot be loaded.

        Args:
            session_id: The ID of the corrupted session.
            sessions_dir: Path to sessions directory. If None, uses default.

        Returns:
            A new Session instance with the same session_id.
        """
        # Create a new session with the given ID
        session = Session(model="claude-3-sonnet", working_directory="/")
        # Override the auto-generated ID with the provided one
        session.id = session_id

        return session

    @staticmethod
    def _get_default_sessions_dir() -> Path:
        """Get default sessions directory path.

        Returns:
            Path to .mlxcli/sessions directory.
        """
        project_root = get_project_root()
        sessions_dir = project_root / ".mlxcli" / "sessions"
        return sessions_dir

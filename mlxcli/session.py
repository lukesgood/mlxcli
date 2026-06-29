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

    @staticmethod
    def list_sessions(sessions_dir: Optional[Path] = None) -> list["Session"]:
        """List all saved sessions.

        Args:
            sessions_dir: Path to sessions directory. If None, uses default.

        Returns:
            List of Session instances sorted by created_at.
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

        # Sort by created_at
        sessions.sort(key=lambda s: s.created_at)
        return sessions

    @staticmethod
    def _get_default_sessions_dir() -> Path:
        """Get default sessions directory path.

        Returns:
            Path to .mlxcli/sessions directory.
        """
        project_root = get_project_root()
        sessions_dir = project_root / ".mlxcli" / "sessions"
        return sessions_dir

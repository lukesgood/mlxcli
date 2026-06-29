"""FileTool - file operations with auto-backup."""

from pathlib import Path
from typing import Optional

from mlxcli.tools.base import Tool
from mlxcli.utils import get_project_root, is_within_project, should_ignore_path


class FileTool(Tool):
    """Tool for file operations with auto-backup capabilities.

    Provides read, write, and list_dir operations with the following features:
    - Auto-backup before file writes (creates .bak file)
    - Respects .gitignore when reading directories
    - Prevents writes outside project directory
    - Graceful error handling for permission issues
    """

    @property
    def name(self) -> str:
        """Tool name/identifier."""
        return "file_tool"

    @property
    def description(self) -> str:
        """Tool description for LLM."""
        return (
            "File operations tool with auto-backup. Supports read, write, and list_dir actions. "
            "Auto-creates .bak files before overwriting. Respects .gitignore patterns. "
            "Prevents writes outside project directory."
        )

    def execute(self, args: dict) -> dict:
        """Execute file operation.

        Args:
            args: Dictionary with required keys:
                - action: "read", "write", or "list_dir"
                - path: file or directory path
                - content: (for write action) file content

        Returns:
            dict: Result with "status" and operation-specific fields.
        """
        action = args.get("action")

        if action == "read":
            return self._read_file(args.get("path"))
        elif action == "write":
            return self._write_file(args.get("path"), args.get("content"))
        elif action == "list_dir":
            return self._list_dir(args.get("path"))
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    def _read_file(self, path: Optional[str]) -> dict:
        """Read a file.

        Args:
            path: Path to file to read.

        Returns:
            dict: {"status": "ok", "content": str, "path": str} or error dict.
        """
        if path is None:
            return {"status": "error", "message": "path is required for read action"}

        try:
            file_path = Path(path).resolve()

            # Check if file exists
            if not file_path.exists():
                return {
                    "status": "error",
                    "message": f"File not found: {path}",
                }

            # Read file
            content = file_path.read_text()
            return {
                "status": "ok",
                "content": content,
                "path": str(file_path),
            }

        except PermissionError:
            return {
                "status": "error",
                "message": f"Permission denied reading file: {path}",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error reading file: {str(e)}",
            }

    def _write_file(self, path: Optional[str], content: Optional[str]) -> dict:
        """Write a file with auto-backup.

        Args:
            path: Path to file to write.
            content: Content to write.

        Returns:
            dict: {"status": "ok", "path": str, "backup_created": bool, "size": int} or error dict.
        """
        if path is None:
            return {"status": "error", "message": "path is required for write action"}
        if content is None:
            return {
                "status": "error",
                "message": "content is required for write action",
            }

        try:
            file_path = Path(path).resolve()
            project_root = get_project_root()

            # Check if path is within project
            if not is_within_project(file_path, project_root):
                return {
                    "status": "error",
                    "message": f"Cannot write outside project directory: {path}",
                }

            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if file exists (for backup)
            backup_created = False
            if file_path.exists():
                # Create backup
                backup_path = Path(str(file_path) + ".bak")
                file_path.rename(backup_path)
                backup_created = True

            # Write new content
            file_path.write_text(content)

            # If it's a session file, set secure permissions (chmod 600)
            if file_path.name.endswith(".session.json") or ".sessions/" in str(
                file_path
            ):
                file_path.chmod(0o600)

            return {
                "status": "ok",
                "path": str(file_path),
                "backup_created": backup_created,
                "size": len(content.encode()),
            }

        except PermissionError:
            return {
                "status": "error",
                "message": f"Permission denied writing file: {path}",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error writing file: {str(e)}",
            }

    def _list_dir(self, path: Optional[str]) -> dict:
        """List directory contents, respecting .gitignore.

        Args:
            path: Path to directory to list.

        Returns:
            dict: {"status": "ok", "path": str, "files": [str], "dirs": [str]} or error dict.
        """
        if path is None:
            return {
                "status": "error",
                "message": "path is required for list_dir action",
            }

        try:
            dir_path = Path(path).resolve()

            # Check if directory exists
            if not dir_path.exists():
                return {
                    "status": "error",
                    "message": f"Directory not found: {path}",
                }

            if not dir_path.is_dir():
                return {
                    "status": "error",
                    "message": f"Not a directory: {path}",
                }

            # Get project root for .gitignore context
            try:
                project_root = get_project_root()
            except RuntimeError:
                project_root = None

            files = []
            dirs = []

            # List directory contents
            for item in dir_path.iterdir():
                # Skip if should be ignored
                if should_ignore_path(item, project_root):
                    continue

                if item.is_dir():
                    dirs.append(item.name)
                else:
                    files.append(item.name)

            files.sort()
            dirs.sort()

            return {
                "status": "ok",
                "path": str(dir_path),
                "files": files,
                "dirs": dirs,
            }

        except PermissionError:
            return {
                "status": "error",
                "message": f"Permission denied listing directory: {path}",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error listing directory: {str(e)}",
            }

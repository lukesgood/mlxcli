"""ProjectContext - auto-discovery of project structure and metadata."""

from pathlib import Path
from typing import Optional, Dict, Any
from functools import cached_property

from mlxcli.utils import get_project_root, should_ignore_path


class ProjectContext:
    """Auto-discovers and manages project context.

    Provides lazy-loaded properties for:
    - Project type detection (Python, Node.js, Rust, Go, or unknown)
    - File tree representation respecting .gitignore patterns
    - Project metadata (files, README excerpt, structure info)

    Attributes:
        project_root: The project root directory (resolved from Path or auto-detected)
    """

    # Default directories to always ignore
    DEFAULT_IGNORE_DIRS = {".git", ".mlxcli", "__pycache__", ".pytest_cache", ".venv", "venv"}

    def __init__(self, project_root: Optional[Path] = None) -> None:
        """Initialize ProjectContext.

        Args:
            project_root: Path to project root. If None, attempts auto-detection.
                         Can be a Path object or string.

        Raises:
            RuntimeError: If project_root is not provided and cannot be auto-detected.
        """
        if project_root is None:
            self._project_root = get_project_root()
        else:
            path = Path(project_root)
            if path.is_file():
                path = path.parent
            self._project_root = path.resolve()

    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return self._project_root

    @cached_property
    def project_type(self) -> str:
        """Detect and return the project type.

        Detection order:
        1. Python: pyproject.toml, setup.py, or requirements.txt
        2. Node.js: package.json
        3. Rust: Cargo.toml
        4. Go: go.mod
        5. Unknown: if no match

        Returns:
            str: One of "python", "nodejs", "rust", "go", "unknown"
        """
        # Python detection
        if (self._project_root / "pyproject.toml").exists():
            return "python"
        if (self._project_root / "setup.py").exists():
            return "python"
        if (self._project_root / "requirements.txt").exists():
            return "python"

        # Node.js detection
        if (self._project_root / "package.json").exists():
            return "nodejs"

        # Rust detection
        if (self._project_root / "Cargo.toml").exists():
            return "rust"

        # Go detection
        if (self._project_root / "go.mod").exists():
            return "go"

        return "unknown"

    @cached_property
    def file_tree(self) -> str:
        """Generate a tree-like representation of the project structure.

        Respects .gitignore patterns and always excludes:
        - .git
        - .mlxcli
        - __pycache__
        - .pytest_cache
        - .venv
        - venv

        Max depth is 3 levels to avoid huge outputs.

        Returns:
            str: Formatted tree representation of the project.
        """
        lines = []
        self._build_tree(self._project_root, "", 0, lines)
        return "\n".join(lines)

    def _build_tree(
        self, path: Path, prefix: str, depth: int, lines: list[str], is_last: bool = True
    ) -> None:
        """Recursively build tree representation.

        Args:
            path: Current path being processed.
            prefix: Current indentation prefix.
            depth: Current depth in tree (max 3).
            lines: List to accumulate tree lines.
            is_last: Whether this is the last item in parent's children.
        """
        max_depth = 3

        # Don't go deeper than max_depth
        if depth >= max_depth:
            return

        # Check if path should be ignored
        if self._should_ignore(path):
            return

        # Get name of the item
        name = path.name
        connector = "└── " if is_last else "├── "

        # Add to lines only if not the root
        if depth > 0:
            lines.append(f"{prefix}{connector}{name}")

        # If it's a directory, process children
        if path.is_dir():
            try:
                entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            except (PermissionError, OSError):
                return

            # Filter and process children
            children = [e for e in entries if not self._should_ignore(e)]

            for i, child in enumerate(children):
                is_last_child = i == len(children) - 1
                # Calculate new prefix
                if depth > 0:
                    extension = "    " if is_last else "│   "
                    new_prefix = prefix + extension
                else:
                    new_prefix = ""

                self._build_tree(child, new_prefix, depth + 1, lines, is_last_child)

    def _should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored.

        Args:
            path: Path to check.

        Returns:
            bool: True if the path should be ignored.
        """
        # Check default ignore list
        if path.name in self.DEFAULT_IGNORE_DIRS:
            return True

        # Check .gitignore patterns
        if should_ignore_path(path, self._project_root):
            return True

        return False

    @cached_property
    def metadata(self) -> Dict[str, Any]:
        """Extract project metadata.

        Returns:
            dict: Metadata including:
                - top_level_files: List of files in project root
                - readme_excerpt: First 500 chars of README.md if exists
                - project_type: Detected project type
                - has_src: Whether src/ directory exists
                - has_tests: Whether tests/ directory exists
        """
        metadata: Dict[str, Any] = {}

        # Top-level files
        try:
            top_level = sorted([
                item.name for item in self._project_root.iterdir()
                if item.is_file() and not item.name.startswith(".")
            ])
            metadata["top_level_files"] = top_level
        except (PermissionError, OSError):
            metadata["top_level_files"] = []

        # README excerpt
        readme_path = self._project_root / "README.md"
        if readme_path.exists():
            try:
                content = readme_path.read_text(encoding="utf-8")
                metadata["readme_excerpt"] = content[:500]
            except (OSError, UnicodeDecodeError):
                metadata["readme_excerpt"] = None
        else:
            metadata["readme_excerpt"] = None

        # Project type
        metadata["project_type"] = self.project_type

        # Directory checks
        metadata["has_src"] = (self._project_root / "src").is_dir()
        metadata["has_tests"] = (
            (self._project_root / "tests").is_dir() or
            (self._project_root / "test").is_dir()
        )

        return metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert ProjectContext to dictionary.

        Returns:
            dict: Dictionary with all properties:
                - project_root: Project root path as string
                - project_type: Detected project type
                - file_tree: Formatted tree representation
                - metadata: Project metadata dictionary
        """
        return {
            "project_root": str(self.project_root),
            "project_type": self.project_type,
            "file_tree": self.file_tree,
            "metadata": self.metadata,
        }

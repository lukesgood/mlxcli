"""Utility functions for MLX-CLI."""

import fnmatch
from pathlib import Path
from typing import Optional


def get_project_root(start_path: Optional[Path] = None) -> Path:
    """Find project root by looking for .mlxcli or .git marker.

    Args:
        start_path: Starting path to search from. Defaults to current working directory.

    Returns:
        Path: The project root directory.

    Raises:
        RuntimeError: If no project root marker is found.
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path)

    current = start_path.resolve()

    # Search up the directory tree
    while True:
        # Check for .mlxcli marker
        if (current / ".mlxcli").exists():
            return current

        # Check for .git marker
        if (current / ".git").exists():
            return current

        # Move to parent
        parent = current.parent
        if parent == current:
            # Reached filesystem root
            raise RuntimeError(
                f"Could not find project root (.mlxcli or .git marker) starting from {start_path}"
            )
        current = parent


def ensure_project_root_dir() -> Path:
    """Create/verify .mlxcli directory in project root.

    Returns:
        Path: The .mlxcli directory path.
    """
    root = get_project_root()
    mlxcli_dir = root / ".mlxcli"
    mlxcli_dir.mkdir(exist_ok=True)
    return mlxcli_dir


def is_within_project(path: Path, project_root: Optional[Path] = None) -> bool:
    """Check if a path is within the project directory.

    Args:
        path: Path to check.
        project_root: Project root directory. If None, attempts to find it.

    Returns:
        bool: True if path is within project, False otherwise.
    """
    path = Path(path).resolve()

    if project_root is None:
        try:
            project_root = get_project_root()
        except RuntimeError:
            return False

    project_root = Path(project_root).resolve()

    try:
        path.relative_to(project_root)
        return True
    except ValueError:
        return False


def _load_gitignore_patterns(project_root: Path) -> list[str]:
    """Load .gitignore patterns from project root.

    Args:
        project_root: Project root directory.

    Returns:
        list[str]: List of gitignore patterns.
    """
    gitignore_path = project_root / ".gitignore"
    patterns = []

    if gitignore_path.exists():
        try:
            with open(gitignore_path, "r") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith("#"):
                        patterns.append(line)
        except (OSError, IOError):
            pass

    return patterns


def should_ignore_path(path: Path, project_root: Optional[Path] = None) -> bool:
    """Check if a path should be ignored based on .gitignore patterns.

    Args:
        path: Path to check.
        project_root: Project root directory. If None, attempts to find it.

    Returns:
        bool: True if path should be ignored, False otherwise.
    """
    path = Path(path)

    if project_root is None:
        try:
            project_root = get_project_root()
        except RuntimeError:
            return False

    project_root = Path(project_root).resolve()

    # Resolve path for comparison
    path = path.resolve()

    # Get relative path from project root
    try:
        rel_path = path.relative_to(project_root)
    except ValueError:
        # Path is not within project root
        return False

    # Load patterns
    patterns = _load_gitignore_patterns(project_root)

    # Convert rel_path to string for pattern matching
    rel_path_str = str(rel_path).replace("\\", "/")
    rel_path_name = rel_path.name

    # Check each pattern
    for pattern in patterns:
        # Handle directory patterns (ending with /)
        if pattern.endswith("/"):
            pattern_no_slash = pattern.rstrip("/")
            # Check if this is a directory path match
            if fnmatch.fnmatch(rel_path_name, pattern_no_slash):
                return True
            # Also check full path
            if fnmatch.fnmatch(rel_path_str, pattern_no_slash + "/*"):
                return True
            # Also check if any parent directory matches
            for part in rel_path.parts:
                if fnmatch.fnmatch(part, pattern_no_slash):
                    return True
        else:
            # Handle file patterns - match against basename and full path
            if fnmatch.fnmatch(rel_path_name, pattern):
                return True
            if fnmatch.fnmatch(rel_path_str, pattern):
                return True

    return False

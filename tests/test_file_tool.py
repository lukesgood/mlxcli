"""Tests for FileTool - file operations with auto-backup."""

import pytest
from pathlib import Path
import sys
import tempfile
import shutil
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.tools.file_tool import FileTool
from mlxcli.utils import (
    get_project_root,
    ensure_project_root_dir,
    is_within_project,
    should_ignore_path,
)


class TestFileTool:
    """Test FileTool implementation."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory with .mlxcli marker."""
        tmpdir = Path(tempfile.mkdtemp())
        mlxcli_dir = tmpdir / ".mlxcli"
        mlxcli_dir.mkdir()
        yield tmpdir
        shutil.rmtree(tmpdir)

    @pytest.fixture
    def file_tool(self, temp_project):
        """Create a FileTool instance with temp project."""
        # Patch get_project_root to use temp_project
        original_get_project_root = get_project_root

        def mock_get_project_root():
            return temp_project

        import mlxcli.tools.file_tool as ft_module
        ft_module.get_project_root = mock_get_project_root

        yield FileTool()

        # Restore original
        ft_module.get_project_root = original_get_project_root

    def test_file_tool_has_name_property(self, file_tool):
        """FileTool should have a name property."""
        assert hasattr(file_tool, "name")
        assert isinstance(file_tool.name, str)
        assert len(file_tool.name) > 0

    def test_file_tool_has_description_property(self, file_tool):
        """FileTool should have a description property."""
        assert hasattr(file_tool, "description")
        assert isinstance(file_tool.description, str)
        assert len(file_tool.description) > 0

    def test_file_tool_can_read_existing_file(self, temp_project, file_tool):
        """FileTool can read existing files."""
        # Create a test file
        test_file = temp_project / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)

        result = file_tool.execute({"action": "read", "path": str(test_file)})

        assert result["status"] == "ok"
        assert result["content"] == test_content
        # Compare resolved paths to handle symlink/realpath differences on macOS
        assert Path(result["path"]).resolve() == test_file.resolve()

    def test_file_tool_returns_error_for_nonexistent_file(self, temp_project, file_tool):
        """FileTool returns error for non-existent files."""
        nonexistent = temp_project / "nonexistent.txt"

        result = file_tool.execute({"action": "read", "path": str(nonexistent)})

        assert result["status"] == "error"
        assert "message" in result

    def test_file_tool_creates_backup_before_overwriting(self, temp_project, file_tool):
        """FileTool creates .bak backup before overwriting file."""
        test_file = temp_project / "test.txt"
        original_content = "Original content"
        test_file.write_text(original_content)

        new_content = "New content"
        result = file_tool.execute(
            {"action": "write", "path": str(test_file), "content": new_content}
        )

        assert result["status"] == "ok"
        assert result["backup_created"] is True

        # Check backup file exists
        backup_file = Path(str(test_file) + ".bak")
        assert backup_file.exists()
        assert backup_file.read_text() == original_content

    def test_file_tool_can_create_new_files_without_backup(self, temp_project, file_tool):
        """FileTool can create new files without backup."""
        new_file = temp_project / "new.txt"
        content = "New file content"

        result = file_tool.execute(
            {"action": "write", "path": str(new_file), "content": content}
        )

        assert result["status"] == "ok"
        assert result["backup_created"] is False
        assert new_file.read_text() == content

    def test_file_tool_can_list_directories(self, temp_project, file_tool):
        """FileTool can list directory contents."""
        # Create some test files
        (temp_project / "file1.txt").write_text("content1")
        (temp_project / "file2.txt").write_text("content2")
        (temp_project / "subdir").mkdir()

        result = file_tool.execute({"action": "list_dir", "path": str(temp_project)})

        assert result["status"] == "ok"
        assert "files" in result
        assert "file1.txt" in result["files"]
        assert "file2.txt" in result["files"]

    def test_file_tool_respects_gitignore_patterns(self, temp_project, file_tool):
        """FileTool respects .gitignore patterns when listing."""
        # Create .gitignore
        gitignore_content = "*.log\n__pycache__/\n.DS_Store"
        (temp_project / ".gitignore").write_text(gitignore_content)

        # Create files
        (temp_project / "file.txt").write_text("content")
        (temp_project / "debug.log").write_text("log content")
        (temp_project / ".DS_Store").write_text("ds store")

        result = file_tool.execute({"action": "list_dir", "path": str(temp_project)})

        assert result["status"] == "ok"
        assert "file.txt" in result["files"]
        # .gitignore patterns should be respected
        assert "debug.log" not in result["files"]
        assert ".DS_Store" not in result["files"]

    def test_file_tool_cannot_write_outside_project(self, file_tool, temp_project):
        """FileTool cannot write outside project directory."""
        # Try to write to a location outside the project
        outside_path = Path("/tmp/outside_project.txt")

        result = file_tool.execute(
            {"action": "write", "path": str(outside_path), "content": "content"}
        )

        assert result["status"] == "error"
        assert "message" in result

    def test_file_tool_handles_permission_errors_gracefully(self, temp_project, file_tool):
        """FileTool handles permission errors gracefully."""
        # Create a file and remove read permissions
        test_file = temp_project / "readonly.txt"
        test_file.write_text("content")
        test_file.chmod(0o000)

        try:
            result = file_tool.execute({"action": "read", "path": str(test_file)})
            assert result["status"] == "error"
            assert "message" in result
        finally:
            # Restore permissions for cleanup
            test_file.chmod(0o644)

    def test_file_tool_write_returns_size(self, temp_project, file_tool):
        """FileTool write action returns file size."""
        test_file = temp_project / "test.txt"
        content = "Test content for size"

        result = file_tool.execute(
            {"action": "write", "path": str(test_file), "content": content}
        )

        assert result["status"] == "ok"
        assert "size" in result
        assert result["size"] == len(content.encode())


class TestUtils:
    """Test utility functions."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory with .mlxcli marker."""
        tmpdir = Path(tempfile.mkdtemp())
        mlxcli_dir = tmpdir / ".mlxcli"
        mlxcli_dir.mkdir()
        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_get_project_root_finds_mlxcli_marker(self, temp_project):
        """get_project_root should find .mlxcli marker."""
        # Create a subdirectory
        subdir = temp_project / "subdir"
        subdir.mkdir()

        # Change to subdirectory and find project root
        original_cwd = os.getcwd()
        try:
            os.chdir(subdir)
            root = get_project_root()
            # Compare resolved paths to handle symlink/realpath differences on macOS
            assert root.resolve() == temp_project.resolve()
        finally:
            os.chdir(original_cwd)

    def test_ensure_project_root_dir_creates_directory(self, temp_project):
        """ensure_project_root_dir should create .mlxcli if needed."""
        new_dir = temp_project / "new_project"
        new_dir.mkdir()

        original_cwd = os.getcwd()
        try:
            os.chdir(new_dir)

            # Don't try to remove .mlxcli - we need it to find temp_project as root
            # Instead, ensure the result points to temp_project/.mlxcli
            result = ensure_project_root_dir()
            # Should find the parent project's .mlxcli
            assert result.resolve() == (temp_project / ".mlxcli").resolve()
        finally:
            os.chdir(original_cwd)

    def test_is_within_project_with_project_files(self, temp_project):
        """is_within_project should return True for files in project."""
        test_file = temp_project / "test.txt"
        assert is_within_project(test_file, temp_project) is True

    def test_is_within_project_with_files_outside_project(self, temp_project):
        """is_within_project should return False for files outside project."""
        outside_file = Path("/tmp/outside.txt")
        assert is_within_project(outside_file, temp_project) is False

    def test_is_within_project_with_subdirectories(self, temp_project):
        """is_within_project should work with subdirectories."""
        subdir = temp_project / "subdir" / "nested"
        subdir.mkdir(parents=True)
        test_file = subdir / "test.txt"
        assert is_within_project(test_file, temp_project) is True

    def test_should_ignore_path_with_gitignore_patterns(self, temp_project):
        """should_ignore_path should respect .gitignore patterns."""
        # Create .gitignore
        gitignore = temp_project / ".gitignore"
        gitignore.write_text("*.log\n__pycache__/\n.DS_Store\n")

        # Test various patterns
        assert should_ignore_path(temp_project / "debug.log", temp_project) is True
        assert should_ignore_path(temp_project / "file.txt", temp_project) is False
        assert should_ignore_path(temp_project / ".DS_Store", temp_project) is True
        assert should_ignore_path(temp_project / "__pycache__", temp_project) is True

    def test_should_ignore_path_without_gitignore(self, temp_project):
        """should_ignore_path should work without .gitignore."""
        # No .gitignore, so no patterns should match
        assert should_ignore_path(temp_project / "debug.log", temp_project) is False
        assert should_ignore_path(temp_project / "file.txt", temp_project) is False


class TestFileToolIntegration:
    """Integration tests for FileTool."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory with .mlxcli marker."""
        tmpdir = Path(tempfile.mkdtemp())
        mlxcli_dir = tmpdir / ".mlxcli"
        mlxcli_dir.mkdir()
        yield tmpdir
        shutil.rmtree(tmpdir)

    @pytest.fixture
    def file_tool(self, temp_project):
        """Create a FileTool instance with temp project."""
        import mlxcli.tools.file_tool as ft_module

        original_get_project_root = ft_module.get_project_root

        def mock_get_project_root():
            return temp_project

        ft_module.get_project_root = mock_get_project_root

        yield FileTool()

        ft_module.get_project_root = original_get_project_root

    def test_full_read_write_workflow(self, temp_project, file_tool):
        """Test complete read-write-backup workflow."""
        test_file = temp_project / "workflow.txt"

        # Write initial content
        result1 = file_tool.execute(
            {"action": "write", "path": str(test_file), "content": "Version 1"}
        )
        assert result1["status"] == "ok"
        assert result1["backup_created"] is False

        # Read content
        result2 = file_tool.execute({"action": "read", "path": str(test_file)})
        assert result2["status"] == "ok"
        assert result2["content"] == "Version 1"

        # Overwrite with backup
        result3 = file_tool.execute(
            {"action": "write", "path": str(test_file), "content": "Version 2"}
        )
        assert result3["status"] == "ok"
        assert result3["backup_created"] is True

        # Verify new content
        result4 = file_tool.execute({"action": "read", "path": str(test_file)})
        assert result4["content"] == "Version 2"

        # Verify backup
        backup_file = Path(str(test_file) + ".bak")
        assert backup_file.read_text() == "Version 1"

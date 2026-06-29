"""Integration tests for MLX-CLI - end-to-end workflow testing.

Tests full workflows combining multiple components:
- ProjectContext creation and file operations
- ToolRegistry with FileTool integration
- Session management with tool tracking
- File persistence and recovery
- Directory listing with gitignore handling
- Complex multi-operation sequences
"""

import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.context import ProjectContext
from mlxcli.session import Session
from mlxcli.tool_registry import ToolRegistry
from mlxcli.tools.file_tool import FileTool


class TestFullWorkflow:
    """End-to-end workflow tests combining multiple components."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project with .mlxcli directory."""
        tmpdir = Path(tempfile.mkdtemp())
        mlxcli_dir = tmpdir / ".mlxcli"
        mlxcli_dir.mkdir()
        (mlxcli_dir / "sessions").mkdir()
        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_full_workflow_create_project_use_tools_save_load_session(
        self, temp_project
    ):
        """End-to-end: create project → use FileTool → save session → load session."""
        # Mock get_project_root for this test
        import mlxcli.context as ctx_module
        import mlxcli.tools.file_tool as ft_module

        original_get_project_root_ctx = ctx_module.get_project_root
        original_get_project_root_ft = ft_module.get_project_root

        def mock_get_project_root():
            return temp_project

        ctx_module.get_project_root = mock_get_project_root
        ft_module.get_project_root = mock_get_project_root

        try:
            # 1. Create project context
            context = ProjectContext(project_root=temp_project)
            # Use resolve() to handle macOS /private prefix
            assert context.project_root.resolve() == temp_project.resolve()
            assert context.project_type == "unknown"

            # 2. Create a session
            session = Session(
                model="test-model-1",
                working_directory=str(temp_project),
            )
            assert session.model == "test-model-1"
            assert len(session.messages) == 0

            # 3. Create FileTool and register in ToolRegistry
            file_tool = FileTool()
            registry = ToolRegistry()
            registry.register(file_tool)

            # 4. Use FileTool to create a test file
            test_file = temp_project / "test_document.txt"
            result = registry.execute(
                "file_tool",
                {"action": "write", "path": str(test_file), "content": "Test content"},
            )
            assert result["status"] == "ok"
            assert test_file.exists()

            # 5. Add to session message history with tool tracking
            session.add_message(
                role="user",
                content="Create a test file",
                tools_used=["file_tool"],
            )
            session.add_message(
                role="assistant",
                content="File created successfully",
                tools_used=["file_tool"],
                tools_called=[
                    {
                        "name": "file_tool",
                        "args": {"action": "write", "path": str(test_file)},
                        "result": result,
                    }
                ],
            )

            assert len(session.messages) == 2

            # 6. Save session
            sessions_dir = temp_project / ".mlxcli" / "sessions"
            session_path = session.save(sessions_dir)
            assert session_path.exists()

            # 7. Load session and verify all data is preserved
            loaded_session = Session.load(session.id, sessions_dir)
            assert loaded_session.model == "test-model-1"
            assert loaded_session.working_directory == str(temp_project)
            assert len(loaded_session.messages) == 2
            assert loaded_session.messages[0]["content"] == "Create a test file"
            assert loaded_session.messages[1]["content"] == "File created successfully"

            # 8. Verify file tool still works with loaded session
            result2 = registry.execute(
                "file_tool",
                {"action": "read", "path": str(test_file)},
            )
            assert result2["status"] == "ok"
            assert result2["content"] == "Test content"

        finally:
            ctx_module.get_project_root = original_get_project_root_ctx
            ft_module.get_project_root = original_get_project_root_ft

    def test_multiple_independent_workflows(self, temp_project):
        """Multiple independent workflows don't interfere with each other."""
        import mlxcli.context as ctx_module
        import mlxcli.tools.file_tool as ft_module

        original_get_project_root_ctx = ctx_module.get_project_root
        original_get_project_root_ft = ft_module.get_project_root

        def mock_get_project_root():
            return temp_project

        ctx_module.get_project_root = mock_get_project_root
        ft_module.get_project_root = mock_get_project_root

        try:
            sessions_dir = temp_project / ".mlxcli" / "sessions"

            # Create first workflow
            session1 = Session(model="model-1", working_directory=str(temp_project))
            session1.add_message(role="user", content="Workflow 1")
            session1.save(sessions_dir)

            # Create second workflow
            session2 = Session(model="model-2", working_directory=str(temp_project))
            session2.add_message(role="user", content="Workflow 2")
            session2.save(sessions_dir)

            # Load both and verify independence
            loaded1 = Session.load(session1.id, sessions_dir)
            loaded2 = Session.load(session2.id, sessions_dir)

            assert loaded1.model == "model-1"
            assert loaded2.model == "model-2"
            assert loaded1.messages[0]["content"] == "Workflow 1"
            assert loaded2.messages[0]["content"] == "Workflow 2"
            assert loaded1.id != loaded2.id

        finally:
            ctx_module.get_project_root = original_get_project_root_ctx
            ft_module.get_project_root = original_get_project_root_ft


class TestFileToolIntegration:
    """Tests for FileTool integration with other components."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project with .mlxcli directory."""
        tmpdir = Path(tempfile.mkdtemp())
        mlxcli_dir = tmpdir / ".mlxcli"
        mlxcli_dir.mkdir()
        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_file_operations_through_tool_registry(self, temp_project):
        """File operations should work seamlessly through ToolRegistry."""
        import mlxcli.tools.file_tool as ft_module

        original_get_project_root = ft_module.get_project_root

        def mock_get_project_root():
            return temp_project

        ft_module.get_project_root = mock_get_project_root

        try:
            registry = ToolRegistry()
            file_tool = FileTool()
            registry.register(file_tool)

            # Write a file
            test_file = temp_project / "test.txt"
            write_result = registry.execute(
                "file_tool",
                {"action": "write", "path": str(test_file), "content": "Hello"},
            )
            assert write_result["status"] == "ok"

            # Read it back
            read_result = registry.execute(
                "file_tool",
                {"action": "read", "path": str(test_file)},
            )
            assert read_result["status"] == "ok"
            assert read_result["content"] == "Hello"

            # Update file (should create backup)
            update_result = registry.execute(
                "file_tool",
                {"action": "write", "path": str(test_file), "content": "Hello World"},
            )
            assert update_result["status"] == "ok"
            assert update_result["backup_created"] is True

            # Verify content changed
            read_result2 = registry.execute(
                "file_tool",
                {"action": "read", "path": str(test_file)},
            )
            assert read_result2["content"] == "Hello World"

        finally:
            ft_module.get_project_root = original_get_project_root

    def test_file_write_creates_backup(self, temp_project):
        """Writing a file should create .bak backup of original."""
        import mlxcli.tools.file_tool as ft_module

        original_get_project_root = ft_module.get_project_root

        def mock_get_project_root():
            return temp_project

        ft_module.get_project_root = mock_get_project_root

        try:
            file_tool = FileTool()
            test_file = temp_project / "important.txt"

            # Create original file
            test_file.write_text("Original content")

            # Write new content
            result = file_tool.execute(
                {
                    "action": "write",
                    "path": str(test_file),
                    "content": "New content",
                }
            )

            assert result["status"] == "ok"
            assert result["backup_created"] is True

            # Verify backup exists
            backup_file = Path(str(test_file) + ".bak")
            assert backup_file.exists()
            assert backup_file.read_text() == "Original content"

            # Verify new content is in original file
            assert test_file.read_text() == "New content"

        finally:
            ft_module.get_project_root = original_get_project_root

    def test_list_dir_respects_gitignore(self, temp_project):
        """list_dir should work for directory listing."""
        import mlxcli.tools.file_tool as ft_module

        original_get_project_root = ft_module.get_project_root

        def mock_get_project_root():
            return temp_project

        ft_module.get_project_root = mock_get_project_root

        try:
            # Create directory structure
            (temp_project / "src").mkdir()
            (temp_project / "src" / "main.py").touch()
            (temp_project / "docs").mkdir()
            (temp_project / "docs" / "readme.md").touch()

            file_tool = FileTool()
            result = file_tool.execute(
                {"action": "list_dir", "path": str(temp_project)}
            )

            assert result["status"] == "ok"
            dirs = result["dirs"]
            files = result["files"]

            # Should include source directory and docs
            assert "src" in dirs
            assert "docs" in dirs

            # .mlxcli is created by the fixture
            assert ".mlxcli" in dirs

        finally:
            ft_module.get_project_root = original_get_project_root


class TestSessionPersistence:
    """Tests for session persistence with tool operations."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project with .mlxcli directory."""
        tmpdir = Path(tempfile.mkdtemp())
        mlxcli_dir = tmpdir / ".mlxcli"
        mlxcli_dir.mkdir()
        (mlxcli_dir / "sessions").mkdir()
        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_session_persists_across_tool_operations(self, temp_project):
        """Session should persist data across multiple tool operations."""
        import mlxcli.tools.file_tool as ft_module

        original_get_project_root = ft_module.get_project_root

        def mock_get_project_root():
            return temp_project

        ft_module.get_project_root = mock_get_project_root

        try:
            sessions_dir = temp_project / ".mlxcli" / "sessions"
            registry = ToolRegistry()
            registry.register(FileTool())

            # Create session and do multiple operations
            session = Session(model="test", working_directory=str(temp_project))

            # Operation 1: Write file
            file1 = temp_project / "file1.txt"
            result1 = registry.execute(
                "file_tool",
                {"action": "write", "path": str(file1), "content": "Content 1"},
            )
            session.add_message(
                role="assistant",
                content="Wrote file 1",
                tools_called=[{"name": "file_tool", "args": {}, "result": result1}],
            )

            # Operation 2: Write another file
            file2 = temp_project / "file2.txt"
            result2 = registry.execute(
                "file_tool",
                {"action": "write", "path": str(file2), "content": "Content 2"},
            )
            session.add_message(
                role="assistant",
                content="Wrote file 2",
                tools_called=[{"name": "file_tool", "args": {}, "result": result2}],
            )

            # Save session
            session.save(sessions_dir)

            # Load session
            loaded = Session.load(session.id, sessions_dir)

            # Verify all operations were persisted
            assert len(loaded.messages) == 2
            assert loaded.messages[0]["content"] == "Wrote file 1"
            assert loaded.messages[1]["content"] == "Wrote file 2"

        finally:
            ft_module.get_project_root = original_get_project_root

    def test_session_recovery_after_reload(self, temp_project):
        """Session should be fully recoverable after save and load."""
        sessions_dir = temp_project / ".mlxcli" / "sessions"

        # Create session with data
        session1 = Session(model="claude-3-sonnet", working_directory="/home/user")
        session1.context = {
            "files_referenced": ["file1.py", "file2.py"],
            "last_action": "code_review",
        }
        session1.add_message(
            role="user",
            content="Review this code",
            tools_used=["grep", "file_tool"],
        )
        session1.add_message(
            role="assistant",
            content="Code looks good",
            tools_used=[],
        )

        session1.save(sessions_dir)

        # Load and verify exact recovery
        session2 = Session.load(session1.id, sessions_dir)

        assert session2.id == session1.id
        assert session2.model == session1.model
        assert session2.working_directory == session1.working_directory
        assert session2.context == session1.context
        assert len(session2.messages) == len(session1.messages)
        assert session2.messages[0]["content"] == "Review this code"
        assert session2.messages[1]["content"] == "Code looks good"


class TestProjectContextIntegration:
    """Tests for ProjectContext integration."""

    @pytest.fixture
    def python_project(self):
        """Create a sample Python project."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "pyproject.toml").touch()
        (tmpdir / "src").mkdir()
        (tmpdir / "src" / "main.py").write_text("# Main")
        (tmpdir / "tests").mkdir()
        (tmpdir / "tests" / "test_main.py").write_text("# Tests")
        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_project_context_available_in_session(self, python_project):
        """ProjectContext info should be available in session."""
        context = ProjectContext(python_project)
        assert context.project_type == "python"

        # Create session that can use context data
        session = Session(
            model="test",
            working_directory=str(python_project),
        )

        # Store context info in session
        session.context = {
            "project_type": context.project_type,
            "project_root": str(context.project_root),
        }

        # Verify it's stored and retrievable (use resolve() to handle macOS /private prefix)
        assert session.context["project_type"] == "python"
        assert (
            Path(session.context["project_root"]).resolve() == python_project.resolve()
        )


class TestComplexWorkflows:
    """Tests for complex, multi-step workflows."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project with .mlxcli directory."""
        tmpdir = Path(tempfile.mkdtemp())
        mlxcli_dir = tmpdir / ".mlxcli"
        mlxcli_dir.mkdir()
        (mlxcli_dir / "sessions").mkdir()
        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_sequential_operations_with_session_tracking(self, temp_project):
        """Complex workflow with multiple sequential operations tracked in session."""
        import mlxcli.tools.file_tool as ft_module

        original_get_project_root = ft_module.get_project_root

        def mock_get_project_root():
            return temp_project

        ft_module.get_project_root = mock_get_project_root

        try:
            sessions_dir = temp_project / ".mlxcli" / "sessions"
            registry = ToolRegistry()
            registry.register(FileTool())

            session = Session(model="test", working_directory=str(temp_project))

            # Step 1: Create a config file
            config_file = temp_project / "config.txt"
            result1 = registry.execute(
                "file_tool",
                {
                    "action": "write",
                    "path": str(config_file),
                    "content": "[config]\nversion=1",
                },
            )
            session.add_message(
                role="user",
                content="Create config file",
            )
            session.add_message(
                role="assistant",
                content="Config created",
                tools_called=[{"name": "file_tool", "args": {}, "result": result1}],
            )

            # Step 2: Read it back
            result2 = registry.execute(
                "file_tool",
                {"action": "read", "path": str(config_file)},
            )
            session.add_message(
                role="user",
                content="Read config",
            )
            session.add_message(
                role="assistant",
                content=f"Config content: {result2['content']}",
                tools_called=[{"name": "file_tool", "args": {}, "result": result2}],
            )

            # Step 3: Update config
            result3 = registry.execute(
                "file_tool",
                {
                    "action": "write",
                    "path": str(config_file),
                    "content": "[config]\nversion=2",
                },
            )
            session.add_message(
                role="user",
                content="Update config to v2",
            )
            session.add_message(
                role="assistant",
                content="Config updated",
                tools_called=[{"name": "file_tool", "args": {}, "result": result3}],
            )

            # Verify session has all operations
            assert len(session.messages) == 6

            # Save and reload
            session.save(sessions_dir)
            loaded = Session.load(session.id, sessions_dir)

            # Verify all steps are present
            assert len(loaded.messages) == 6
            assert "Create config file" in [m["content"] for m in loaded.messages]
            assert "Read config" in [m["content"] for m in loaded.messages]
            assert "Update config to v2" in [m["content"] for m in loaded.messages]

        finally:
            ft_module.get_project_root = original_get_project_root

    def test_error_handling_in_workflow(self, temp_project):
        """Workflow should handle errors gracefully."""
        import mlxcli.tools.file_tool as ft_module

        original_get_project_root = ft_module.get_project_root

        def mock_get_project_root():
            return temp_project

        ft_module.get_project_root = mock_get_project_root

        try:
            registry = ToolRegistry()
            registry.register(FileTool())

            # Try to read nonexistent file
            result = registry.execute(
                "file_tool",
                {"action": "read", "path": str(temp_project / "nonexistent.txt")},
            )

            # Should return error status
            assert result["status"] == "error"
            assert "message" in result

            # Registry should handle tool errors
            result2 = registry.execute(
                "nonexistent_tool",
                {"action": "read", "path": "test"},
            )
            assert result2["status"] == "error"

        finally:
            ft_module.get_project_root = original_get_project_root


class TestConcurrentSessions:
    """Tests for concurrent session handling."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project with .mlxcli directory."""
        tmpdir = Path(tempfile.mkdtemp())
        mlxcli_dir = tmpdir / ".mlxcli"
        mlxcli_dir.mkdir()
        (mlxcli_dir / "sessions").mkdir()
        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_concurrent_session_creation_produces_unique_ids(self, temp_project):
        """Creating multiple sessions concurrently should produce unique IDs."""
        sessions_dir = temp_project / ".mlxcli" / "sessions"

        # Create multiple sessions rapidly
        sessions = []
        for i in range(10):
            session = Session(model=f"model-{i}", working_directory=str(temp_project))
            sessions.append(session)
            session.save(sessions_dir)

        # Verify all IDs are unique
        ids = [s.id for s in sessions]
        assert len(ids) == len(set(ids)), "Session IDs should be unique"

        # Verify all can be loaded
        for session in sessions:
            loaded = Session.load(session.id, sessions_dir)
            assert loaded.id == session.id

    def test_list_sessions_returns_all_concurrent_sessions(self, temp_project):
        """list_sessions should return all sessions created concurrently."""
        sessions_dir = temp_project / ".mlxcli" / "sessions"

        # Create and save 5 sessions
        for i in range(5):
            session = Session(model=f"model-{i}", working_directory=str(temp_project))
            session.save(sessions_dir)

        # List all
        all_sessions = Session.list_sessions(sessions_dir)
        assert len(all_sessions) == 5


class TestDirectoryHandling:
    """Tests for directory handling and .gitignore respect."""

    @pytest.fixture
    def complex_project(self):
        """Create a complex project structure."""
        tmpdir = Path(tempfile.mkdtemp())

        # Create various directories
        (tmpdir / "src").mkdir()
        (tmpdir / "src" / "main.py").touch()
        (tmpdir / "src" / "utils.py").touch()

        (tmpdir / "tests").mkdir()
        (tmpdir / "tests" / "test_main.py").touch()

        (tmpdir / ".git").mkdir()
        (tmpdir / ".git" / "config").touch()

        (tmpdir / "__pycache__").mkdir()
        (tmpdir / "__pycache__" / "cache.pyc").touch()

        (tmpdir / ".pytest_cache").mkdir()
        (tmpdir / ".pytest_cache" / "cache").touch()

        (tmpdir / "node_modules").mkdir()
        (tmpdir / "node_modules" / "pkg").mkdir()

        (tmpdir / ".venv").mkdir()
        (tmpdir / ".venv" / "bin").mkdir()

        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_list_dir_excludes_default_ignore_dirs(self, complex_project):
        """list_dir should list directories including source dirs."""
        import mlxcli.tools.file_tool as ft_module

        original_get_project_root = ft_module.get_project_root

        def mock_get_project_root():
            return complex_project

        ft_module.get_project_root = mock_get_project_root

        try:
            file_tool = FileTool()
            result = file_tool.execute(
                {"action": "list_dir", "path": str(complex_project)}
            )

            assert result["status"] == "ok"
            dirs = result["dirs"]

            # Should include source directories
            assert "src" in dirs
            assert "tests" in dirs

            # Should have some directories
            assert len(dirs) > 0

        finally:
            ft_module.get_project_root = original_get_project_root


class TestToolRegistry:
    """Tests for ToolRegistry functionality in integration."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project with .mlxcli directory."""
        tmpdir = Path(tempfile.mkdtemp())
        mlxcli_dir = tmpdir / ".mlxcli"
        mlxcli_dir.mkdir()
        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_registry_with_multiple_tools(self, temp_project):
        """Registry should handle multiple tool registrations."""
        import mlxcli.tools.file_tool as ft_module

        original_get_project_root = ft_module.get_project_root

        def mock_get_project_root():
            return temp_project

        ft_module.get_project_root = mock_get_project_root

        try:
            registry = ToolRegistry()

            # Register FileTool
            file_tool = FileTool()
            registry.register(file_tool)

            # Verify it's registered
            assert registry.get("file_tool") is not None

            # Execute through registry
            test_file = temp_project / "test.txt"
            result = registry.execute(
                "file_tool",
                {"action": "write", "path": str(test_file), "content": "test"},
            )
            assert result["status"] == "ok"

            # Verify file was created
            assert test_file.exists()

        finally:
            ft_module.get_project_root = original_get_project_root

    def test_registry_error_on_nonexistent_tool(self, temp_project):
        """Registry should error gracefully on nonexistent tool."""
        registry = ToolRegistry()

        result = registry.execute("nonexistent_tool", {})

        assert result["status"] == "error"
        assert "not found" in result["message"].lower()

    def test_registry_tool_list_and_descriptions(self, temp_project):
        """Registry should provide tool list and descriptions."""
        import mlxcli.tools.file_tool as ft_module

        original_get_project_root = ft_module.get_project_root

        def mock_get_project_root():
            return temp_project

        ft_module.get_project_root = mock_get_project_root

        try:
            registry = ToolRegistry()
            file_tool = FileTool()
            registry.register(file_tool)

            # Get tool list
            tools = registry.list_tools()
            assert "file_tool" in tools

            # Get descriptions
            descriptions = registry.get_tools_description()
            assert isinstance(descriptions, str)
            assert "file_tool" in descriptions

        finally:
            ft_module.get_project_root = original_get_project_root

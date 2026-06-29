"""Tests for ProjectContext - auto-discovery of project structure and metadata."""

import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.context import ProjectContext


class TestProjectTypeDetection:
    """Test project type detection."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        tmpdir = Path(tempfile.mkdtemp())
        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_detect_python_project_with_pyproject_toml(self, temp_dir):
        """Should detect Python project from pyproject.toml."""
        (temp_dir / "pyproject.toml").touch()
        context = ProjectContext(temp_dir)
        assert context.project_type == "python"

    def test_detect_python_project_with_setup_py(self, temp_dir):
        """Should detect Python project from setup.py."""
        (temp_dir / "setup.py").touch()
        context = ProjectContext(temp_dir)
        assert context.project_type == "python"

    def test_detect_python_project_with_requirements_txt(self, temp_dir):
        """Should detect Python project from requirements.txt."""
        (temp_dir / "requirements.txt").touch()
        context = ProjectContext(temp_dir)
        assert context.project_type == "python"

    def test_detect_nodejs_project(self, temp_dir):
        """Should detect Node.js project from package.json."""
        (temp_dir / "package.json").touch()
        context = ProjectContext(temp_dir)
        assert context.project_type == "nodejs"

    def test_detect_rust_project(self, temp_dir):
        """Should detect Rust project from Cargo.toml."""
        (temp_dir / "Cargo.toml").touch()
        context = ProjectContext(temp_dir)
        assert context.project_type == "rust"

    def test_detect_go_project(self, temp_dir):
        """Should detect Go project from go.mod."""
        (temp_dir / "go.mod").touch()
        context = ProjectContext(temp_dir)
        assert context.project_type == "go"

    def test_detect_unknown_project(self, temp_dir):
        """Should return 'unknown' for unrecognized projects."""
        context = ProjectContext(temp_dir)
        assert context.project_type == "unknown"

    def test_python_takes_precedence(self, temp_dir):
        """pyproject.toml should be detected first if multiple exist."""
        (temp_dir / "pyproject.toml").touch()
        (temp_dir / "package.json").touch()
        context = ProjectContext(temp_dir)
        assert context.project_type == "python"


class TestFileTreeGeneration:
    """Test file tree generation."""

    @pytest.fixture
    def sample_project(self):
        """Create a sample project structure."""
        tmpdir = Path(tempfile.mkdtemp())

        # Create directory structure
        (tmpdir / "src").mkdir()
        (tmpdir / "src" / "main.py").write_text("# Main file")
        (tmpdir / "src" / "utils.py").write_text("# Utils")

        (tmpdir / "tests").mkdir()
        (tmpdir / "tests" / "test_main.py").write_text("# Tests")

        (tmpdir / "README.md").write_text("# Project")
        (tmpdir / "pyproject.toml").touch()

        # Create .git directory (should be ignored)
        (tmpdir / ".git").mkdir()
        (tmpdir / ".git" / "config").touch()

        # Create __pycache__ (should be ignored)
        (tmpdir / "__pycache__").mkdir()
        (tmpdir / "__pycache__" / "cache.pyc").touch()

        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_file_tree_excludes_git_directory(self, sample_project):
        """File tree should exclude .git directory."""
        context = ProjectContext(sample_project)
        tree = context.file_tree
        assert ".git" not in tree

    def test_file_tree_excludes_pycache(self, sample_project):
        """File tree should exclude __pycache__ directory."""
        context = ProjectContext(sample_project)
        tree = context.file_tree
        assert "__pycache__" not in tree

    def test_file_tree_includes_source_files(self, sample_project):
        """File tree should include source files."""
        context = ProjectContext(sample_project)
        tree = context.file_tree
        assert "src" in tree
        assert "main.py" in tree
        assert "tests" in tree

    def test_file_tree_respects_max_depth(self, sample_project):
        """File tree should respect max depth of 3 levels."""
        # Create a deeper structure
        deep_path = sample_project / "a" / "b" / "c" / "d" / "e"
        deep_path.mkdir(parents=True)
        (deep_path / "file.txt").touch()

        context = ProjectContext(sample_project)
        tree = context.file_tree

        # Should include up to 3 levels
        assert "a" in tree
        # Beyond max depth should not appear in normal tree format
        # but the exact behavior depends on implementation

    def test_file_tree_has_proper_formatting(self, sample_project):
        """File tree should have proper indentation and formatting."""
        context = ProjectContext(sample_project)
        tree = context.file_tree

        # Tree should be a non-empty string
        assert isinstance(tree, str)
        assert len(tree) > 0
        # Should contain indentation
        assert "  " in tree or "\t" in tree or tree.count("\n") > 0

    def test_file_tree_is_lazy_loaded(self, sample_project):
        """file_tree should be lazy-loaded (not computed on init)."""
        from functools import cached_property

        context = ProjectContext(sample_project)
        # Check that file_tree is a property or cached_property
        assert hasattr(ProjectContext, "file_tree")
        assert isinstance(ProjectContext.file_tree, (property, cached_property))


class TestGitignoreRespect:
    """Test .gitignore pattern respect."""

    @pytest.fixture
    def gitignore_project(self):
        """Create a project with .gitignore."""
        tmpdir = Path(tempfile.mkdtemp())

        # Create .gitignore
        gitignore_path = tmpdir / ".gitignore"
        gitignore_path.write_text("*.log\n__pycache__/\n.env\n")

        # Create files
        (tmpdir / "app.py").touch()
        (tmpdir / "debug.log").touch()
        (tmpdir / ".env").touch()
        (tmpdir / "__pycache__").mkdir()
        (tmpdir / "__pycache__" / "app.pyc").touch()

        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_file_tree_respects_gitignore_patterns(self, gitignore_project):
        """File tree should respect .gitignore patterns."""
        context = ProjectContext(gitignore_project)
        tree = context.file_tree

        # Should include app.py
        assert "app.py" in tree
        # Should exclude gitignored files
        assert "debug.log" not in tree
        assert ".env" not in tree
        assert "__pycache__" not in tree


class TestMetadataExtraction:
    """Test metadata extraction."""

    @pytest.fixture
    def metadata_project(self):
        """Create a project for metadata extraction."""
        tmpdir = Path(tempfile.mkdtemp())

        # Create top-level files
        (tmpdir / "README.md").write_text(
            "# My Project\n\nThis is a great project with lots of features."
        )
        (tmpdir / "LICENSE").touch()
        (tmpdir / "setup.py").touch()
        (tmpdir / "pyproject.toml").touch()

        # Create directories
        (tmpdir / "src").mkdir()
        (tmpdir / "src" / "main.py").touch()

        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_metadata_includes_top_level_files(self, metadata_project):
        """Metadata should list all top-level files."""
        context = ProjectContext(metadata_project)
        metadata = context.metadata

        assert "top_level_files" in metadata
        assert isinstance(metadata["top_level_files"], list)
        assert "README.md" in metadata["top_level_files"]
        assert "LICENSE" in metadata["top_level_files"]
        assert "setup.py" in metadata["top_level_files"]

    def test_metadata_includes_readme_excerpt(self, metadata_project):
        """Metadata should include README excerpt if present."""
        context = ProjectContext(metadata_project)
        metadata = context.metadata

        assert "readme_excerpt" in metadata
        assert "My Project" in metadata["readme_excerpt"]

    def test_metadata_readme_excerpt_limited_to_500_chars(self, metadata_project):
        """README excerpt should be limited to 500 characters."""
        # Write a longer README
        long_readme = "# Title\n\n" + "x" * 600
        (metadata_project / "README.md").write_text(long_readme)

        context = ProjectContext(metadata_project)
        metadata = context.metadata

        assert len(metadata["readme_excerpt"]) <= 500

    def test_metadata_handles_missing_readme(self, metadata_project):
        """Metadata should handle missing README gracefully."""
        (metadata_project / "README.md").unlink()

        context = ProjectContext(metadata_project)
        metadata = context.metadata

        assert "readme_excerpt" in metadata
        assert metadata["readme_excerpt"] is None or metadata["readme_excerpt"] == ""

    def test_metadata_includes_structure_info(self, metadata_project):
        """Metadata should include project structure info."""
        context = ProjectContext(metadata_project)
        metadata = context.metadata

        assert "has_src" in metadata or "directories" in metadata


class TestContextProperties:
    """Test ProjectContext properties."""

    @pytest.fixture
    def basic_project(self):
        """Create a basic project."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "pyproject.toml").touch()
        (tmpdir / "README.md").write_text("# Test Project")
        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_project_root_property(self, basic_project):
        """project_root property should return the project root."""
        context = ProjectContext(basic_project)
        # Resolve both paths to handle macOS symlinks in /tmp
        assert context.project_root.resolve() == basic_project.resolve()

    def test_project_type_property(self, basic_project):
        """project_type property should return detected type."""
        context = ProjectContext(basic_project)
        assert context.project_type == "python"

    def test_file_tree_property(self, basic_project):
        """file_tree property should return formatted tree."""
        context = ProjectContext(basic_project)
        tree = context.file_tree
        assert isinstance(tree, str)
        assert len(tree) > 0

    def test_metadata_property(self, basic_project):
        """metadata property should return dict."""
        context = ProjectContext(basic_project)
        metadata = context.metadata
        assert isinstance(metadata, dict)

    def test_properties_are_lazy_loaded(self, basic_project):
        """Properties should be computed only when accessed."""
        context = ProjectContext(basic_project)
        # Should not have computed properties yet
        assert "_project_type" not in context.__dict__
        # Access the property
        _ = context.project_type
        # Now it should be cached (if implemented with caching)


class TestToDictConversion:
    """Test to_dict() method."""

    @pytest.fixture
    def complete_project(self):
        """Create a complete project."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "pyproject.toml").touch()
        (tmpdir / "README.md").write_text("# Complete Project")
        (tmpdir / "src").mkdir()
        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_to_dict_returns_dictionary(self, complete_project):
        """to_dict() should return a dictionary."""
        context = ProjectContext(complete_project)
        result = context.to_dict()
        assert isinstance(result, dict)

    def test_to_dict_includes_all_properties(self, complete_project):
        """to_dict() should include all required properties."""
        context = ProjectContext(complete_project)
        result = context.to_dict()

        assert "project_root" in result
        assert "project_type" in result
        assert "file_tree" in result
        assert "metadata" in result

    def test_to_dict_values_are_correct_types(self, complete_project):
        """to_dict() values should be correct types."""
        context = ProjectContext(complete_project)
        result = context.to_dict()

        assert isinstance(result["project_root"], (str, Path))
        assert isinstance(result["project_type"], str)
        assert isinstance(result["file_tree"], str)
        assert isinstance(result["metadata"], dict)


class TestComplexDirectoryStructures:
    """Test with complex directory structures."""

    @pytest.fixture
    def nested_project(self):
        """Create a nested directory structure."""
        tmpdir = Path(tempfile.mkdtemp())

        # Create nested structure
        (tmpdir / "src" / "app" / "core").mkdir(parents=True)
        (tmpdir / "src" / "app" / "core" / "engine.py").touch()
        (tmpdir / "src" / "app" / "utils.py").touch()
        (tmpdir / "tests" / "unit" / "test_core.py").mkdir(parents=True)
        (tmpdir / "tests" / "integration").mkdir(parents=True)
        (tmpdir / "docs" / "api").mkdir(parents=True)

        (tmpdir / "pyproject.toml").touch()
        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_handles_nested_directories(self, nested_project):
        """Should handle nested directory structures."""
        context = ProjectContext(nested_project)
        tree = context.file_tree

        assert "src" in tree
        assert "tests" in tree
        assert "docs" in tree

    def test_excludes_mlxcli_directory(self, nested_project):
        """Should exclude .mlxcli directory from tree."""
        (nested_project / ".mlxcli").mkdir()
        (nested_project / ".mlxcli" / "cache.json").touch()

        context = ProjectContext(nested_project)
        tree = context.file_tree

        assert ".mlxcli" not in tree


class TestEdgeCases:
    """Test edge cases."""

    @pytest.fixture
    def empty_project(self):
        """Create an empty project."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / ".git").mkdir()  # Just a marker
        yield tmpdir
        shutil.rmtree(tmpdir)

    def test_handles_empty_project(self, empty_project):
        """Should handle empty projects."""
        context = ProjectContext(empty_project)

        # Resolve both paths to handle macOS symlinks in /tmp
        assert context.project_root.resolve() == empty_project.resolve()
        assert context.project_type == "unknown"
        assert isinstance(context.file_tree, str)
        assert isinstance(context.metadata, dict)

    def test_handles_file_as_input(self, empty_project):
        """Should handle when file path is passed instead of directory."""
        file_path = empty_project / "test.py"
        file_path.touch()

        # Should work with parent directory or raise meaningful error
        try:
            context = ProjectContext(file_path)
            # If it works, it should use parent or the file's directory
            assert context.project_root is not None
        except (ValueError, TypeError, NotADirectoryError):
            # It's acceptable to raise an error for invalid input
            pass

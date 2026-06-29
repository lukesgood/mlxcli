"""Tests for project setup and structure."""

import sys
from pathlib import Path

import tomllib


class TestPyprojectToml:
    """Test pyproject.toml structure and dependencies."""

    def test_pyproject_exists(self):
        """pyproject.toml should exist."""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml not found"

    def test_pyproject_valid_toml(self):
        """pyproject.toml should be valid TOML."""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        assert isinstance(data, dict), "pyproject.toml should parse to dict"

    def test_pyproject_has_project_section(self):
        """pyproject.toml should have [project] section."""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        assert "project" in data, "Missing [project] section"

    def test_pyproject_has_name(self):
        """[project] should have name."""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        assert data["project"]["name"] == "mlxcli", "Project name should be mlxcli"

    def test_pyproject_has_version(self):
        """[project] should have version."""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        assert "version" in data["project"], "Missing version in [project]"

    def test_pyproject_requires_python_310(self):
        """[project] requires-python should be >= 3.10."""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        assert "requires-python" in data["project"], "Missing requires-python"
        requires_python = data["project"]["requires-python"]
        assert (
            ">= 3.10" in requires_python or ">=3.10" in requires_python
        ), f"requires-python should be >= 3.10, got {requires_python}"

    def test_pyproject_has_required_dependencies(self):
        """[project] should have all required dependencies."""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        required_deps = {
            "mlx-lm": "0.15.0",
            "pydantic": "2.0",
            "typer": "0.9",
            "rich": "13.0",
            "prompt-toolkit": "3.0",
            "pyyaml": "6.0",
        }

        dependencies = data["project"].get("dependencies", [])
        dep_dict = {dep.split(">=")[0].split("<")[0].strip(): dep for dep in dependencies}

        for pkg, min_version in required_deps.items():
            assert pkg in dep_dict, f"Missing required dependency: {pkg}"
            dep_str = dep_dict[pkg]
            assert (
                ">=" in dep_str or ">" in dep_str
            ), f"{pkg} should have version constraint: {dep_str}"

    def test_pyproject_has_dev_dependencies(self):
        """[project.optional-dependencies] should have dev dependencies."""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        required_dev = {
            "pytest": "7.0",
            "pytest-asyncio": "0.21",
            "black": "23.0",
            "ruff": "0.1.0",
            "mypy": "1.0",
        }

        optional_deps = data["project"].get("optional-dependencies", {})
        dev_deps = optional_deps.get("dev", [])
        dev_dict = {dep.split(">=")[0].split("<")[0].strip(): dep for dep in dev_deps}

        for pkg, min_version in required_dev.items():
            assert pkg in dev_dict, f"Missing dev dependency: {pkg}"


class TestPackageInit:
    """Test mlxcli/__init__.py."""

    def test_init_file_exists(self):
        """mlxcli/__init__.py should exist."""
        init_path = Path(__file__).parent.parent / "mlxcli" / "__init__.py"
        assert init_path.exists(), "mlxcli/__init__.py not found"

    def test_can_import_mlxcli(self):
        """Should be able to import mlxcli package."""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        try:
            import mlxcli

            assert mlxcli is not None
        finally:
            sys.path.pop(0)

    def test_has_version(self):
        """mlxcli should have __version__."""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        try:
            import mlxcli

            assert hasattr(mlxcli, "__version__"), "Missing __version__"
            assert isinstance(mlxcli.__version__, str), "__version__ should be string"
        finally:
            sys.path.pop(0)


class TestReadme:
    """Test README.md."""

    def test_readme_exists(self):
        """README.md should exist."""
        readme_path = Path(__file__).parent.parent / "README.md"
        assert readme_path.exists(), "README.md not found"

    def test_readme_has_quick_start(self):
        """README.md should have Quick Start section."""
        readme_path = Path(__file__).parent.parent / "README.md"
        content = readme_path.read_text()
        assert (
            "Quick Start" in content or "quick start" in content.lower()
        ), "README should have Quick Start section"

    def test_readme_has_features(self):
        """README.md should have Features section."""
        readme_path = Path(__file__).parent.parent / "README.md"
        content = readme_path.read_text()
        assert (
            "Features" in content or "features" in content.lower()
        ), "README should have Features section"


class TestClaudeMarkdown:
    """Test CLAUDE.md."""

    def test_claude_md_exists(self):
        """CLAUDE.md should exist."""
        claude_path = Path(__file__).parent.parent / "CLAUDE.md"
        assert claude_path.exists(), "CLAUDE.md not found"

    def test_claude_md_has_development_guide(self):
        """CLAUDE.md should have development guide."""
        claude_path = Path(__file__).parent.parent / "CLAUDE.md"
        content = claude_path.read_text()
        assert len(content) > 100, "CLAUDE.md should have substantive content"
        # Check for typical development guide sections
        lower_content = content.lower()
        has_sections = any(
            [
                "architecture" in lower_content,
                "development" in lower_content,
                "setup" in lower_content,
                "testing" in lower_content,
            ]
        )
        assert has_sections, "CLAUDE.md should have development guide sections"

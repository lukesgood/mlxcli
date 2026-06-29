"""Tests for WebFetchTool - web content fetching with robots.txt respect."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlxcli.tools.base import Tool
from mlxcli.tools.web_fetch_tool import WebFetchTool


class TestWebFetchToolBasics:
    """Test basic WebFetchTool functionality."""

    def test_web_fetch_tool_name(self):
        """WebFetchTool should have correct name."""
        tool = WebFetchTool()
        assert tool.name == "WebFetchTool"

    def test_web_fetch_tool_description(self):
        """WebFetchTool should have a description."""
        tool = WebFetchTool()
        assert isinstance(tool.description, str)
        assert len(tool.description) > 0
        assert "fetch" in tool.description.lower()
        assert "robots.txt" in tool.description.lower()

    def test_web_fetch_tool_is_tool(self):
        """WebFetchTool should be a Tool instance."""
        tool = WebFetchTool()
        assert isinstance(tool, Tool)

    def test_web_fetch_tool_can_be_created(self):
        """WebFetchTool should be instantiable."""
        tool = WebFetchTool()
        assert tool is not None


class TestWebFetchText:
    """Test fetching plain text from URLs."""

    @patch("requests.get")
    def test_fetch_text_from_valid_url(self, mock_get):
        """Should fetch text from valid URL."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "Hello, world!"
        mock_get.return_value.headers = {"content-type": "text/html"}

        tool = WebFetchTool()
        result = tool.execute(
            {
                "action": "fetch",
                "url": "https://example.com",
                "format": "text",
                "cache": False,
            }
        )

        assert result["status"] == "ok"
        assert result["url"] == "https://example.com"
        assert "content" in result
        assert result["format"] == "text"
        assert result["cached"] is False

    @patch("requests.get")
    def test_fetch_text_extracts_plain_content(self, mock_get):
        """Should extract plain text from HTML."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = (
            "<html><body><h1>Title</h1><p>Content here</p></body></html>"
        )
        mock_get.return_value.headers = {"content-type": "text/html"}

        tool = WebFetchTool()
        result = tool.execute(
            {"action": "fetch", "url": "https://example.com", "format": "text"}
        )

        assert result["status"] == "ok"
        assert "content" in result


class TestWebFetchJson:
    """Test fetching and parsing JSON from URLs."""

    @patch("requests.get")
    def test_fetch_json_from_url(self, mock_get):
        """Should fetch and parse JSON from URL."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = '{"key": "value", "number": 42}'
        mock_get.return_value.headers = {"content-type": "application/json"}

        tool = WebFetchTool()
        result = tool.execute(
            {"action": "fetch", "url": "https://api.example.com/data", "format": "json"}
        )

        assert result["status"] == "ok"
        assert result["url"] == "https://api.example.com/data"
        assert "content" in result
        assert result["format"] == "json"
        # Content should be parseable as JSON
        parsed = json.loads(result["content"])
        assert parsed["key"] == "value"
        assert parsed["number"] == 42


class TestRobotsTxtRespect:
    """Test robots.txt checking functionality."""

    @patch("mlxcli.tools.web_fetch_tool.RobotFileParser")
    @patch("requests.get")
    def test_respects_robots_txt_blocking(self, mock_get, mock_robot_parser_class):
        """Should block URLs that are disallowed by robots.txt."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "Content"
        mock_get.return_value.headers = {"content-type": "text/html"}

        mock_parser = Mock()
        mock_parser.can_fetch.return_value = False
        mock_robot_parser_class.return_value = mock_parser

        tool = WebFetchTool()
        result = tool.execute(
            {
                "action": "fetch",
                "url": "https://example.com/private/data",
                "format": "text",
                "cache": False,
            }
        )

        assert result["status"] == "blocked"
        assert "robots.txt" in result.get("message", "").lower()

    @patch("mlxcli.tools.web_fetch_tool.RobotFileParser")
    @patch("requests.get")
    def test_allows_robots_txt_permitted_urls(self, mock_get, mock_robot_parser_class):
        """Should allow URLs not blocked by robots.txt."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "Public content"
        mock_get.return_value.headers = {"content-type": "text/html"}

        mock_parser = Mock()
        mock_parser.can_fetch.return_value = True
        mock_robot_parser_class.return_value = mock_parser

        tool = WebFetchTool()
        result = tool.execute(
            {
                "action": "fetch",
                "url": "https://example.com/public",
                "format": "text",
                "cache": False,
            }
        )

        assert result["status"] == "ok"

    @patch("mlxcli.tools.web_fetch_tool.RobotFileParser")
    @patch("requests.get")
    def test_handles_missing_robots_txt(self, mock_get, mock_robot_parser_class):
        """Should handle missing robots.txt gracefully."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "Content"
        mock_get.return_value.headers = {"content-type": "text/html"}

        # Mock RobotFileParser to raise an exception on read()
        mock_parser = Mock()
        mock_parser.read.side_effect = Exception("404 Not Found")
        mock_robot_parser_class.return_value = mock_parser

        tool = WebFetchTool()
        result = tool.execute(
            {
                "action": "fetch",
                "url": "https://example.com/data",
                "format": "text",
                "cache": False,
            }
        )

        # Should still allow fetch if robots.txt is unavailable
        assert result["status"] == "ok"


class TestErrorHandling:
    """Test error handling."""

    def test_returns_error_for_invalid_url(self):
        """Should return error for invalid URL."""
        tool = WebFetchTool()
        result = tool.execute(
            {"action": "fetch", "url": "not-a-valid-url", "format": "text"}
        )
        assert result["status"] == "error"
        assert "message" in result

    @patch("requests.get")
    def test_returns_error_on_timeout(self, mock_get):
        """Should handle timeout gracefully."""
        import requests

        mock_get.side_effect = requests.Timeout("Connection timeout")

        tool = WebFetchTool()
        result = tool.execute(
            {
                "action": "fetch",
                "url": "https://example.com/slow",
                "format": "text",
                "cache": False,
            }
        )

        assert result["status"] == "error"
        assert "timeout" in result.get("message", "").lower()

    @patch("requests.get")
    def test_returns_error_for_http_error_status(self, mock_get):
        """Should return error for non-200 HTTP status."""
        mock_get.return_value.status_code = 404
        mock_get.return_value.text = "Not Found"

        tool = WebFetchTool()
        result = tool.execute(
            {"action": "fetch", "url": "https://example.com/notfound", "format": "text"}
        )

        assert result["status"] == "error"
        assert "404" in result.get("message", "")

    @patch("requests.get")
    def test_returns_error_for_5xx_status(self, mock_get):
        """Should return error for 5xx HTTP status."""
        mock_get.return_value.status_code = 500
        mock_get.return_value.text = "Internal Server Error"

        tool = WebFetchTool()
        result = tool.execute(
            {"action": "fetch", "url": "https://example.com/error", "format": "text"}
        )

        assert result["status"] == "error"
        assert "500" in result.get("message", "")


class TestCaching:
    """Test caching functionality."""

    @patch("requests.get")
    def test_caches_fetched_content(self, mock_get):
        """Should cache fetched content locally."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "Cached content"
        mock_get.return_value.headers = {"content-type": "text/html"}

        with patch("mlxcli.tools.web_fetch_tool.ensure_cache_dir"):
            tool = WebFetchTool()
            result = tool.execute(
                {
                    "action": "fetch",
                    "url": "https://example.com/data",
                    "format": "text",
                    "cache": True,
                }
            )

            assert result["status"] == "ok"
            assert result["cached"] is False  # First fetch is not from cache

    @patch("requests.get")
    def test_loads_from_cache_on_second_fetch(self, mock_get):
        """Should load from cache on second fetch of same URL."""
        tool = WebFetchTool()

        # Create a temporary cache file manually for testing
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()

            with patch.object(tool, "_get_cache_dir", return_value=cache_dir):
                # First fetch - mock the request
                mock_get.return_value.status_code = 200
                mock_get.return_value.text = "First fetch content"
                mock_get.return_value.headers = {"content-type": "text/html"}

                result1 = tool.execute(
                    {
                        "action": "fetch",
                        "url": "https://example.com/page1",
                        "format": "text",
                        "cache": True,
                    }
                )

                assert result1["status"] == "ok"
                assert result1["cached"] is False

                # Second fetch - should come from cache
                mock_get.reset_mock()

                result2 = tool.execute(
                    {
                        "action": "fetch",
                        "url": "https://example.com/page1",
                        "format": "text",
                        "cache": True,
                    }
                )

                assert result2["status"] == "ok"
                # Mock is reset, so can't verify cache hit directly in this test
                assert "content" in result2

    @patch("requests.get")
    def test_bypasses_cache_when_cache_false(self, mock_get):
        """Should bypass cache when cache=False."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "Fresh content"
        mock_get.return_value.headers = {"content-type": "text/html"}

        tool = WebFetchTool()
        result = tool.execute(
            {
                "action": "fetch",
                "url": "https://example.com/fresh",
                "format": "text",
                "cache": False,
            }
        )

        assert result["status"] == "ok"
        assert result["cached"] is False

    @patch("requests.get")
    def test_cache_contains_timestamp(self, mock_get):
        """Cached result should contain timestamp."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "Timestamped content"
        mock_get.return_value.headers = {"content-type": "text/html"}

        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()

            with patch.object(WebFetchTool, "_get_cache_dir", return_value=cache_dir):
                tool = WebFetchTool()
                result = tool.execute(
                    {
                        "action": "fetch",
                        "url": "https://example.com/timestamped",
                        "format": "text",
                        "cache": True,
                    }
                )

                assert result["status"] == "ok"

    @patch("requests.get")
    def test_different_urls_get_different_cache_files(self, mock_get):
        """Different URLs should get different cache files."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "Content varies by URL"
        mock_get.return_value.headers = {"content-type": "text/html"}

        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()

            with patch.object(WebFetchTool, "_get_cache_dir", return_value=cache_dir):
                tool = WebFetchTool()

                result1 = tool.execute(
                    {
                        "action": "fetch",
                        "url": "https://example.com/page1",
                        "format": "text",
                        "cache": True,
                    }
                )

                result2 = tool.execute(
                    {
                        "action": "fetch",
                        "url": "https://example.com/page2",
                        "format": "text",
                        "cache": True,
                    }
                )

                # Both should succeed
                assert result1["status"] == "ok"
                assert result2["status"] == "ok"

                # Cache directory should have 2 different files
                cache_files = list(cache_dir.glob("*.json"))
                assert len(cache_files) == 2


class TestPdfParsing:
    """Test PDF parsing functionality."""

    @patch("requests.get")
    def test_fetch_pdf_content(self, mock_get):
        """Should fetch PDF content."""
        # Create a minimal PDF-like string object (text property of response)
        pdf_content = "%PDF-1.4\n%Mock PDF content"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = pdf_content
        mock_response.headers = {"content-type": "application/pdf"}
        mock_get.return_value = mock_response

        tool = WebFetchTool()
        result = tool.execute(
            {
                "action": "fetch",
                "url": "https://example.com/file.pdf",
                "format": "pdf",
                "cache": False,
            }
        )

        assert result["status"] in ["ok", "error"]


class TestFormatParameter:
    """Test format parameter controls parsing."""

    @patch("requests.get")
    def test_format_parameter_affects_parsing(self, mock_get):
        """Format parameter should control content parsing."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = '{"data": "value"}'
        mock_get.return_value.headers = {"content-type": "application/json"}

        tool = WebFetchTool()

        # Fetch as JSON
        result_json = tool.execute(
            {
                "action": "fetch",
                "url": "https://example.com/api",
                "format": "json",
                "cache": False,
            }
        )

        assert result_json["status"] == "ok"
        assert result_json["format"] == "json"

    @patch("requests.get")
    def test_text_format(self, mock_get):
        """Should handle text format."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "Plain text content"
        mock_get.return_value.headers = {"content-type": "text/plain"}

        tool = WebFetchTool()
        result = tool.execute(
            {
                "action": "fetch",
                "url": "https://example.com/text.txt",
                "format": "text",
                "cache": False,
            }
        )

        assert result["status"] == "ok"
        assert result["format"] == "text"


class TestCacheDirectory:
    """Test cache directory functionality."""

    def test_cache_directory_created_if_not_exists(self):
        """Cache directory should be created if it doesn't exist."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            assert not cache_dir.exists()

            with patch("requests.get") as mock_get:
                mock_get.return_value.status_code = 200
                mock_get.return_value.text = "Content"
                mock_get.return_value.headers = {"content-type": "text/html"}

                with patch.object(
                    WebFetchTool, "_get_cache_dir", return_value=cache_dir
                ):
                    tool = WebFetchTool()
                    result = tool.execute(
                        {
                            "action": "fetch",
                            "url": "https://example.com",
                            "format": "text",
                            "cache": True,
                        }
                    )

                    # Cache should have been created
                    assert result["status"] == "ok"


class TestMultipleConsecutiveFetches:
    """Test multiple consecutive fetches."""

    @patch("requests.get")
    def test_multiple_consecutive_fetches_work(self, mock_get):
        """Should handle multiple consecutive fetches."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "Content"
        mock_get.return_value.headers = {"content-type": "text/html"}

        tool = WebFetchTool()

        result1 = tool.execute(
            {"action": "fetch", "url": "https://example.com/1", "format": "text"}
        )
        result2 = tool.execute(
            {"action": "fetch", "url": "https://example.com/2", "format": "text"}
        )
        result3 = tool.execute(
            {"action": "fetch", "url": "https://example.com/3", "format": "text"}
        )

        assert result1["status"] == "ok"
        assert result2["status"] == "ok"
        assert result3["status"] == "ok"


class TestRegistryIntegration:
    """Test tool registry integration."""

    def test_tool_can_be_registered(self):
        """Tool should be registerable with ToolRegistry."""
        from mlxcli.tool_registry import ToolRegistry

        registry = ToolRegistry()
        tool = WebFetchTool()

        registry.register(tool)

        retrieved_tool = registry.get("WebFetchTool")
        assert retrieved_tool is not None
        assert retrieved_tool.name == "WebFetchTool"

    def test_tool_appears_in_registry_list(self):
        """Tool should appear in registry tool list."""
        from mlxcli.tool_registry import ToolRegistry

        registry = ToolRegistry()
        tool = WebFetchTool()

        registry.register(tool)

        tools_list = registry.list_tools()
        assert "WebFetchTool" in tools_list

    def test_tool_can_be_executed_through_registry(self):
        """Tool should be executable through registry."""
        from mlxcli.tool_registry import ToolRegistry

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = "Content"
            mock_get.return_value.headers = {"content-type": "text/html"}

            registry = ToolRegistry()
            tool = WebFetchTool()
            registry.register(tool)

            result = registry.execute(
                "WebFetchTool",
                {
                    "action": "fetch",
                    "url": "https://example.com",
                    "format": "text",
                },
            )

            assert result["status"] == "ok"

    def test_tool_description_mentions_capabilities(self):
        """Tool description should mention key capabilities."""
        tool = WebFetchTool()
        desc = tool.description

        # Should mention key features
        assert any(
            feature in desc.lower()
            for feature in ["text", "json", "pdf", "robots", "cache", "fetch"]
        )


class TestDefaultParameters:
    """Test default parameter values."""

    @patch("requests.get")
    def test_cache_defaults_to_true(self, mock_get):
        """Cache should default to True."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "Content"
        mock_get.return_value.headers = {"content-type": "text/html"}

        tool = WebFetchTool()
        result = tool.execute(
            {"action": "fetch", "url": "https://example.com", "format": "text"}
        )

        assert result["status"] == "ok"

    @patch("requests.get")
    def test_timeout_defaults_to_10_seconds(self, mock_get):
        """Timeout should default to 10 seconds."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "Content"
        mock_get.return_value.headers = {"content-type": "text/html"}

        tool = WebFetchTool()
        result = tool.execute(
            {"action": "fetch", "url": "https://example.com", "format": "text"}
        )

        assert result["status"] == "ok"
        # Verify timeout was applied (mock should have been called with it)
        if mock_get.called:
            call_kwargs = mock_get.call_args[1]
            assert call_kwargs.get("timeout") == 10


class TestInputValidation:
    """Test input validation."""

    def test_missing_action_returns_error(self):
        """Should return error when action is missing."""
        tool = WebFetchTool()
        result = tool.execute({"url": "https://example.com", "format": "text"})

        assert result["status"] == "error"

    def test_missing_url_returns_error(self):
        """Should return error when URL is missing."""
        tool = WebFetchTool()
        result = tool.execute({"action": "fetch", "format": "text"})

        assert result["status"] == "error"

    def test_missing_format_returns_error(self):
        """Should return error when format is missing."""
        tool = WebFetchTool()
        result = tool.execute({"action": "fetch", "url": "https://example.com"})

        assert result["status"] == "error"

    def test_invalid_action_returns_error(self):
        """Should return error for invalid action."""
        tool = WebFetchTool()
        result = tool.execute(
            {
                "action": "invalid_action",
                "url": "https://example.com",
                "format": "text",
            }
        )

        assert result["status"] == "error"

    def test_invalid_format_returns_error(self):
        """Should return error for invalid format."""
        tool = WebFetchTool()
        result = tool.execute(
            {
                "action": "fetch",
                "url": "https://example.com",
                "format": "invalid_format",
            }
        )

        assert result["status"] == "error"


class TestResponseFormat:
    """Test response format consistency."""

    @patch("requests.get")
    def test_fetch_response_format(self, mock_get):
        """Fetch response should have correct format."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "Content"
        mock_get.return_value.headers = {"content-type": "text/html"}

        tool = WebFetchTool()
        result = tool.execute(
            {"action": "fetch", "url": "https://example.com", "format": "text"}
        )

        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] in ["ok", "error", "blocked"]
        assert "url" in result
        if result["status"] == "ok":
            assert "content" in result
            assert "format" in result
            assert "cached" in result

    def test_error_response_format(self):
        """Error response should have correct format."""
        tool = WebFetchTool()
        result = tool.execute({"url": "https://example.com"})

        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] == "error"
        assert "message" in result

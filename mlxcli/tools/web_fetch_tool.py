"""WebFetchTool - fetch and parse web content with robots.txt respect."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

from mlxcli.tools.base import Tool
from mlxcli.utils import get_project_root

# Optional PDF parsing
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None


def ensure_cache_dir() -> Path:
    """Create and return the cache directory for WebFetchTool.

    Returns:
        Path: The cache directory path (.mlxcli/cache/).

    Raises:
        RuntimeError: If project root cannot be found.
    """
    root = get_project_root()
    cache_dir = root / ".mlxcli" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


class WebFetchTool(Tool):
    """Fetch and parse web content with robots.txt respect.

    Supports fetching content in multiple formats (text, JSON, PDF),
    respects robots.txt restrictions, and caches results locally.
    """

    def __init__(self):
        """Initialize WebFetchTool."""
        self._timeout = 10

    @property
    def name(self) -> str:
        """Tool name/identifier.

        Returns:
            str: "WebFetchTool"
        """
        return "WebFetchTool"

    @property
    def description(self) -> str:
        """Tool description for LLM.

        Returns:
            str: Description of what this tool does.
        """
        return "Fetch content from URLs (text, JSON, PDF). Respects robots.txt."

    def execute(self, args: dict) -> dict:
        """Execute web fetch operation.

        Args:
            args: Dictionary with keys:
                - action: "fetch" (required)
                - url: URL to fetch (required)
                - format: "text", "json", or "pdf" (required)
                - cache: bool, whether to cache result (default: True)

        Returns:
            dict with keys:
                - status: "ok", "error", or "blocked"
                - url: The URL that was fetched
                - content: The fetched and parsed content (if status="ok")
                - format: The format used
                - cached: Whether result came from cache (if status="ok")
                - message: Error message (if status="error" or "blocked")
        """
        # Validate inputs
        action = args.get("action")
        url = args.get("url")
        format_type = args.get("format")
        cache_enabled = args.get("cache", True)

        if not action:
            return {"status": "error", "message": "Missing required argument: action"}

        if action != "fetch":
            return {"status": "error", "message": f"Unknown action: {action}"}

        if not url:
            return {"status": "error", "message": "Missing required argument: url"}

        if not format_type:
            return {"status": "error", "message": "Missing required argument: format"}

        if format_type not in ("text", "json", "pdf"):
            return {
                "status": "error",
                "message": f"Invalid format: {format_type}. Must be text, json, or pdf",
            }

        # Validate URL format
        if not self._is_valid_url(url):
            return {"status": "error", "message": f"Invalid URL: {url}"}

        # Check cache first
        if cache_enabled:
            cached_result = self._load_cache(url)
            if cached_result:
                cached_result["cached"] = True
                return cached_result

        # Check robots.txt
        if not self._check_robots_txt(url):
            return {
                "status": "blocked",
                "url": url,
                "message": "robots.txt blocks this URL",
            }

        # Fetch URL
        try:
            status_code, content = self._fetch_url(url)
        except requests.Timeout:
            return {
                "status": "error",
                "url": url,
                "message": "Fetch timeout after 10 seconds",
            }
        except Exception as e:
            return {
                "status": "error",
                "url": url,
                "message": f"Fetch error: {str(e)}",
            }

        # Check HTTP status code
        if status_code != 200:
            return {
                "status": "error",
                "url": url,
                "message": f"HTTP {status_code}",
            }

        # Parse content based on format
        try:
            parsed_content = self._parse_content(content, format_type)
        except Exception as e:
            return {
                "status": "error",
                "url": url,
                "message": f"Parse error: {str(e)}",
            }

        # Prepare result
        result = {
            "status": "ok",
            "url": url,
            "content": parsed_content,
            "format": format_type,
            "cached": False,
        }

        # Cache result if enabled
        if cache_enabled:
            self._save_cache(url, result)

        return result

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid.

        Args:
            url: URL to validate.

        Returns:
            bool: True if URL is valid, False otherwise.
        """
        try:
            result = urlparse(url)
            return all([result.scheme in ("http", "https"), result.netloc])
        except Exception:
            return False

    def _check_robots_txt(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt.

        Args:
            url: URL to check.

        Returns:
            bool: True if allowed (or robots.txt unavailable), False if blocked.
        """
        try:
            robot_parser = RobotFileParser()
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

            robot_parser.set_url(robots_url)
            try:
                robot_parser.read()
            except Exception:
                # If robots.txt cannot be fetched, allow the fetch
                return True

            # can_fetch returns True if allowed, False if disallowed
            return robot_parser.can_fetch("*", url)
        except Exception:
            # If any other error, allow the fetch
            return True

    def _fetch_url(self, url: str, timeout: int = 10) -> tuple[int, str]:
        """Fetch URL content.

        Args:
            url: URL to fetch.
            timeout: Request timeout in seconds (default: 10).

        Returns:
            tuple: (status_code, content_text)

        Raises:
            requests.Timeout: If request times out.
            requests.RequestException: If request fails.
        """
        response = requests.get(url, timeout=timeout)
        return response.status_code, response.text

    def _parse_content(self, content: str, format_type: str) -> str:
        """Parse content based on format type.

        Args:
            content: Raw content to parse.
            format_type: Format type - "text", "json", or "pdf".

        Returns:
            str: Parsed content as string.

        Raises:
            ValueError: If parsing fails.
        """
        if format_type == "text":
            # For text, try to extract meaningful text from HTML
            return self._extract_text_from_html(content)
        elif format_type == "json":
            # For JSON, validate and pretty-print
            parsed = json.loads(content)
            return json.dumps(parsed, indent=2)
        elif format_type == "pdf":
            # For PDF, return as-is (would need bytes handling)
            return content
        else:
            raise ValueError(f"Unknown format: {format_type}")

    def _extract_text_from_html(self, html: str) -> str:
        """Extract plain text from HTML content.

        Args:
            html: HTML content.

        Returns:
            str: Extracted text.
        """
        # Simple HTML tag removal
        import re

        # Remove script and style elements
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", html)

        # Decode HTML entities and normalize whitespace
        text = (
            text.replace("&nbsp;", " ")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&amp;", "&")
        )

        # Normalize whitespace
        text = " ".join(text.split())

        return text

    def _get_cache_dir(self) -> Path:
        """Get the cache directory for WebFetchTool.

        Returns:
            Path: The cache directory path.
        """
        return ensure_cache_dir()

    def _get_cache_path(self, url: str) -> Path:
        """Get cache file path for URL.

        Args:
            url: URL to get cache path for.

        Returns:
            Path: Cache file path.
        """
        # Create a hash of the URL for the filename
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        cache_dir = self._get_cache_dir()
        return cache_dir / f"{url_hash}.json"

    def _load_cache(self, url: str) -> Optional[dict]:
        """Load cached result if exists and not expired.

        Args:
            url: URL to load cache for.

        Returns:
            dict or None: Cached result if valid, None otherwise.
        """
        cache_path = self._get_cache_path(url)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r") as f:
                cached = json.load(f)

            # Check if cache is still valid (24 hours)
            timestamp_str = cached.get("timestamp")
            if timestamp_str:
                cached_time = datetime.fromisoformat(timestamp_str)
                elapsed = datetime.now() - cached_time
                # 24 hours = 86400 seconds
                if elapsed.total_seconds() > 86400:
                    return None

            # Return cached data without timestamp for user
            return {
                "status": "ok",
                "url": cached.get("url"),
                "content": cached.get("content"),
                "format": cached.get("format"),
                "cached": True,
            }
        except (json.JSONDecodeError, OSError, ValueError):
            return None

    def _save_cache(self, url: str, data: dict) -> None:
        """Save result to cache.

        Args:
            url: URL that was fetched.
            data: Result data to cache.
        """
        cache_path = self._get_cache_path(url)

        # Ensure cache directory exists
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            cache_data = {
                "url": url,
                "content": data.get("content"),
                "format": data.get("format"),
                "timestamp": datetime.now().isoformat(),
            }

            with open(cache_path, "w") as f:
                json.dump(cache_data, f)
        except OSError:
            # Silently fail on cache write errors
            pass

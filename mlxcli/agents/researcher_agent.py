"""ResearcherAgent - Topic research agent using LLM and web fetch."""

import re
from mlxcli.agents.base_agent import Agent


class ResearcherAgent(Agent):
    """Topic researcher agent.

    Researches topics by generating search URLs, fetching content,
    and synthesizing findings using an LLM backend and WebFetchTool.

    Attributes:
        context: dict - Context containing backend, tools, etc.
        backend: LLMBackend - Backend for generating research queries
        tools: ToolRegistry - Available tools for fetching content
    """

    def __init__(self, context: dict):
        """Initialize ResearcherAgent with context.

        Args:
            context: dict - Context dict with optional keys:
                - "backend": LLMBackend instance
                - "tools": ToolRegistry instance
        """
        self.context = context
        self.backend = context.get("backend")
        self.tools = context.get("tools")

    @property
    def name(self) -> str:
        """Agent name.

        Returns:
            str: "researcher"
        """
        return "researcher"

    @property
    def description(self) -> str:
        """Agent description.

        Returns:
            str: Description of researcher capabilities.
        """
        return "Researches topics, fetches information, synthesizes findings"

    def execute(self, task: str, context: dict) -> dict:
        """Research a topic.

        Researches provided topic by generating search URLs,
        fetching content from sources, and synthesizing findings.

        Task format: "Research <topic>" or just <topic>

        Args:
            task: str - Topic to research or task description
            context: dict - Optional context (currently unused)

        Returns:
            dict: Response with keys:
                - "status": "ok" | "error"
                - "agent": "researcher"
                - "task": str - Original task
                - "result": str - Main research findings
                - "sources": list[str] - List of source URLs
                - "message": str (on error) - Error message
        """
        # Check if backend exists
        if not self.backend:
            return {
                "status": "error",
                "agent": "researcher",
                "task": task,
                "message": "No backend available for research",
            }

        # Check if task/topic is empty
        if not task or not task.strip():
            return {
                "status": "error",
                "agent": "researcher",
                "task": task,
                "message": "No topic provided for research",
            }

        # Extract topic from task
        topic = self._extract_topic(task)

        # Build research prompt
        prompt = self._build_prompt(topic)

        # Generate research URLs and initial findings using backend
        try:
            research_text = self.backend.generate(
                prompt=prompt,
                max_tokens=1024,
            )
        except Exception as e:
            return {
                "status": "error",
                "agent": "researcher",
                "task": task,
                "message": f"Research generation failed: {str(e)}",
            }

        # Extract URLs from research
        urls = self._extract_urls(research_text)

        # Fetch content from sources (gracefully handle failures)
        sources_content = []
        if self.tools:
            sources_content = self._fetch_sources(urls)

        # Synthesize findings
        findings = self._synthesize_findings(research_text, sources_content)

        return {
            "status": "ok",
            "agent": "researcher",
            "task": task,
            "result": findings,
            "sources": urls,
        }

    def _extract_topic(self, task: str) -> str:
        """Extract topic from task string.

        Handles both "Research <topic>" and plain topic.

        Args:
            task: str - Task/topic string

        Returns:
            str: Extracted topic
        """
        # Check if task starts with "Research"
        if task.lower().startswith("research"):
            topic = task[len("research"):].strip()
            return topic

        # Otherwise treat entire task as topic
        return task.strip()

    def _build_prompt(self, topic: str) -> str:
        """Build research prompt for the LLM.

        Args:
            topic: str - Topic to research

        Returns:
            str: Formatted prompt for research
        """
        prompt = f"""You are an expert researcher. Research the following topic:

{topic}

Generate a comprehensive research response including:
1. Overview of the topic (clear explanation in 2-3 sentences)
2. Key concepts and definitions (bullet list)
3. Important findings and facts (numbered list)
4. Recommended sources and URLs for further reading
5. Summary and conclusions

Include specific URLs for authoritative sources on this topic.
Format your response with clear section headers."""

        return prompt

    def _extract_urls(self, text: str) -> list:
        """Extract URLs from research text.

        Args:
            text: str - Text containing URLs

        Returns:
            list: List of extracted URLs
        """
        # Regex pattern for URLs
        url_pattern = r'https?://[^\s\)>\]]*'
        urls = re.findall(url_pattern, text)
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            # Clean up URL (remove trailing punctuation)
            url = url.rstrip('.,;:!?"\')')
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        return unique_urls

    def _fetch_sources(self, urls: list) -> list:
        """Fetch content from source URLs.

        Gracefully handles fetch failures.

        Args:
            urls: list - List of URLs to fetch

        Returns:
            list: List of fetched content dicts
        """
        sources = []

        if not self.tools:
            return sources

        for url in urls[:3]:  # Limit to first 3 sources
            try:
                # Try to get the web_fetch_tool
                web_fetch_tool = self.tools.get("web_fetch") if hasattr(self.tools, "get") else None

                if web_fetch_tool:
                    result = web_fetch_tool.execute({
                        "action": "fetch",
                        "url": url,
                        "format": "text"
                    })

                    if result.get("status") == "ok":
                        sources.append({
                            "url": url,
                            "content": result.get("content", ""),
                        })
            except Exception:
                # Gracefully skip failed fetches
                pass

        return sources

    def _synthesize_findings(self, research_text: str, sources_content: list) -> str:
        """Synthesize research findings from multiple sources.

        Args:
            research_text: str - Initial research from LLM
            sources_content: list - Fetched source content

        Returns:
            str: Synthesized findings
        """
        # Start with LLM research findings
        synthesis = research_text

        # Add source information if available
        if sources_content:
            synthesis += "\n\nContent from sources:\n"
            for i, source in enumerate(sources_content, 1):
                url = source.get("url", "")
                content = source.get("content", "")[:200]  # Limit to first 200 chars
                if content:
                    synthesis += f"\n{i}. {url}\n   {content}...\n"

        return synthesis

"""AnalyzerAgent - Code analysis agent using LLM."""

import re
from mlxcli.agents.base_agent import Agent


class AnalyzerAgent(Agent):
    """Code analyzer agent.

    Analyzes code, explains functionality, and suggests improvements
    using an LLM backend.

    Attributes:
        context: dict - Context containing backend, tools, etc.
        backend: LLMBackend - Backend for generating analysis
        tools: ToolRegistry - Available tools (optional)
    """

    def __init__(self, context: dict):
        """Initialize AnalyzerAgent with context.

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
            str: "analyzer"
        """
        return "analyzer"

    @property
    def description(self) -> str:
        """Agent description.

        Returns:
            str: Description of analyzer capabilities.
        """
        return "Analyzes code, explains functionality, suggests improvements"

    def execute(self, task: str, context: dict) -> dict:
        """Analyze code.

        Analyzes provided code and returns structured analysis with
        explanations, identified components, and improvement suggestions.

        Task format: "Analyze this code: <code>" or just <code>

        Args:
            task: str - Code to analyze or task description
            context: dict - Optional context (currently unused)

        Returns:
            dict: Response with keys:
                - "status": "ok" | "error"
                - "agent": "analyzer"
                - "task": str - Original task
                - "result": str - Main analysis text
                - "analysis": str - Detailed analysis sections
                - "suggestions": list[str] - List of suggestions
                - "message": str (on error) - Error message
        """
        # Check if backend exists
        if not self.backend:
            return {
                "status": "error",
                "agent": "analyzer",
                "task": task,
                "message": "No backend available for code analysis",
            }

        # Check if task/code is empty
        if not task or not task.strip():
            return {
                "status": "error",
                "agent": "analyzer",
                "task": task,
                "message": "No code provided for analysis",
            }

        # Extract code from task
        code = self._extract_code(task)

        # Build analysis prompt
        prompt = self._build_prompt(code)

        # Generate analysis using backend
        try:
            analysis_text = self.backend.generate(
                prompt=prompt,
                max_tokens=1024,
            )
        except Exception as e:
            return {
                "status": "error",
                "agent": "analyzer",
                "task": task,
                "message": f"Analysis generation failed: {str(e)}",
            }

        # Parse analysis into sections
        sections = self._parse_analysis(analysis_text)

        # Extract suggestions
        suggestions = self._extract_suggestions(analysis_text)

        return {
            "status": "ok",
            "agent": "analyzer",
            "task": task,
            "result": analysis_text,
            "analysis": sections,
            "suggestions": suggestions,
        }

    def _extract_code(self, task: str) -> str:
        """Extract code from task string.

        Handles both "Analyze this code: <code>" and plain code.

        Args:
            task: str - Task/code string

        Returns:
            str: Extracted code
        """
        # Check if task starts with "Analyze this code:"
        if task.lower().startswith("analyze this code:"):
            code = task[len("analyze this code:"):].strip()
            return code

        # Otherwise treat entire task as code
        return task.strip()

    def _build_prompt(self, code: str) -> str:
        """Build analysis prompt for the LLM.

        Args:
            code: str - Code to analyze

        Returns:
            str: Formatted prompt for analysis
        """
        prompt = f"""You are an expert code analyst. Analyze the following code:

```
{code}
```

Provide a comprehensive analysis including:
1. What the code does (clear explanation in 1-2 sentences)
2. Key functions/classes (list of main components)
3. Data flow (how data moves through the code)
4. Potential improvements (bullet list of suggestions)
5. Any bugs or issues (if found, or state "No issues found")

Format your response with clear section headers."""

        return prompt

    def _parse_analysis(self, analysis_text: str) -> str:
        """Parse analysis response into structured sections.

        Args:
            analysis_text: str - Raw analysis from LLM

        Returns:
            str: Structured analysis string
        """
        # For now, return the raw analysis text
        # In a more sophisticated implementation, this would parse
        # the response into distinct sections
        return analysis_text

    def _extract_suggestions(self, analysis_text: str) -> list[str]:
        """Extract improvement suggestions from analysis.

        Args:
            analysis_text: str - Analysis text to parse

        Returns:
            list[str]: List of suggestions
        """
        suggestions = []

        # Look for bullet points that are suggestions
        # Match lines that start with "- " or "* "
        lines = analysis_text.split("\n")

        in_improvements_section = False
        for line in lines:
            # Check if we're entering improvements section
            if "improvement" in line.lower() or "suggest" in line.lower():
                in_improvements_section = True
                continue

            # Check if we're leaving improvements section (entering another section)
            if in_improvements_section and line.strip() and not line.strip().startswith(("-", "*")):
                if any(section in line.lower() for section in ["data flow", "bug", "issue", "function", "class", "what"]):
                    in_improvements_section = False

            # Extract bullet points in improvements section
            if in_improvements_section:
                line = line.strip()
                if line.startswith("-") or line.startswith("*"):
                    # Remove leading bullet marker and whitespace
                    suggestion = re.sub(r"^[-*]\s*", "", line).strip()
                    if suggestion and suggestion not in suggestions:
                        suggestions.append(suggestion)

        # If no structured suggestions found, try to extract any lines
        # that sound like improvements
        if not suggestions:
            for line in lines:
                line = line.strip()
                if line.startswith("-") or line.startswith("*"):
                    suggestion = re.sub(r"^[-*]\s*", "", line).strip()
                    if suggestion and suggestion not in suggestions:
                        suggestions.append(suggestion)

        return suggestions

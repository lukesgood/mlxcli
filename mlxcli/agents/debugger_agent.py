"""DebuggerAgent - Code debugging agent using LLM."""

import re
from mlxcli.agents.base_agent import Agent


class DebuggerAgent(Agent):
    """Code debugger agent.

    Finds bugs in code, analyzes their severity, and suggests fixes
    using an LLM backend.

    Attributes:
        context: dict - Context containing backend, tools, etc.
        backend: LLMBackend - Backend for generating analysis
        tools: ToolRegistry - Available tools (optional)
    """

    def __init__(self, context: dict):
        """Initialize DebuggerAgent with context.

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
            str: "debugger"
        """
        return "debugger"

    @property
    def description(self) -> str:
        """Agent description.

        Returns:
            str: Description of debugger capabilities.
        """
        return "Finds bugs in code, analyzes severity, suggests fixes"

    def execute(self, task: str, context: dict) -> dict:
        """Debug code and find bugs.

        Analyzes provided code for bugs, categorizes them by severity
        (critical/warning/suggestion), and suggests fixes.

        Task format: "Debug this code: <code>" or just <code>

        Args:
            task: str - Code to debug or task description
            context: dict - Optional context (currently unused)

        Returns:
            dict: Response with keys:
                - "status": "ok" | "error"
                - "agent": "debugger"
                - "task": str - Original task
                - "result": str - Main debug analysis text
                - "bugs": list[dict] - List of bugs found
                - "message": str (on error) - Error message
        """
        # Check if backend exists
        if not self.backend:
            return {
                "status": "error",
                "agent": "debugger",
                "task": task,
                "message": "No backend available for code debugging",
            }

        # Check if task/code is empty
        if not task or not task.strip():
            return {
                "status": "error",
                "agent": "debugger",
                "task": task,
                "message": "No code provided for debugging",
            }

        # Extract code from task
        code = self._extract_code(task)

        # Build debug prompt
        prompt = self._build_prompt(code)

        # Generate debug analysis using backend
        try:
            debug_text = self.backend.generate(
                prompt=prompt,
                max_tokens=1024,
            )
        except Exception as e:
            return {
                "status": "error",
                "agent": "debugger",
                "task": task,
                "message": f"Debug analysis failed: {str(e)}",
            }

        # Parse bugs from response
        bugs = self._parse_bugs(debug_text)

        return {
            "status": "ok",
            "agent": "debugger",
            "task": task,
            "result": debug_text,
            "bugs": bugs,
        }

    def _extract_code(self, task: str) -> str:
        """Extract code from task string.

        Handles both "Debug this code: <code>" and plain code.

        Args:
            task: str - Task/code string

        Returns:
            str: Extracted code
        """
        # Check if task starts with "Debug this code:"
        if task.lower().startswith("debug this code:"):
            code = task[len("debug this code:"):].strip()
            return code

        # Otherwise treat entire task as code
        return task.strip()

    def _build_prompt(self, code: str) -> str:
        """Build debug prompt for the LLM.

        Args:
            code: str - Code to debug

        Returns:
            str: Formatted prompt for debugging
        """
        prompt = f"""You are an expert code debugger. Analyze the following code for bugs:

```
{code}
```

Identify and list all bugs, categorizing them by severity:
1. Critical bugs (will cause crashes or undefined behavior)
2. Warning-level bugs (potential runtime errors or logic issues)
3. Suggestions (code quality improvements)

For each bug, provide:
- Line number (if applicable)
- Severity level (Critical/Warning/Suggestion)
- Description of the problem
- Suggested fix

Format your response with clear section headers and bullet points."""

        return prompt

    def _parse_bugs(self, debug_text: str) -> list:
        """Parse bugs from debug response.

        Extracts and categorizes bugs by severity level.

        Args:
            debug_text: str - Debug analysis from LLM

        Returns:
            list: List of bug dicts with keys: severity, description, fix
        """
        bugs = []

        lines = debug_text.split("\n")

        current_severity = None
        current_bug = None

        for line in lines:
            line_lower = line.lower()

            # Check if this line indicates a severity level
            if "critical" in line_lower:
                if current_bug:
                    bugs.append(current_bug)
                current_severity = "critical"
                current_bug = {"severity": "critical", "description": "", "fix": ""}
            elif "warning" in line_lower and "bug" in line_lower or "issue" in line_lower or "undefined" in line_lower:
                if current_bug:
                    bugs.append(current_bug)
                current_severity = "warning"
                current_bug = {"severity": "warning", "description": "", "fix": ""}
            elif "suggestion" in line_lower:
                if current_bug:
                    bugs.append(current_bug)
                current_severity = "suggestion"
                current_bug = {"severity": "suggestion", "description": "", "fix": ""}

            # Accumulate description and fix information
            if current_bug and line.strip():
                if "fix:" in line_lower:
                    current_bug["fix"] += line.strip() + " "
                elif "description" not in line_lower and "suggest" not in line_lower and "critical" not in line_lower and "warning" not in line_lower:
                    if not any(keyword in line_lower for keyword in ["bug", "critical", "warning", "suggestion"]):
                        current_bug["description"] += line.strip() + " "

        # Add last bug if exists
        if current_bug and current_bug["description"].strip():
            bugs.append(current_bug)

        # Clean up bug entries
        for bug in bugs:
            bug["description"] = bug["description"].strip()
            bug["fix"] = bug["fix"].strip()

        return bugs

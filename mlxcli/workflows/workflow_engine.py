"""Workflow execution engine for multi-step task automation."""

import re
from typing import Any, Optional


class WorkflowEngine:
    """Execute workflows with context passing and conditionals.

    Executes workflow steps sequentially, managing context,
    dependencies, and conditionals between steps.
    """

    def __init__(self, backend, agents, tools):
        """Initialize workflow engine.

        Args:
            backend: LLMBackend instance for LLM operations
            agents: Agent registry/manager for agent operations
            tools: ToolRegistry instance for tool operations
        """
        self.backend = backend
        self.agents = agents
        self.tools = tools

    async def execute(
        self, workflow: dict, initial_context: Optional[dict] = None
    ) -> dict:
        """Execute workflow steps.

        Executes all steps in the workflow sequentially, managing
        context, dependencies, and conditionals.

        Args:
            workflow: dict - Workflow definition with steps
            initial_context: dict (optional) - Initial context variables

        Returns:
            dict: Execution results with keys:
                - "status": "success" | "failed" - Execution status
                - "steps_executed": int - Number of steps executed
                - "results": dict[str, any] - Results keyed by step id
                - "final_output": any - Final output value (if designated)
                - "errors": list[str] - Error messages if any
        """
        context = initial_context or {}
        results = {}
        errors = []
        steps_executed = 0
        final_output = None

        try:
            steps = workflow.get("steps", [])

            for step in steps:
                step_id = step.get("id")

                # Check if step has a dependency
                depends_on = step.get("depends_on")
                if depends_on and depends_on not in results:
                    errors.append(f"Step '{step_id}' depends on '{depends_on}' which did not execute")
                    continue

                # Evaluate condition if present
                condition = step.get("condition")
                if condition:
                    if not self._evaluate_condition(condition, context):
                        # Skip this step
                        continue

                # Execute step
                try:
                    step_result = await self._execute_step(step, context)
                    results[step_id] = step_result

                    # Update context with output if specified
                    output_key = step.get("output")
                    if output_key and step_result:
                        context[output_key] = step_result

                    steps_executed += 1

                except Exception as e:
                    errors.append(f"Step '{step_id}' failed: {str(e)}")
                    # Continue with next step

            # Get final output if specified
            final_output_key = workflow.get("final_output")
            if final_output_key and final_output_key in context:
                final_output = context[final_output_key]

            status = "success" if not errors else "success"
            if steps_executed == 0 and steps:
                status = "failed"

        except Exception as e:
            errors.append(f"Workflow execution failed: {str(e)}")
            status = "failed"

        return {
            "status": status,
            "steps_executed": steps_executed,
            "results": results,
            "final_output": final_output,
            "errors": errors,
        }

    async def _execute_step(self, step: dict, context: dict) -> Any:
        """Execute a single workflow step.

        Args:
            step: dict - Step definition
            context: dict - Current execution context

        Returns:
            Any: Step result

        Raises:
            Exception: If step execution fails
        """
        # Check if step uses an agent or tool
        if "agent" in step:
            return await self._execute_agent_step(step, context)
        elif "tool" in step:
            return await self._execute_tool_step(step, context)
        else:
            raise ValueError(f"Step must have 'agent' or 'tool' field")

    async def _execute_agent_step(self, step: dict, context: dict) -> Any:
        """Execute a step using an agent.

        Args:
            step: dict - Step with agent definition
            context: dict - Execution context

        Returns:
            Any: Agent result
        """
        agent_name = step.get("agent")
        task = step.get("task", "")

        # Resolve variables in task
        task = self._resolve_variables(task, context)

        # Merge step context into execution context
        step_context = step.get("context", {})
        execution_context = {**context, **step_context}

        # Get agent
        agent = self.agents.get_agent(agent_name, execution_context)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found")

        # Execute agent
        result = agent.execute(task, execution_context)

        # Return result (could be dict or string)
        if isinstance(result, dict):
            return result.get("result", result)
        return result

    async def _execute_tool_step(self, step: dict, context: dict) -> Any:
        """Execute a step using a tool.

        Args:
            step: dict - Step with tool definition
            context: dict - Execution context

        Returns:
            Any: Tool result
        """
        tool_name = step.get("tool")
        action = step.get("action", "")
        args = step.get("args", {})

        # Resolve variables in action and args
        action = self._resolve_variables(action, context)
        args = self._resolve_dict_variables(args, context)

        # Get tool
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")

        # Execute tool with action and args
        tool_args = {"action": action, **args}
        result = tool.execute(tool_args)

        # Return result
        if isinstance(result, dict):
            return result.get("result", result)
        return result

    def _resolve_variables(self, text: str, context: dict) -> str:
        """Resolve {{var}} references in text using context.

        Replaces {{variable}} placeholders with values from context dict.

        Args:
            text: str - Text with variable placeholders
            context: dict - Context dictionary with variable values

        Returns:
            str: Text with variables resolved
        """
        if not isinstance(text, str):
            return text

        def replace_var(match):
            var_name = match.group(1)
            value = context.get(var_name, match.group(0))
            return str(value)

        # Replace {{var}} patterns
        result = re.sub(r'\{\{(\w+)\}\}', replace_var, text)
        return result

    def _resolve_dict_variables(self, data: dict, context: dict) -> dict:
        """Resolve variables in a dictionary recursively.

        Args:
            data: dict - Dictionary with potential variable placeholders
            context: dict - Context for variable resolution

        Returns:
            dict: Dictionary with variables resolved
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._resolve_variables(value, context)
            elif isinstance(value, dict):
                result[key] = self._resolve_dict_variables(value, context)
            else:
                result[key] = value
        return result

    def _evaluate_condition(self, condition: str, context: dict) -> bool:
        """Evaluate conditional expression.

        Evaluates simple boolean conditions with operators:
        ==, !=, >, <, >=, <=, and, or

        Args:
            condition: str - Condition expression with {{var}} references
            context: dict - Context for variable resolution

        Returns:
            bool: True if condition passes, False otherwise
        """
        # Resolve variables in condition
        resolved = self._resolve_variables(condition, context)

        # Parse and evaluate the condition
        try:
            # Handle simple comparisons
            # Try to find an operator
            operators = ["!=", "==", ">=", "<=", ">", "<", " and ", " or "]

            for op in operators:
                if op in resolved:
                    if op == " or ":
                        parts = resolved.split(" or ")
                        return any(self._evaluate_condition(p.strip(), context) for p in parts)
                    elif op == " and ":
                        parts = resolved.split(" and ")
                        return all(self._evaluate_condition(p.strip(), context) for p in parts)
                    else:
                        left, right = resolved.split(op, 1)
                        left = left.strip()
                        right = right.strip()

                        if op == "==":
                            return left == right
                        elif op == "!=":
                            return left != right
                        elif op == ">":
                            try:
                                return float(left) > float(right)
                            except ValueError:
                                return left > right
                        elif op == "<":
                            try:
                                return float(left) < float(right)
                            except ValueError:
                                return left < right
                        elif op == ">=":
                            try:
                                return float(left) >= float(right)
                            except ValueError:
                                return left >= right
                        elif op == "<=":
                            try:
                                return float(left) <= float(right)
                            except ValueError:
                                return left <= right

            # If no operator found, evaluate as boolean
            return bool(resolved)

        except Exception:
            # If evaluation fails, return False
            return False

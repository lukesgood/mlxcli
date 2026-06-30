"""YAML/JSON workflow parsing and validation."""

import json
from typing import Tuple

import yaml


class WorkflowParser:
    """Parse and validate workflow definitions from YAML/JSON.

    Supports parsing workflow definitions from YAML and JSON formats
    and validates them against the expected workflow schema.
    """

    @staticmethod
    def parse_yaml(yaml_str: str) -> dict:
        """Parse YAML workflow definition.

        Parses a YAML string into a workflow dictionary.

        Args:
            yaml_str: str - YAML workflow definition as string

        Returns:
            dict: Workflow dictionary with structure:
                - version: str - Workflow format version
                - name: str - Workflow name
                - description: str (optional) - Workflow description
                - steps: list[dict] - List of workflow steps
                - final_output: str (optional) - Final output key

        Raises:
            yaml.YAMLError: If YAML parsing fails
            ValueError: If YAML is not valid dictionary format
        """
        try:
            result = yaml.safe_load(yaml_str)
            if not isinstance(result, dict):
                raise ValueError("YAML must represent a dictionary")
            return result
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML: {e}")

    @staticmethod
    def parse_json(json_str: str) -> dict:
        """Parse JSON workflow definition.

        Parses a JSON string into a workflow dictionary.

        Args:
            json_str: str - JSON workflow definition as string

        Returns:
            dict: Workflow dictionary with same structure as YAML parsing

        Raises:
            json.JSONDecodeError: If JSON parsing fails
            ValueError: If JSON is not valid dictionary format
        """
        try:
            result = json.loads(json_str)
            if not isinstance(result, dict):
                raise ValueError("JSON must represent a dictionary")
            return result
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {e}")

    @staticmethod
    def validate_workflow(workflow: dict) -> Tuple[bool, str]:
        """Validate workflow structure.

        Validates that a workflow dictionary has the required structure
        and all steps are properly defined.

        Args:
            workflow: dict - Workflow dictionary to validate

        Returns:
            tuple[bool, str]: (is_valid, error_message)
                - is_valid: bool - True if workflow is valid, False otherwise
                - error_message: str - Error message if invalid, empty string if valid

        Validation checks:
        - Must be a dictionary
        - Must have 'version' key (currently only "1.0" supported)
        - Must have 'name' key
        - Must have 'steps' key with at least one step
        - Each step must have 'id' key
        - Each step must have 'agent' or 'tool' key
        """
        # Check workflow is a dict
        if not isinstance(workflow, dict):
            return False, "Workflow must be a dictionary"

        # Check version exists
        if "version" not in workflow:
            return False, "Workflow must have 'version' field"

        # Check version is supported
        if workflow["version"] not in ("1.0",):
            return False, f"Workflow version '{workflow['version']}' is not supported (only 1.0)"

        # Check name exists
        if "name" not in workflow:
            return False, "Workflow must have 'name' field"

        # Check steps exist
        if "steps" not in workflow:
            return False, "Workflow must have 'steps' field"

        steps = workflow["steps"]
        if not isinstance(steps, list):
            return False, "Workflow 'steps' must be a list"

        if len(steps) == 0:
            return False, "Workflow 'steps' must have at least one step"

        # Validate each step
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                return False, f"Step {i} must be a dictionary"

            if "id" not in step:
                return False, f"Step {i} must have 'id' field"

            # Must have either agent or tool
            if "agent" not in step and "tool" not in step:
                return False, f"Step {step.get('id', i)} must have 'agent' or 'tool' field"

        return True, ""

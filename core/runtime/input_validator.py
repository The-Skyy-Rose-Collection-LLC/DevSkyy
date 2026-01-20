"""
Tool Input Validation & Sanitization
=====================================

Production-grade input validation for tool execution.

Features:
- Schema-based parameter validation
- Length limit enforcement (strings 10K, arrays 1K items)
- Control character blocking
- XSS/SQL injection prevention
- Audit logging of all validations

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
import re
import string
from typing import Any

from security.input_validation import SecurityValidator

logger = logging.getLogger(__name__)

# Logging for audit trail
audit_logger = logging.getLogger("tool_validation_audit")


class ToolInputValidationError(Exception):
    """Tool input validation error."""

    def __init__(self, tool_name: str, reason: str, details: dict[str, Any] | None = None):
        self.tool_name = tool_name
        self.reason = reason
        self.details = details or {}
        super().__init__(f"Tool {tool_name} validation failed: {reason}")


class ToolInputValidator:
    """
    Input validation for tool execution.

    Enforces:
    - Schema validation against tool's input_schema
    - Length limits (strings 10K, arrays 1K items)
    - Control character blocking
    - XSS/SQL injection prevention
    - Audit logging
    """

    # Length limits
    DEFAULT_STRING_LIMIT = 10 * 1024  # 10KB per string
    DEFAULT_ARRAY_LIMIT = 1000  # 1000 items per array
    DEFAULT_OBJECT_LIMIT = 100  # 100 keys per object
    MAX_NESTING_DEPTH = 10  # Max JSON nesting

    # Control character ranges (ASCII 0x00-0x1F except tab/newline/carriage return in strings)
    CONTROL_CHARS_REGEX = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")

    # Printable characters (allow basic alphanumeric + common symbols)
    ALLOWED_SPECIAL_CHARS = set(string.punctuation + string.whitespace)

    def __init__(self):
        self.security_validator = SecurityValidator()
        self.validation_log = []

    def validate(
        self,
        tool_name: str,
        params: dict[str, Any],
        input_schema: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> tuple[bool, list[str]]:
        """
        Validate tool parameters.

        Args:
            tool_name: Name of the tool
            params: Parameters to validate
            input_schema: JSON Schema for parameters (optional)
            request_id: Request ID for audit logging

        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []

        # Log validation attempt
        audit_logger.info(
            "Tool input validation started",
            extra={
                "tool_name": tool_name,
                "request_id": request_id,
                "param_count": len(params),
            },
        )

        try:
            # Check for null/empty params
            if not isinstance(params, dict):
                errors.append("Parameters must be a dictionary")
                self._log_validation_failure(tool_name, errors, request_id)
                return False, errors

            # Validate schema if provided
            if input_schema:
                schema_errors = self._validate_against_schema(params, input_schema)
                errors.extend(schema_errors)

            # Validate and sanitize each parameter
            for param_name, param_value in params.items():
                param_errors = self._validate_parameter(tool_name, param_name, param_value, depth=0)
                errors.extend(param_errors)

            # Log success/failure
            if errors:
                self._log_validation_failure(tool_name, errors, request_id)
                return False, errors
            else:
                audit_logger.info(
                    "Tool input validation succeeded",
                    extra={"tool_name": tool_name, "request_id": request_id},
                )
                return True, []

        except Exception as e:
            error_msg = f"Validation exception: {str(e)}"
            errors.append(error_msg)
            audit_logger.error(
                "Tool input validation error",
                extra={"tool_name": tool_name, "request_id": request_id, "error": str(e)},
            )
            return False, errors

    def _validate_against_schema(self, params: dict[str, Any], schema: dict[str, Any]) -> list[str]:
        """Validate params against JSON Schema."""
        errors = []

        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in params:
                errors.append(f"Required field missing: {field}")

        # Check properties if defined
        properties = schema.get("properties", {})
        for prop_name, prop_schema in properties.items():
            if prop_name in params:
                # Type validation
                expected_type = prop_schema.get("type")
                if expected_type:
                    param_type = type(params[prop_name]).__name__
                    type_map = {
                        "string": str,
                        "integer": int,
                        "number": (int, float),
                        "boolean": bool,
                        "array": list,
                        "object": dict,
                    }
                    expected_py_type = type_map.get(expected_type)
                    if expected_py_type and not isinstance(params[prop_name], expected_py_type):
                        errors.append(
                            f"Field '{prop_name}': expected {expected_type}, got {param_type}"
                        )

                # Length constraints
                if expected_type == "string":
                    min_len = prop_schema.get("minLength", 0)
                    max_len = prop_schema.get("maxLength", self.DEFAULT_STRING_LIMIT)
                    param_len = len(str(params[prop_name]))
                    if param_len < min_len:
                        errors.append(f"Field '{prop_name}': too short (min {min_len})")
                    if param_len > max_len:
                        errors.append(f"Field '{prop_name}': too long (max {max_len})")

                # Array constraints
                if expected_type == "array":
                    min_items = prop_schema.get("minItems", 0)
                    max_items = prop_schema.get("maxItems", self.DEFAULT_ARRAY_LIMIT)
                    param_len = len(params[prop_name])
                    if param_len < min_items:
                        errors.append(f"Field '{prop_name}': too few items (min {min_items})")
                    if param_len > max_items:
                        errors.append(f"Field '{prop_name}': too many items (max {max_items})")

        return errors

    def _validate_parameter(
        self, tool_name: str, param_name: str, param_value: Any, depth: int = 0
    ) -> list[str]:
        """
        Recursively validate a single parameter.

        Args:
            tool_name: Name of the tool
            param_name: Parameter name
            param_value: Parameter value
            depth: Current nesting depth

        Returns:
            List of validation errors
        """
        errors = []

        # Check nesting depth
        if depth > self.MAX_NESTING_DEPTH:
            errors.append(
                f"Parameter '{param_name}': nesting too deep (max {self.MAX_NESTING_DEPTH})"
            )
            return errors

        if isinstance(param_value, str):
            errors.extend(self._validate_string(param_name, param_value))

        elif isinstance(param_value, list | tuple):
            errors.extend(self._validate_array(tool_name, param_name, param_value, depth))

        elif isinstance(param_value, dict):
            errors.extend(self._validate_object(tool_name, param_name, param_value, depth))

        elif param_value is None:
            # None is acceptable
            pass

        elif isinstance(param_value, int | float | bool):
            # Primitives are safe after type checking
            pass

        else:
            errors.append(f"Parameter '{param_name}': unsupported type {type(param_value)}")

        return errors

    def _validate_string(self, param_name: str, value: str) -> list[str]:
        """Validate a string parameter."""
        errors = []

        # Check length
        if len(value) > self.DEFAULT_STRING_LIMIT:
            errors.append(
                f"Parameter '{param_name}': string too long (max {self.DEFAULT_STRING_LIMIT} bytes)"
            )

        # Check for control characters
        if self.CONTROL_CHARS_REGEX.search(value):
            errors.append(f"Parameter '{param_name}': contains invalid control characters")

        # Check for SQL injection
        if self.security_validator.detect_sql_injection(value):
            errors.append(f"Parameter '{param_name}': potential SQL injection detected")

        # Check for XSS
        if self.security_validator.detect_xss(value):
            errors.append(f"Parameter '{param_name}': potential XSS detected")

        return errors

    def _validate_array(
        self, tool_name: str, param_name: str, value: list | tuple, depth: int
    ) -> list[str]:
        """Validate an array parameter."""
        errors = []

        # Check array length
        if len(value) > self.DEFAULT_ARRAY_LIMIT:
            errors.append(
                f"Parameter '{param_name}': array too large (max {self.DEFAULT_ARRAY_LIMIT} items)"
            )
            # Still validate first N items
            value = value[: self.DEFAULT_ARRAY_LIMIT]

        # Validate each item
        for idx, item in enumerate(value):
            item_errors = self._validate_parameter(
                tool_name, f"{param_name}[{idx}]", item, depth + 1
            )
            errors.extend(item_errors)

        return errors

    def _validate_object(
        self, tool_name: str, param_name: str, value: dict, depth: int
    ) -> list[str]:
        """Validate an object parameter."""
        errors = []

        # Check object size
        if len(value) > self.DEFAULT_OBJECT_LIMIT:
            errors.append(
                f"Parameter '{param_name}': object too large (max {self.DEFAULT_OBJECT_LIMIT} keys)"
            )
            # Validate only first N keys
            keys = list(value.keys())[: self.DEFAULT_OBJECT_LIMIT]
            value = {k: value[k] for k in keys}

        # Validate each key-value pair
        for key, val in value.items():
            # Validate key
            if not isinstance(key, str):
                errors.append(
                    f"Parameter '{param_name}': object key must be string, got {type(key)}"
                )
                continue

            if self.CONTROL_CHARS_REGEX.search(key):
                errors.append(f"Parameter '{param_name}': object key contains invalid characters")

            # Validate value
            val_errors = self._validate_parameter(tool_name, f"{param_name}.{key}", val, depth + 1)
            errors.extend(val_errors)

        return errors

    def _log_validation_failure(
        self, tool_name: str, errors: list[str], request_id: str | None
    ) -> None:
        """Log validation failure for audit trail."""
        audit_logger.warning(
            "Tool input validation failed",
            extra={
                "tool_name": tool_name,
                "request_id": request_id,
                "error_count": len(errors),
                "errors": errors[:5],  # Log first 5 errors
            },
        )


# Global instance
tool_input_validator = ToolInputValidator()

"""
Test Input Validation for Tools
================================

Tests for tool input validation including:
- Length limit enforcement
- Control character blocking
- XSS/SQL injection prevention
- Audit logging
"""

import pytest

from core.runtime.input_validator import ToolInputValidator


@pytest.fixture
def validator():
    """Create validator instance for tests."""
    return ToolInputValidator()


class TestStringValidation:
    """Test string parameter validation."""

    def test_valid_string(self, validator):
        """Valid string should pass validation."""
        is_valid, errors = validator.validate("test_tool", {"name": "test"}, request_id="req-1")
        assert is_valid
        assert errors == []

    def test_string_too_long(self, validator):
        """String exceeding 10KB should fail."""
        long_string = "a" * (10 * 1024 + 1)
        is_valid, errors = validator.validate(
            "test_tool", {"data": long_string}, request_id="req-1"
        )
        assert not is_valid
        assert any("too long" in error for error in errors)

    def test_control_characters_blocked(self, validator):
        """Control characters should be blocked."""
        invalid_string = "test\x00data"  # Null byte
        is_valid, errors = validator.validate(
            "test_tool", {"data": invalid_string}, request_id="req-1"
        )
        assert not is_valid
        assert any("control character" in error.lower() for error in errors)

    def test_xss_detection(self, validator):
        """XSS payload should be detected."""
        xss_payload = "<script>alert('xss')</script>"
        is_valid, errors = validator.validate(
            "test_tool", {"html": xss_payload}, request_id="req-1"
        )
        assert not is_valid
        assert any("xss" in error.lower() for error in errors)

    def test_sql_injection_detection(self, validator):
        """SQL injection payload should be detected."""
        sql_payload = "' OR '1'='1"
        is_valid, errors = validator.validate(
            "test_tool", {"query": sql_payload}, request_id="req-1"
        )
        assert not is_valid
        assert any("sql" in error.lower() for error in errors)


class TestArrayValidation:
    """Test array parameter validation."""

    def test_valid_array(self, validator):
        """Valid array should pass validation."""
        is_valid, errors = validator.validate("test_tool", {"items": [1, 2, 3]}, request_id="req-1")
        assert is_valid
        assert errors == []

    def test_array_too_large(self, validator):
        """Array exceeding 1000 items should fail."""
        large_array = list(range(1001))
        is_valid, errors = validator.validate(
            "test_tool", {"items": large_array}, request_id="req-1"
        )
        assert not is_valid
        assert any("too large" in error.lower() for error in errors)

    def test_nested_array_validation(self, validator):
        """Nested arrays should be validated."""
        nested = [[1, 2], [3, 4]]
        is_valid, errors = validator.validate("test_tool", {"data": nested}, request_id="req-1")
        assert is_valid

    def test_array_with_invalid_string(self, validator):
        """Array containing invalid string should fail."""
        array_with_xss = ["normal", "<script>alert()</script>"]
        is_valid, errors = validator.validate(
            "test_tool", {"items": array_with_xss}, request_id="req-1"
        )
        assert not is_valid
        assert any("xss" in error.lower() for error in errors)


class TestObjectValidation:
    """Test object parameter validation."""

    def test_valid_object(self, validator):
        """Valid object should pass validation."""
        obj = {"key": "value", "count": 42}
        is_valid, errors = validator.validate("test_tool", {"data": obj}, request_id="req-1")
        assert is_valid

    def test_object_with_too_many_keys(self, validator):
        """Object exceeding 100 keys should fail."""
        large_obj = {f"key_{i}": i for i in range(101)}
        is_valid, errors = validator.validate("test_tool", {"data": large_obj}, request_id="req-1")
        assert not is_valid
        assert any("too large" in error.lower() for error in errors)

    def test_nested_object_validation(self, validator):
        """Nested objects should be validated."""
        nested = {"outer": {"inner": {"deep": "value"}}}
        is_valid, errors = validator.validate("test_tool", {"data": nested}, request_id="req-1")
        assert is_valid

    def test_object_key_with_control_chars(self, validator):
        """Object key with control chars should fail."""
        invalid_obj = {"key\x00bad": "value"}
        is_valid, errors = validator.validate(
            "test_tool", {"data": invalid_obj}, request_id="req-1"
        )
        assert not is_valid


class TestSchemaValidation:
    """Test JSON Schema-based validation."""

    def test_required_field_missing(self, validator):
        """Missing required field should fail."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name"],
        }
        params = {"age": 30}  # Missing 'name'
        is_valid, errors = validator.validate(
            "test_tool", params, input_schema=schema, request_id="req-1"
        )
        assert not is_valid
        assert any("required" in error.lower() for error in errors)

    def test_type_mismatch(self, validator):
        """Type mismatch should fail."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": [],
        }
        params = {"name": "John", "age": "not_a_number"}  # Wrong type for age
        is_valid, errors = validator.validate(
            "test_tool", params, input_schema=schema, request_id="req-1"
        )
        assert not is_valid

    def test_string_length_from_schema(self, validator):
        """Schema-defined length limits should be enforced."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 2, "maxLength": 10},
            },
            "required": [],
        }
        # Too long
        params = {"name": "a" * 11}
        is_valid, errors = validator.validate(
            "test_tool", params, input_schema=schema, request_id="req-1"
        )
        assert not is_valid


class TestNestingDepth:
    """Test maximum nesting depth enforcement."""

    def test_shallow_nesting_ok(self, validator):
        """Shallow nesting should pass."""
        data = {"a": {"b": {"c": "value"}}}  # Depth 3
        is_valid, errors = validator.validate("test_tool", {"data": data}, request_id="req-1")
        assert is_valid

    def test_deep_nesting_fails(self, validator):
        """Nesting deeper than 10 should fail."""
        # Create deeply nested structure (depth > 10)
        data = {"a": "val"}
        for _ in range(11):
            data = {"nested": data}

        is_valid, errors = validator.validate("test_tool", {"data": data}, request_id="req-1")
        assert not is_valid
        assert any("nesting" in error.lower() for error in errors)


class TestPrimitiveTypes:
    """Test primitive type validation."""

    def test_valid_primitives(self, validator):
        """Valid primitives should pass."""
        params = {
            "string": "test",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "null": None,
        }
        is_valid, errors = validator.validate("test_tool", params, request_id="req-1")
        assert is_valid

    def test_null_is_allowed(self, validator):
        """None/null values should be allowed."""
        is_valid, errors = validator.validate("test_tool", {"value": None}, request_id="req-1")
        assert is_valid


class TestMultipleErrors:
    """Test validation with multiple errors."""

    def test_multiple_validation_errors(self, validator):
        """Multiple errors should be collected."""
        params = {
            "field1": "<script>alert()</script>",  # XSS
            "field2": "' OR '1'='1'",  # SQL injection
            "field3": "a" * (10 * 1024 + 1),  # Too long
        }
        is_valid, errors = validator.validate("test_tool", params, request_id="req-1")
        assert not is_valid
        assert len(errors) >= 3  # At least 3 errors


class TestValidationLogging:
    """Test that validations are logged."""

    def test_validation_creates_audit_log(self, validator):
        """Validation should create audit log entries."""
        is_valid, errors = validator.validate(
            "test_tool",
            {"name": "test"},
            request_id="req-123",
        )
        assert is_valid
        # Audit logging happens internally, just verify it doesn't crash


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

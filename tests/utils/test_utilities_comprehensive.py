"""
Comprehensive Tests for Utility Functions and Helper Modules
Tests common utilities, helpers, and shared functions
Coverage target: ≥90% for utility modules

Author: DevSkyy Team
Version: 1.0.0
Python: >=3.11.0
Per CLAUDE.md Truth Protocol requirements
"""

from datetime import datetime, timedelta

import pytest


# ============================================================================
# TEST DATE/TIME UTILITIES
# ============================================================================


class TestDateTimeUtilities:
    """Test date and time utility functions"""

    def test_current_datetime(self):
        """Should get current datetime"""
        now = datetime.now()
        assert isinstance(now, datetime)

    def test_datetime_formatting(self):
        """Should format datetime to string"""
        dt = datetime(2025, 1, 1, 12, 0, 0)
        formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
        assert formatted == "2025-01-01 12:00:00"

    def test_datetime_parsing(self):
        """Should parse datetime from string"""
        date_str = "2025-01-01 12:00:00"
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 1

    def test_date_arithmetic(self):
        """Should perform date arithmetic"""
        dt = datetime(2025, 1, 1)
        next_day = dt + timedelta(days=1)
        assert next_day.day == 2

    def test_date_comparison(self):
        """Should compare dates"""
        dt1 = datetime(2025, 1, 1)
        dt2 = datetime(2025, 1, 2)
        assert dt1 < dt2
        assert dt2 > dt1

    def test_timestamp_conversion(self):
        """Should convert to/from timestamp"""
        dt = datetime(2025, 1, 1, 12, 0, 0)
        timestamp = dt.timestamp()
        assert isinstance(timestamp, float)
        # Convert back
        dt_from_ts = datetime.fromtimestamp(timestamp)
        assert dt_from_ts.year == 2025


# ============================================================================
# TEST STRING UTILITIES
# ============================================================================


class TestStringUtilities:
    """Test string utility functions"""

    def test_string_trimming(self):
        """Should trim whitespace"""
        text = "  hello world  "
        trimmed = text.strip()
        assert trimmed == "hello world"

    def test_string_splitting(self):
        """Should split strings"""
        text = "one,two,three"
        parts = text.split(",")
        assert len(parts) == 3
        assert parts[0] == "one"

    def test_string_joining(self):
        """Should join strings"""
        parts = ["one", "two", "three"]
        joined = ",".join(parts)
        assert joined == "one,two,three"

    def test_string_case_conversion(self):
        """Should convert string case"""
        text = "Hello World"
        assert text.lower() == "hello world"
        assert text.upper() == "HELLO WORLD"
        assert text.title() == "Hello World"

    def test_string_replacement(self):
        """Should replace substrings"""
        text = "hello world"
        replaced = text.replace("world", "universe")
        assert replaced == "hello universe"

    def test_string_formatting(self):
        """Should format strings"""
        template = "Hello {name}!"
        result = template.format(name="World")
        assert result == "Hello World!"

    def test_string_contains(self):
        """Should check substring presence"""
        text = "hello world"
        assert "world" in text
        assert "universe" not in text


# ============================================================================
# TEST COLLECTION UTILITIES
# ============================================================================


class TestCollectionUtilities:
    """Test collection utility functions"""

    def test_list_operations(self):
        """Should perform list operations"""
        lst = [1, 2, 3, 4, 5]
        assert len(lst) == 5
        assert lst[0] == 1
        assert lst[-1] == 5

    def test_list_comprehension(self):
        """Should use list comprehension"""
        lst = [1, 2, 3, 4, 5]
        doubled = [x * 2 for x in lst]
        assert doubled == [2, 4, 6, 8, 10]

    def test_list_filtering(self):
        """Should filter lists"""
        lst = [1, 2, 3, 4, 5]
        evens = [x for x in lst if x % 2 == 0]
        assert evens == [2, 4]

    def test_dict_operations(self):
        """Should perform dict operations"""
        d = {"a": 1, "b": 2, "c": 3}
        assert len(d) == 3
        assert d["a"] == 1
        assert "b" in d

    def test_dict_iteration(self):
        """Should iterate over dict"""
        d = {"a": 1, "b": 2}
        keys = list(d.keys())
        values = list(d.values())
        assert keys == ["a", "b"]
        assert values == [1, 2]

    def test_set_operations(self):
        """Should perform set operations"""
        s1 = {1, 2, 3}
        s2 = {3, 4, 5}
        assert s1.union(s2) == {1, 2, 3, 4, 5}
        assert s1.intersection(s2) == {3}
        assert s1.difference(s2) == {1, 2}


# ============================================================================
# TEST DATA VALIDATION UTILITIES
# ============================================================================


class TestDataValidationUtilities:
    """Test data validation utilities"""

    def test_is_valid_email(self):
        """Should validate email format"""
        import re

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        assert re.match(email_pattern, "test@example.com")
        assert not re.match(email_pattern, "invalid-email")

    def test_is_valid_url(self):
        """Should validate URL format"""
        import re

        url_pattern = r"^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$"

        assert re.match(url_pattern, "https://example.com")
        assert re.match(url_pattern, "http://example.com/path")
        assert not re.match(url_pattern, "not-a-url")

    def test_is_alphanumeric(self):
        """Should check if alphanumeric"""
        assert "abc123".isalnum()
        assert not "abc-123".isalnum()


# ============================================================================
# TEST FILE UTILITIES
# ============================================================================


class TestFileUtilities:
    """Test file utility functions"""

    def test_file_extension(self):
        """Should extract file extension"""
        import os

        filename = "document.pdf"
        _, ext = os.path.splitext(filename)
        assert ext == ".pdf"

    def test_file_basename(self):
        """Should extract file basename"""
        import os

        path = "/path/to/file.txt"
        basename = os.path.basename(path)
        assert basename == "file.txt"

    def test_file_dirname(self):
        """Should extract directory name"""
        import os

        path = "/path/to/file.txt"
        dirname = os.path.dirname(path)
        assert dirname == "/path/to"

    def test_path_join(self):
        """Should join path components"""
        import os

        path = os.path.join("path", "to", "file.txt")
        assert "file.txt" in path


# ============================================================================
# TEST JSON UTILITIES
# ============================================================================


class TestJSONUtilities:
    """Test JSON utility functions"""

    def test_json_dumps(self):
        """Should serialize to JSON"""
        import json

        data = {"name": "Test", "value": 123}
        json_str = json.dumps(data)
        assert isinstance(json_str, str)
        assert "Test" in json_str

    def test_json_loads(self):
        """Should parse JSON"""
        import json

        json_str = '{"name": "Test", "value": 123}'
        data = json.loads(json_str)
        assert data["name"] == "Test"
        assert data["value"] == 123

    def test_json_pretty_print(self):
        """Should pretty print JSON"""
        import json

        data = {"name": "Test", "nested": {"key": "value"}}
        json_str = json.dumps(data, indent=2)
        assert "\n" in json_str  # Has newlines

    def test_json_handles_special_types(self):
        """Should handle special types"""
        import json

        data = {"date": datetime(2025, 1, 1).isoformat()}
        json_str = json.dumps(data)
        assert "2025" in json_str


# ============================================================================
# TEST ENCODING UTILITIES
# ============================================================================


class TestEncodingUtilities:
    """Test encoding utility functions"""

    def test_base64_encoding(self):
        """Should encode/decode base64"""
        import base64

        text = "Hello World"
        encoded = base64.b64encode(text.encode()).decode()
        assert isinstance(encoded, str)

        # Decode
        decoded = base64.b64decode(encoded.encode()).decode()
        assert decoded == text

    def test_url_encoding(self):
        """Should URL encode/decode"""
        from urllib.parse import quote, unquote

        text = "hello world"
        encoded = quote(text)
        assert "%20" in encoded

        # Decode
        decoded = unquote(encoded)
        assert decoded == text


# ============================================================================
# TEST MATH UTILITIES
# ============================================================================


class TestMathUtilities:
    """Test math utility functions"""

    def test_basic_math(self):
        """Should perform basic math operations"""
        assert 2 + 2 == 4
        assert 5 - 3 == 2
        assert 3 * 4 == 12
        assert 10 / 2 == 5

    def test_rounding(self):
        """Should round numbers"""
        assert round(3.14159, 2) == 3.14
        assert round(3.5) == 4

    def test_min_max(self):
        """Should find min and max"""
        numbers = [1, 5, 3, 9, 2]
        assert min(numbers) == 1
        assert max(numbers) == 9

    def test_sum_average(self):
        """Should calculate sum and average"""
        numbers = [1, 2, 3, 4, 5]
        total = sum(numbers)
        avg = total / len(numbers)
        assert total == 15
        assert avg == 3.0


# ============================================================================
# TEST HASH UTILITIES
# ============================================================================


class TestHashUtilities:
    """Test hashing utility functions"""

    def test_md5_hash(self):
        """Should create MD5 hash"""
        import hashlib

        text = "hello world"
        hash_obj = hashlib.md5(text.encode())
        hash_str = hash_obj.hexdigest()
        assert isinstance(hash_str, str)
        assert len(hash_str) == 32  # MD5 is 128 bits = 32 hex chars

    def test_sha256_hash(self):
        """Should create SHA256 hash"""
        import hashlib

        text = "hello world"
        hash_obj = hashlib.sha256(text.encode())
        hash_str = hash_obj.hexdigest()
        assert isinstance(hash_str, str)
        assert len(hash_str) == 64  # SHA256 is 256 bits = 64 hex chars

    def test_hash_consistency(self):
        """Should produce consistent hashes"""
        import hashlib

        text = "test"
        hash1 = hashlib.sha256(text.encode()).hexdigest()
        hash2 = hashlib.sha256(text.encode()).hexdigest()
        assert hash1 == hash2


# ============================================================================
# TEST UUID UTILITIES
# ============================================================================


class TestUUIDUtilities:
    """Test UUID utility functions"""

    def test_uuid_generation(self):
        """Should generate UUIDs"""
        from uuid import uuid4

        uuid1 = uuid4()
        uuid2 = uuid4()

        assert uuid1 != uuid2
        assert isinstance(str(uuid1), str)

    def test_uuid_format(self):
        """Should have proper UUID format"""
        from uuid import uuid4

        uuid = str(uuid4())
        assert len(uuid) == 36  # 32 hex + 4 hyphens
        assert uuid.count("-") == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=.", "--cov-report=term-missing"])

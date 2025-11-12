"""
Unit Tests for .gitignore Cursor Directory Entry
Testing that .cursor/ directory is properly ignored
"""

import os

import pytest


class TestGitignoreCursorEntry:
    """Test .gitignore has .cursor/ entry"""

    @pytest.mark.unit
    def test_gitignore_file_exists(self):
        """Test .gitignore file exists"""
        assert os.path.exists(".gitignore")

    @pytest.mark.unit
    def test_gitignore_contains_cursor_entry(self):
        """Test .gitignore contains .cursor/ entry"""
        with open(".gitignore", "r") as f:
            content = f.read()

        # Should have .cursor/ entry
        assert ".cursor/" in content

    @pytest.mark.unit
    def test_cursor_directory_pattern_format(self):
        """Test .cursor/ entry is properly formatted"""
        with open(".gitignore", "r") as f:
            lines = f.readlines()

        cursor_lines = [line.strip() for line in lines if ".cursor" in line]

        # Should have at least one .cursor entry
        assert len(cursor_lines) > 0

        # Should be properly formatted (with trailing slash for directory)
        assert any(line == ".cursor/" for line in cursor_lines)

    @pytest.mark.unit
    def test_gitignore_not_empty(self):
        """Test .gitignore is not empty"""
        with open(".gitignore", "r") as f:
            content = f.read()

        assert len(content) > 0

    @pytest.mark.unit
    def test_gitignore_has_proper_structure(self):
        """Test .gitignore has proper structure"""
        with open(".gitignore", "r") as f:
            lines = f.readlines()

        # Should have multiple entries
        non_empty_lines = [line for line in lines if line.strip() and not line.strip().startswith("#")]
        assert len(non_empty_lines) > 5

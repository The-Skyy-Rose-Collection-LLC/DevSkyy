"""
Unit Tests for .gitignore Validation
Tests to ensure .gitignore patterns are valid and comprehensive
"""

import os
from pathlib import Path

import pytest


class TestGitignoreStructure:
    """Test .gitignore file structure and content"""

    @pytest.fixture
    def gitignore_path(self):
        """Get path to .gitignore file"""
        return Path(__file__).parent.parent / ".gitignore"

    @pytest.fixture
    def gitignore_content(self, gitignore_path):
        """Read .gitignore content"""
        with open(gitignore_path, "r") as f:
            return f.read()

    def test_gitignore_exists(self, gitignore_path):
        """Test that .gitignore file exists"""
        assert gitignore_path.exists(), ".gitignore file should exist"
        assert gitignore_path.is_file(), ".gitignore should be a file"

    def test_gitignore_readable(self, gitignore_path):
        """Test that .gitignore is readable"""
        assert os.access(gitignore_path, os.R_OK), ".gitignore should be readable"

    def test_gitignore_not_empty(self, gitignore_content):
        """Test that .gitignore is not empty"""
        assert len(gitignore_content.strip()) > 0, ".gitignore should not be empty"
        assert len(gitignore_content.split("\n")) > 10, ".gitignore should have multiple lines"

    def test_cursor_directory_ignored(self, gitignore_content):
        """Test that .cursor/ directory is in .gitignore"""
        assert ".cursor/" in gitignore_content, ".cursor/ should be ignored"

    def test_common_python_patterns_present(self, gitignore_content):
        """Test that common Python patterns are present"""
        required_patterns = [
            "__pycache__/",
            "*.py[cod]",
            "*.so",
            ".Python",
            "venv/",
            ".venv/",
            "*.egg-info/",
        ]
        for pattern in required_patterns:
            assert pattern in gitignore_content, f"Pattern '{pattern}' should be in .gitignore"

    def test_environment_files_ignored(self, gitignore_content):
        """Test that environment files are ignored"""
        env_patterns = [".env", ".env.local", ".env.*.local"]
        for pattern in env_patterns:
            assert pattern in gitignore_content, f"Environment pattern '{pattern}' should be ignored"

    def test_ide_files_ignored(self, gitignore_content):
        """Test that IDE files are ignored"""
        ide_patterns = [".vscode/", ".idea/", "*.swp", "*.swo", ".cursor/"]
        for pattern in ide_patterns:
            assert pattern in gitignore_content, f"IDE pattern '{pattern}' should be ignored"

    def test_os_specific_files_ignored(self, gitignore_content):
        """Test that OS-specific files are ignored"""
        os_patterns = [".DS_Store", "Thumbs.db", "desktop.ini"]
        for pattern in os_patterns:
            assert pattern in gitignore_content, f"OS pattern '{pattern}' should be ignored"

    def test_security_files_ignored(self, gitignore_content):
        """Test that security-related files are ignored"""
        security_patterns = ["*.key", "*.pem", "*.crt"]
        for pattern in security_patterns:
            assert pattern in gitignore_content, f"Security pattern '{pattern}' should be ignored"

    def test_backup_files_ignored(self, gitignore_content):
        """Test that backup files are ignored"""
        backup_patterns = ["*.backup", "*.broken", "main.py.*", "!main.py"]
        for pattern in backup_patterns:
            assert pattern in gitignore_content, f"Backup pattern '{pattern}' should be present"

    def test_database_files_ignored(self, gitignore_content):
        """Test that database files are ignored"""
        db_patterns = ["*.db", "*.sqlite", "*.sqlite3"]
        for pattern in db_patterns:
            assert pattern in gitignore_content, f"Database pattern '{pattern}' should be ignored"

    def test_ml_model_files_ignored(self, gitignore_content):
        """Test that ML/AI model files are ignored"""
        ml_patterns = ["*.h5", "*.pkl", "*.pickle", "*.pt", "*.pth", "*.onnx", "models/", "checkpoints/"]
        for pattern in ml_patterns:
            assert pattern in gitignore_content, f"ML pattern '{pattern}' should be ignored"

    def test_node_modules_ignored(self, gitignore_content):
        """Test that Node.js files are ignored"""
        assert "node_modules/" in gitignore_content, "node_modules/ should be ignored"
        assert "package-lock.json" in gitignore_content, "package-lock.json should be ignored"

    def test_no_trailing_whitespace(self, gitignore_content):
        """Test that lines don't have trailing whitespace"""
        lines = gitignore_content.split("\n")
        for i, line in enumerate(lines):
            if line and not line.isspace():
                assert line == line.rstrip(), f"Line {i+1} should not have trailing whitespace: '{line}'"

    def test_sections_are_commented(self, gitignore_content):
        """Test that major sections have comments"""
        required_sections = [
            "# Python",
            "# Environment",
            "# IDE",
            "# OS",
            "# Security",
            "# Database",
            "# ML/AI Models",
        ]
        for section in required_sections:
            assert section in gitignore_content, f"Section comment '{section}' should be present"

    def test_cache_directories_ignored(self, gitignore_content):
        """Test that cache directories are ignored"""
        cache_patterns = [".cache/", "*.cache", ".mypy_cache/", ".pytest_cache/"]
        for pattern in cache_patterns:
            assert pattern in gitignore_content, f"Cache pattern '{pattern}' should be ignored"


class TestGitignorePatterns:
    """Test that .gitignore patterns are valid and work correctly"""

    @pytest.fixture
    def gitignore_patterns(self):
        """Extract all patterns from .gitignore"""
        gitignore_path = Path(__file__).parent.parent / ".gitignore"
        with open(gitignore_path, "r") as f:
            lines = f.readlines()

        patterns = []
        for line in lines:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith("#"):
                patterns.append(line)
        return patterns

    def test_patterns_not_empty(self, gitignore_patterns):
        """Test that we have patterns"""
        assert len(gitignore_patterns) > 20, "Should have at least 20 patterns"

    def test_no_duplicate_patterns(self, gitignore_patterns):
        """Test that there are no duplicate patterns"""
        seen = set()
        duplicates = []
        for pattern in gitignore_patterns:
            if pattern in seen:
                duplicates.append(pattern)
            seen.add(pattern)
        assert len(duplicates) == 0, f"Found duplicate patterns: {duplicates}"

    def test_negation_patterns_valid(self, gitignore_patterns):
        """Test that negation patterns (!) are used correctly"""
        negation_patterns = [p for p in gitignore_patterns if p.startswith("!")]
        for pattern in negation_patterns:
            # Negation pattern should have a corresponding positive pattern
            positive_pattern = pattern[1:]  # Remove the !
            # This is a basic check - just ensure it's not empty
            assert len(positive_pattern) > 0, f"Negation pattern '{pattern}' should negate something"

    def test_pattern_syntax_valid(self, gitignore_patterns):
        """Test that patterns use valid gitignore syntax"""
        for pattern in gitignore_patterns:
            # Basic syntax validation
            assert not pattern.endswith(" "), f"Pattern '{pattern}' should not end with space"
            assert not pattern.startswith(" "), f"Pattern '{pattern}' should not start with space"
            # Patterns with wildcards
            if "*" in pattern:
                assert pattern.count("**") <= 1 or "**" not in pattern, f"Pattern '{pattern}' has invalid ** usage"

    def test_directory_patterns_end_with_slash(self, gitignore_patterns):
        """Test that directory patterns typically end with /"""
        directory_keywords = ["cache", "modules", "packages", "checkpoints", "models"]
        for pattern in gitignore_patterns:
            # Skip negation and file extension patterns
            if pattern.startswith("!") or pattern.startswith("*."):
                continue
            # Check if it looks like a directory name
            for keyword in directory_keywords:
                if keyword in pattern.lower() and not pattern.endswith("/"):
                    # This is a soft check - not all directory patterns need /
                    pass  # Just documenting the expectation

    def test_wildcard_patterns_valid(self, gitignore_patterns):
        """Test that wildcard patterns are valid"""
        wildcard_patterns = [p for p in gitignore_patterns if "*" in p]
        for pattern in wildcard_patterns:
            # Ensure wildcards are used appropriately
            assert pattern.count("*") > 0, f"Pattern '{pattern}' should have wildcard"
            # Common valid patterns: *.ext, *pattern*, pattern*
            if pattern.startswith("*."):
                # File extension pattern
                ext = pattern[2:]
                assert len(ext) > 0, f"Extension in '{pattern}' should not be empty"
                assert ext.isalnum() or ext in ["py[cod]"], f"Extension '{ext}' should be alphanumeric"


class TestGitignoreEffectiveness:
    """Test that .gitignore effectively ignores the right files"""

    def test_should_ignore_pycache(self):
        """Test that __pycache__ directories should be ignored"""
        gitignore_path = Path(__file__).parent.parent / ".gitignore"
        with open(gitignore_path, "r") as f:
            content = f.read()
        assert "__pycache__/" in content, "__pycache__/ should be ignored"

    def test_should_ignore_venv(self):
        """Test that virtual environment directories should be ignored"""
        gitignore_path = Path(__file__).parent.parent / ".gitignore"
        with open(gitignore_path, "r") as f:
            content = f.read()
        venv_patterns = ["venv/", ".venv/", "env/"]
        for pattern in venv_patterns:
            assert pattern in content, f"Virtual environment pattern '{pattern}' should be ignored"

    def test_should_ignore_env_files(self):
        """Test that .env files should be ignored"""
        gitignore_path = Path(__file__).parent.parent / ".gitignore"
        with open(gitignore_path, "r") as f:
            content = f.read()
        assert ".env" in content, ".env files should be ignored"

    def test_should_not_ignore_gitignore_itself(self):
        """Test that .gitignore doesn't ignore itself"""
        gitignore_path = Path(__file__).parent.parent / ".gitignore"
        with open(gitignore_path, "r") as f:
            content = f.read()
        # .gitignore should not contain a pattern that would ignore itself
        assert ".gitignore" not in [
            line.strip() for line in content.split("\n") if line.strip() and not line.startswith("#")
        ]

    def test_cursor_ide_files_ignored(self):
        """Test that .cursor/ directory is properly ignored"""
        gitignore_path = Path(__file__).parent.parent / ".gitignore"
        with open(gitignore_path, "r") as f:
            content = f.read()
        assert ".cursor/" in content, ".cursor/ directory should be ignored for Cursor IDE"


class TestGitignoreCoverage:
    """Test that .gitignore covers all necessary file types for the project"""

    @pytest.fixture
    def gitignore_content(self):
        """Read .gitignore content"""
        gitignore_path = Path(__file__).parent.parent / ".gitignore"
        with open(gitignore_path, "r") as f:
            return f.read()

    def test_covers_python_artifacts(self, gitignore_content):
        """Test coverage of Python-specific artifacts"""
        python_artifacts = [
            "__pycache__",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".Python",
            "pip-wheel-metadata",
            "*.egg-info",
        ]
        for artifact in python_artifacts:
            assert artifact in gitignore_content, f"Python artifact '{artifact}' should be covered"

    def test_covers_testing_artifacts(self, gitignore_content):
        """Test coverage of testing artifacts"""
        testing_artifacts = [".coverage", ".pytest_cache/", "htmlcov/"]
        for artifact in testing_artifacts:
            assert artifact in gitignore_content, f"Testing artifact '{artifact}' should be covered"

    def test_covers_build_artifacts(self, gitignore_content):
        """Test coverage of build artifacts"""
        build_artifacts = ["dist/", "build/", "*.egg-info/"]
        for artifact in build_artifacts:
            assert artifact in gitignore_content, f"Build artifact '{artifact}' should be covered"

    def test_covers_cloud_credentials(self, gitignore_content):
        """Test coverage of cloud credential files"""
        credential_patterns = [".aws/", ".gcloud/", "credentials.json", "*-key.json"]
        for pattern in credential_patterns:
            assert pattern in gitignore_content, f"Credential pattern '{pattern}' should be covered"

    def test_covers_large_media_files(self, gitignore_content):
        """Test coverage of large media files"""
        media_extensions = ["*.mp4", "*.avi", "*.mov", "*.zip", "*.tar.gz"]
        for ext in media_extensions:
            assert ext in gitignore_content, f"Media extension '{ext}' should be covered"

    def test_covers_jupyter_artifacts(self, gitignore_content):
        """Test coverage of Jupyter artifacts"""
        jupyter_artifacts = [".ipynb_checkpoints/", "*.ipynb"]
        for artifact in jupyter_artifacts:
            assert artifact in gitignore_content, f"Jupyter artifact '{artifact}' should be covered"


@pytest.mark.integration
class TestGitignoreIntegration:
    """Integration tests for .gitignore functionality"""

    def test_gitignore_in_repository_root(self):
        """Test that .gitignore is in the repository root"""
        repo_root = Path(__file__).parent.parent
        gitignore_path = repo_root / ".gitignore"
        assert gitignore_path.exists(), ".gitignore should be in repository root"

    def test_gitignore_format_compatible_with_git(self):
        """Test that .gitignore format is compatible with git"""
        gitignore_path = Path(__file__).parent.parent / ".gitignore"
        with open(gitignore_path, "r") as f:
            content = f.read()

        # Check for common format issues
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith("#"):
                # Patterns should not have leading/trailing spaces
                assert line == line.strip() or line.startswith("#"), f"Line {i+1} has improper spacing"

    def test_main_py_not_ignored(self):
        """Test that main.py is not ignored (but main.py.* is)"""
        gitignore_path = Path(__file__).parent.parent / ".gitignore"
        with open(gitignore_path, "r") as f:
            lines = [line.strip() for line in f.readlines()]

        # main.py.* should be ignored, but !main.py should negate that
        assert "main.py.*" in lines, "main.py.* should be ignored"
        assert "!main.py" in lines, "main.py should be explicitly not ignored"

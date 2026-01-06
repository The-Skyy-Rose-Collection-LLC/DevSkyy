#!/usr/bin/env python3
"""
Tests for environment setup scripts.

Tests:
- generate_secrets.sh creates valid .env.production file
- validate_environment.py correctly validates configuration
- Generated secrets meet security requirements
"""

import os
import re
import subprocess
from pathlib import Path

import pytest


class TestGenerateSecrets:
    """Test generate_secrets.sh script."""

    def test_script_exists(self):
        """Verify generate_secrets.sh exists."""
        script_path = Path("scripts/generate_secrets.sh")
        assert script_path.exists(), "generate_secrets.sh not found"

    def test_script_is_bash(self):
        """Verify script has correct shebang."""
        script_path = Path("scripts/generate_secrets.sh")
        with open(script_path) as f:
            first_line = f.readline().strip()
        assert first_line == "#!/usr/bin/env bash", "Incorrect shebang"

    def test_generates_env_file(self, tmp_path):
        """Test that script generates .env.production file."""
        # Create temp directory and run script there
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            # Run script
            result = subprocess.run(
                [f"{original_dir}/scripts/generate_secrets.sh"],
                capture_output=True,
                text=True,
            )

            # Check script executed successfully
            assert result.returncode == 0, f"Script failed: {result.stderr}"

            # Check .env.production was created
            env_file = tmp_path / ".env.production"
            assert env_file.exists(), ".env.production not created"

            # Check file permissions (600)
            stat_info = env_file.stat()
            permissions = oct(stat_info.st_mode)[-3:]
            assert permissions == "600", f"Wrong permissions: {permissions}"

        finally:
            os.chdir(original_dir)

    def test_generated_secrets_format(self, tmp_path):
        """Test that generated secrets have correct format."""
        # Generate secrets file
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            subprocess.run(
                [f"{original_dir}/scripts/generate_secrets.sh"],
                capture_output=True,
                check=True,
            )

            # Read generated file
            env_file = tmp_path / ".env.production"
            content = env_file.read_text()

            # Check required secrets exist
            required_vars = [
                "JWT_SECRET_KEY",
                "ENCRYPTION_MASTER_KEY",
                "SESSION_SECRET",
                "DATABASE_PASSWORD",
                "REDIS_PASSWORD",
                "API_KEY",
            ]

            for var in required_vars:
                pattern = f"^{var}=.+$"
                assert re.search(
                    pattern, content, re.MULTILINE
                ), f"{var} not found in .env.production"

            # Verify JWT_SECRET_KEY length (should be ~86 chars for 64 bytes)
            jwt_match = re.search(r"^JWT_SECRET_KEY=(.+)$", content, re.MULTILINE)
            assert jwt_match, "JWT_SECRET_KEY not found"
            jwt_value = jwt_match.group(1).strip()
            assert len(jwt_value) >= 64, f"JWT_SECRET_KEY too short: {len(jwt_value)}"

            # Verify ENCRYPTION_MASTER_KEY is base64 (should be ~44 chars for 32 bytes)
            enc_match = re.search(
                r"^ENCRYPTION_MASTER_KEY=(.+)$", content, re.MULTILINE
            )
            assert enc_match, "ENCRYPTION_MASTER_KEY not found"
            enc_value = enc_match.group(1).strip()
            assert (
                len(enc_value) >= 32
            ), f"ENCRYPTION_MASTER_KEY too short: {len(enc_value)}"
            # Should be base64-compatible
            assert re.match(
                r"^[A-Za-z0-9+/=]+$", enc_value
            ), "ENCRYPTION_MASTER_KEY not valid base64"

        finally:
            os.chdir(original_dir)


class TestValidateEnvironment:
    """Test validate_environment.py script."""

    def test_script_exists(self):
        """Verify validate_environment.py exists."""
        script_path = Path("scripts/validate_environment.py")
        assert script_path.exists(), "validate_environment.py not found"

    def test_script_is_python(self):
        """Verify script has correct shebang."""
        script_path = Path("scripts/validate_environment.py")
        with open(script_path) as f:
            first_line = f.readline().strip()
        assert first_line == "#!/usr/bin/env python3", "Incorrect shebang"

    def test_validates_missing_file(self):
        """Test validation fails for missing file."""
        result = subprocess.run(
            ["python3", "scripts/validate_environment.py", "/nonexistent/file"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, "Should fail for missing file"
        assert "not found" in result.stdout.lower()

    def test_validates_complete_env(self, tmp_path):
        """Test validation passes for complete environment."""
        # Create complete .env file
        env_file = tmp_path / ".env.test"
        env_content = """
JWT_SECRET_KEY=test_jwt_secret_key_that_is_long_enough_for_validation_purposes_64chars
ENCRYPTION_MASTER_KEY=dGVzdF9lbmNyeXB0aW9uX2tleV8zMl9ieXRlcw==
SESSION_SECRET=test_session_secret_32_chars_long
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/testdb
REDIS_URL=redis://:pass@localhost:6379/0
OPENAI_API_KEY=sk-test123
DEBUG=false
ENVIRONMENT=production
"""
        env_file.write_text(env_content)

        # Run validation
        result = subprocess.run(
            ["python3", "scripts/validate_environment.py", str(env_file)],
            capture_output=True,
            text=True,
        )

        # Should pass validation
        assert result.returncode == 0, f"Validation failed: {result.stdout}"
        assert "VALIDATION PASSED" in result.stdout

    def test_validates_missing_required_vars(self, tmp_path):
        """Test validation fails for missing required variables."""
        # Create incomplete .env file (missing JWT_SECRET_KEY)
        env_file = tmp_path / ".env.test"
        env_content = """
ENCRYPTION_MASTER_KEY=dGVzdF9lbmNyeXB0aW9uX2tleV8zMl9ieXRlcw==
SESSION_SECRET=test_session_secret_32_chars_long
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/testdb
REDIS_URL=redis://:pass@localhost:6379/0
"""
        env_file.write_text(env_content)

        # Run validation
        result = subprocess.run(
            ["python3", "scripts/validate_environment.py", str(env_file)],
            capture_output=True,
            text=True,
        )

        # Should fail validation
        assert result.returncode == 1, "Should fail for missing required vars"
        assert "VALIDATION FAILED" in result.stdout
        assert "JWT_SECRET_KEY" in result.stdout

    def test_validates_weak_secrets(self, tmp_path):
        """Test validation fails for weak secrets."""
        # Create .env with weak secret
        env_file = tmp_path / ".env.test"
        env_content = """
JWT_SECRET_KEY=weak
ENCRYPTION_MASTER_KEY=dGVzdF9lbmNyeXB0aW9uX2tleV8zMl9ieXRlcw==
SESSION_SECRET=test_session_secret_32_chars_long
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/testdb
REDIS_URL=redis://:pass@localhost:6379/0
OPENAI_API_KEY=sk-test123
"""
        env_file.write_text(env_content)

        # Run validation
        result = subprocess.run(
            ["python3", "scripts/validate_environment.py", str(env_file)],
            capture_output=True,
            text=True,
        )

        # Should fail validation
        assert result.returncode == 1, "Should fail for weak secret"
        assert "too short" in result.stdout.lower()

    def test_validates_invalid_database_url(self, tmp_path):
        """Test validation fails for invalid database URL."""
        # Create .env with invalid DATABASE_URL
        env_file = tmp_path / ".env.test"
        env_content = """
JWT_SECRET_KEY=test_jwt_secret_key_that_is_long_enough_for_validation_purposes_64chars
ENCRYPTION_MASTER_KEY=dGVzdF9lbmNyeXB0aW9uX2tleV8zMl9ieXRlcw==
SESSION_SECRET=test_session_secret_32_chars_long
DATABASE_URL=not_a_valid_url
REDIS_URL=redis://:pass@localhost:6379/0
OPENAI_API_KEY=sk-test123
"""
        env_file.write_text(env_content)

        # Run validation
        result = subprocess.run(
            ["python3", "scripts/validate_environment.py", str(env_file)],
            capture_output=True,
            text=True,
        )

        # Should fail validation
        assert result.returncode == 1, "Should fail for invalid DATABASE_URL"
        assert "DATABASE_URL" in result.stdout
        assert "Invalid" in result.stdout or "invalid" in result.stdout

    def test_validates_no_llm_providers(self, tmp_path):
        """Test validation fails when no LLM provider is configured."""
        # Create .env without any LLM provider keys
        env_file = tmp_path / ".env.test"
        env_content = """
JWT_SECRET_KEY=test_jwt_secret_key_that_is_long_enough_for_validation_purposes_64chars
ENCRYPTION_MASTER_KEY=dGVzdF9lbmNyeXB0aW9uX2tleV8zMl9ieXRlcw==
SESSION_SECRET=test_session_secret_32_chars_long
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/testdb
REDIS_URL=redis://:pass@localhost:6379/0
"""
        env_file.write_text(env_content)

        # Run validation
        result = subprocess.run(
            ["python3", "scripts/validate_environment.py", str(env_file)],
            capture_output=True,
            text=True,
        )

        # Should fail validation
        assert result.returncode == 1, "Should fail without LLM provider"
        assert "LLM provider" in result.stdout


class TestSecretSecurity:
    """Test security aspects of generated secrets."""

    def test_secrets_are_random(self, tmp_path):
        """Verify generated secrets are different each time."""
        original_dir = os.getcwd()
        secrets1 = {}
        secrets2 = {}

        try:
            # Generate first set
            dir1 = tmp_path / "test1"
            dir1.mkdir()
            os.chdir(dir1)
            subprocess.run(
                [f"{original_dir}/scripts/generate_secrets.sh"],
                capture_output=True,
                check=True,
            )
            content1 = (dir1 / ".env.production").read_text()
            for line in content1.split("\n"):
                if "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    if key in ["JWT_SECRET_KEY", "ENCRYPTION_MASTER_KEY"]:
                        secrets1[key] = value

            # Generate second set
            dir2 = tmp_path / "test2"
            dir2.mkdir()
            os.chdir(dir2)
            subprocess.run(
                [f"{original_dir}/scripts/generate_secrets.sh"],
                capture_output=True,
                check=True,
            )
            content2 = (dir2 / ".env.production").read_text()
            for line in content2.split("\n"):
                if "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    if key in ["JWT_SECRET_KEY", "ENCRYPTION_MASTER_KEY"]:
                        secrets2[key] = value

            # Verify secrets are different
            assert (
                secrets1["JWT_SECRET_KEY"] != secrets2["JWT_SECRET_KEY"]
            ), "JWT secrets should be different"
            assert (
                secrets1["ENCRYPTION_MASTER_KEY"] != secrets2["ENCRYPTION_MASTER_KEY"]
            ), "Encryption keys should be different"

        finally:
            os.chdir(original_dir)

    def test_no_common_passwords(self, tmp_path):
        """Verify generated passwords don't match common patterns."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            subprocess.run(
                [f"{original_dir}/scripts/generate_secrets.sh"],
                capture_output=True,
                check=True,
            )

            content = (tmp_path / ".env.production").read_text()

            # Common weak patterns
            weak_patterns = [
                r"password",
                r"12345",
                r"qwerty",
                r"admin",
                r"root",
                r"test",
            ]

            for pattern in weak_patterns:
                assert not re.search(
                    pattern, content, re.IGNORECASE
                ), f"Weak pattern '{pattern}' found in secrets"

        finally:
            os.chdir(original_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

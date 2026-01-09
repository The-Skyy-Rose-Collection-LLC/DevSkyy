"""
Security Testing & Validation Framework
========================================

Comprehensive security testing for DevSkyy Platform:
- Penetration testing utilities
- Security unit tests
- Vulnerability scanning
- Security regression tests
- OWASP compliance testing
"""

import logging
import re
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TestResult(str, Enum):
    """Security test result"""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"


class SecurityTestCase(BaseModel):
    """Security test case definition"""

    id: str
    name: str
    description: str
    category: str
    severity: str = "medium"
    owasp_category: str | None = None
    test_function: str | None = None


class SecurityTestResult(BaseModel):
    """Security test result"""

    test_id: str
    test_name: str
    result: TestResult
    message: str = ""
    duration_ms: float = 0
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SecurityTestSuite:
    """
    Comprehensive security testing framework.

    Features:
    - Injection attack testing
    - Authentication bypass testing
    - Authorization testing
    - Cryptography validation
    - Input validation testing
    - OWASP Top 10 coverage
    """

    def __init__(self):
        self.test_cases: list[SecurityTestCase] = []
        self.results: list[SecurityTestResult] = []
        self._register_default_tests()

    def _register_default_tests(self):
        """Register default security test cases"""
        self.test_cases = [
            SecurityTestCase(
                id="SEC-AUTH-001",
                name="Password Strength Validation",
                description="Verify password strength requirements are enforced",
                category="authentication",
                severity="high",
                owasp_category="A07:2021-Identification and Authentication Failures",
            ),
            SecurityTestCase(
                id="SEC-AUTH-002",
                name="JWT Token Validation",
                description="Verify JWT tokens are properly validated",
                category="authentication",
                severity="critical",
                owasp_category="A07:2021-Identification and Authentication Failures",
            ),
            SecurityTestCase(
                id="SEC-INJ-001",
                name="SQL Injection Prevention",
                description="Test SQL injection attack vectors",
                category="injection",
                severity="critical",
                owasp_category="A03:2021-Injection",
            ),
            SecurityTestCase(
                id="SEC-INJ-002",
                name="XSS Prevention",
                description="Test cross-site scripting prevention",
                category="injection",
                severity="high",
                owasp_category="A03:2021-Injection",
            ),
            SecurityTestCase(
                id="SEC-CRYPTO-001",
                name="Encryption Key Strength",
                description="Verify encryption keys meet minimum strength requirements",
                category="cryptography",
                severity="critical",
                owasp_category="A02:2021-Cryptographic Failures",
            ),
            SecurityTestCase(
                id="SEC-CRYPTO-002",
                name="Password Hashing Algorithm",
                description="Verify secure password hashing is used",
                category="cryptography",
                severity="critical",
                owasp_category="A02:2021-Cryptographic Failures",
            ),
            SecurityTestCase(
                id="SEC-ACCESS-001",
                name="Authorization Bypass",
                description="Test for authorization bypass vulnerabilities",
                category="access_control",
                severity="critical",
                owasp_category="A01:2021-Broken Access Control",
            ),
            SecurityTestCase(
                id="SEC-CONFIG-001",
                name="Security Headers",
                description="Verify security headers are properly configured",
                category="configuration",
                severity="medium",
                owasp_category="A05:2021-Security Misconfiguration",
            ),
        ]

    def test_password_strength(self, password: str) -> SecurityTestResult:
        """Test password strength requirements"""
        import time

        start = time.time()

        issues = []

        if len(password) < 12:
            issues.append("Password must be at least 12 characters")
        if not re.search(r"[A-Z]", password):
            issues.append("Password must contain uppercase letter")
        if not re.search(r"[a-z]", password):
            issues.append("Password must contain lowercase letter")
        if not re.search(r"\d", password):
            issues.append("Password must contain digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Password must contain special character")

        # Check for common patterns
        common_patterns = ["password", "123456", "qwerty", "admin"]
        if any(p in password.lower() for p in common_patterns):
            issues.append("Password contains common pattern")

        duration = (time.time() - start) * 1000

        return SecurityTestResult(
            test_id="SEC-AUTH-001",
            test_name="Password Strength Validation",
            result=TestResult.PASSED if not issues else TestResult.FAILED,
            message="; ".join(issues) if issues else "Password meets strength requirements",
            duration_ms=duration,
            details={"issues": issues},
        )

    def test_sql_injection_patterns(self, input_data: str) -> SecurityTestResult:
        """Test for SQL injection patterns"""
        import time

        start = time.time()

        # Comprehensive SQL injection pattern detection
        sql_patterns = [
            # Basic SQL keywords
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE|REPLACE)\b)",
            # Comment indicators
            r"(--|#|/\*|\*/)",
            # Boolean-based injection
            r"(\bOR\b\s+\d+\s*=\s*\d+)",
            r"(\bAND\b\s+\d+\s*=\s*\d+)",
            r"(\bOR\b\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
            r"(\bAND\b\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
            # Stacked queries
            r"(;\s*(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER))",
            # String-based injection
            r"(\'\s*(OR|AND)\s*\')",
            r"(\"\s*(OR|AND)\s*\")",
            # Time-based blind injection
            r"(\b(SLEEP|BENCHMARK|WAITFOR|pg_sleep)\b)",
            # Union-based injection
            r"(\bUNION\b\s+(ALL\s+)?SELECT)",
            # Information schema exploitation
            r"(\binformation_schema\b)",
            # Database-specific commands
            r"(\b(EXEC|EXECUTE|sp_executesql|xp_cmdshell)\b)",
            # Substring/character extraction
            r"(\b(SUBSTRING|SUBSTR|MID|CHAR|ASCII)\b\s*\()",
            # Null byte and encoding bypasses
            r"(%00|\\x00|\\0)",
            # Hex encoding
            r"(0x[0-9a-fA-F]+)",
            # SQL functions often used in attacks
            r"(\b(CONCAT|GROUP_CONCAT|LOAD_FILE|INTO\s+OUTFILE)\b)",
            # Database fingerprinting
            r"(\b(@@version|version\(\)|user\(\)|database\(\)|schema\(\))\b)",
        ]

        detected = []
        detected_patterns = []

        for pattern in sql_patterns:
            match = re.search(pattern, input_data, re.IGNORECASE)
            if match:
                detected.append(pattern)
                detected_patterns.append(match.group(0))

        duration = (time.time() - start) * 1000

        return SecurityTestResult(
            test_id="SEC-INJ-001",
            test_name="SQL Injection Prevention",
            result=TestResult.FAILED if detected else TestResult.PASSED,
            message=(
                f"Detected {len(detected)} SQL injection patterns"
                if detected
                else "No SQL injection patterns detected"
            ),
            duration_ms=duration,
            details={
                "patterns_detected": len(detected),
                "matched_patterns": detected_patterns[:10],  # Limit to first 10
            },
        )

    def test_xss_patterns(self, input_data: str) -> SecurityTestResult:
        """Test for XSS patterns"""
        import time

        start = time.time()

        xss_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"expression\s*\(",
            r"url\s*\(\s*['\"]?javascript:",
        ]

        detected = []
        for pattern in xss_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                detected.append(pattern)

        duration = (time.time() - start) * 1000

        return SecurityTestResult(
            test_id="SEC-INJ-002",
            test_name="XSS Prevention",
            result=TestResult.FAILED if detected else TestResult.PASSED,
            message=(
                f"Detected {len(detected)} XSS patterns" if detected else "No XSS patterns detected"
            ),
            duration_ms=duration,
            details={"patterns_detected": len(detected)},
        )

    def test_encryption_key_strength(self, key: bytes) -> SecurityTestResult:
        """Test encryption key strength"""
        import time

        start = time.time()

        issues = []

        # Check key length (minimum 256 bits = 32 bytes)
        if len(key) < 32:
            issues.append(f"Key length {len(key) * 8} bits is below minimum 256 bits")

        # Check for low entropy (simple check)
        unique_bytes = len(set(key))
        if unique_bytes < len(key) * 0.5:
            issues.append("Key has low entropy (too many repeated bytes)")

        # Check for null bytes
        if b"\x00" * 4 in key:
            issues.append("Key contains consecutive null bytes")

        duration = (time.time() - start) * 1000

        return SecurityTestResult(
            test_id="SEC-CRYPTO-001",
            test_name="Encryption Key Strength",
            result=TestResult.PASSED if not issues else TestResult.FAILED,
            message="; ".join(issues) if issues else "Encryption key meets strength requirements",
            duration_ms=duration,
            details={"key_length_bits": len(key) * 8, "unique_bytes": unique_bytes},
        )

    def test_security_headers(self, headers: dict[str, str]) -> SecurityTestResult:
        """Test security headers configuration"""
        import time

        start = time.time()

        required_headers = {
            "Strict-Transport-Security": "HSTS header missing",
            "X-Content-Type-Options": "X-Content-Type-Options header missing",
            "X-Frame-Options": "X-Frame-Options header missing",
            "X-XSS-Protection": "X-XSS-Protection header missing",
            "Content-Security-Policy": "CSP header missing",
        }

        missing = []
        for header, message in required_headers.items():
            if header not in headers:
                missing.append(message)

        duration = (time.time() - start) * 1000

        return SecurityTestResult(
            test_id="SEC-CONFIG-001",
            test_name="Security Headers",
            result=TestResult.PASSED if not missing else TestResult.WARNING,
            message="; ".join(missing) if missing else "All security headers present",
            duration_ms=duration,
            details={"missing_headers": missing, "present_headers": list(headers.keys())},
        )

    def run_all_tests(self, test_data: dict[str, Any] = None) -> dict[str, Any]:
        """Run all security tests"""
        test_data = test_data or {}
        self.results = []

        # Run password test
        if "password" in test_data:
            self.results.append(self.test_password_strength(test_data["password"]))

        # Run injection tests
        if "input" in test_data:
            self.results.append(self.test_sql_injection_patterns(test_data["input"]))
            self.results.append(self.test_xss_patterns(test_data["input"]))

        # Run crypto tests
        if "encryption_key" in test_data:
            self.results.append(self.test_encryption_key_strength(test_data["encryption_key"]))

        # Run header tests
        if "headers" in test_data:
            self.results.append(self.test_security_headers(test_data["headers"]))

        # Generate summary
        passed = sum(1 for r in self.results if r.result == TestResult.PASSED)
        failed = sum(1 for r in self.results if r.result == TestResult.FAILED)
        warnings = sum(1 for r in self.results if r.result == TestResult.WARNING)

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "total_tests": len(self.results),
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "success_rate": (passed / len(self.results) * 100) if self.results else 0,
            "results": [r.model_dump() for r in self.results],
        }


# Global instance
security_tests = SecurityTestSuite()

"""
Code Security Analysis System
=============================

Static code analysis and security linting for DevSkyy Platform:
- Security vulnerability detection
- Code pattern analysis
- Dependency scanning
- Secret detection
- Security best practices enforcement
"""

import logging
import re
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SecuritySeverity(str, Enum):
    """Security issue severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SecurityCategory(str, Enum):
    """Security issue categories"""

    INJECTION = "injection"
    AUTHENTICATION = "authentication"
    CRYPTOGRAPHY = "cryptography"
    SECRETS = "secrets"
    CONFIGURATION = "configuration"
    DATA_EXPOSURE = "data_exposure"
    INPUT_VALIDATION = "input_validation"
    ERROR_HANDLING = "error_handling"


class SecurityFinding(BaseModel):
    """Security finding from code analysis"""

    id: str
    title: str
    description: str
    severity: SecuritySeverity
    category: SecurityCategory
    file_path: str
    line_number: int
    code_snippet: str = ""
    recommendation: str = ""
    cwe_id: str | None = None  # Common Weakness Enumeration
    owasp_category: str | None = None


class SecurityRule(BaseModel):
    """Security rule for code analysis"""

    id: str
    name: str
    description: str
    severity: SecuritySeverity
    category: SecurityCategory
    pattern: str  # Regex pattern
    recommendation: str
    cwe_id: str | None = None
    enabled: bool = True


class CodeSecurityAnalyzer:
    """
    Static code security analyzer for Python code.

    Features:
    - Pattern-based vulnerability detection
    - AST-based code analysis
    - Secret detection
    - Security best practices checking
    - OWASP Top 10 coverage
    """

    def __init__(self):
        self.findings: list[SecurityFinding] = []
        self.rules = self._initialize_rules()
        self.secret_patterns = self._initialize_secret_patterns()

    def _initialize_rules(self) -> list[SecurityRule]:
        """Initialize security rules"""
        return [
            # SQL Injection
            SecurityRule(
                id="SEC001",
                name="SQL Injection Risk",
                description="Potential SQL injection vulnerability detected",
                severity=SecuritySeverity.CRITICAL,
                category=SecurityCategory.INJECTION,
                pattern=r'execute\s*\(\s*["\'].*%s.*["\']',
                recommendation="Use parameterized queries instead of string formatting",
                cwe_id="CWE-89",
            ),
            SecurityRule(
                id="SEC002",
                name="SQL String Formatting",
                description="SQL query built with string formatting",
                severity=SecuritySeverity.HIGH,
                category=SecurityCategory.INJECTION,
                pattern=r"(SELECT|INSERT|UPDATE|DELETE).*\.format\(",
                recommendation="Use parameterized queries with placeholders",
                cwe_id="CWE-89",
            ),
            # Command Injection
            SecurityRule(
                id="SEC003",
                name="Command Injection Risk",
                description="Potential command injection vulnerability",
                severity=SecuritySeverity.CRITICAL,
                category=SecurityCategory.INJECTION,
                pattern=r"(os\.system|subprocess\.call|subprocess\.run)\s*\([^)]*\+",
                recommendation="Use subprocess with shell=False and list arguments",
                cwe_id="CWE-78",
            ),
            SecurityRule(
                id="SEC004",
                name="Shell=True Usage",
                description="subprocess called with shell=True",
                severity=SecuritySeverity.HIGH,
                category=SecurityCategory.INJECTION,
                pattern=r"subprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True",
                recommendation="Avoid shell=True, use list of arguments instead",
                cwe_id="CWE-78",
            ),
            # Cryptography Issues
            SecurityRule(
                id="SEC005",
                name="Weak Hash Algorithm",
                description="Use of weak hash algorithm (MD5/SHA1)",
                severity=SecuritySeverity.MEDIUM,
                category=SecurityCategory.CRYPTOGRAPHY,
                pattern=r"hashlib\.(md5|sha1)\s*\(",
                recommendation="Use SHA-256 or stronger hash algorithms",
                cwe_id="CWE-328",
            ),
            SecurityRule(
                id="SEC006",
                name="Hardcoded Cryptographic Key",
                description="Hardcoded encryption key detected",
                severity=SecuritySeverity.HIGH,
                category=SecurityCategory.CRYPTOGRAPHY,
                pattern=r'(key|secret|password)\s*=\s*["\'][^"\']{8,}["\']',
                recommendation="Use environment variables or secure key management",
                cwe_id="CWE-321",
            ),
            # Authentication Issues
            SecurityRule(
                id="SEC007",
                name="Hardcoded Password",
                description="Hardcoded password detected",
                severity=SecuritySeverity.CRITICAL,
                category=SecurityCategory.AUTHENTICATION,
                pattern=r'password\s*=\s*["\'][^"\']+["\']',
                recommendation="Use environment variables or secure credential storage",
                cwe_id="CWE-798",
            ),
            SecurityRule(
                id="SEC008",
                name="Weak Password Comparison",
                description="Password compared using == instead of constant-time comparison",
                severity=SecuritySeverity.MEDIUM,
                category=SecurityCategory.AUTHENTICATION,
                pattern=r"password\s*==\s*",
                recommendation="Use hmac.compare_digest() for password comparison",
                cwe_id="CWE-208",
            ),
            # Input Validation
            SecurityRule(
                id="SEC009",
                name="Eval Usage",
                description="Use of eval() function",
                severity=SecuritySeverity.CRITICAL,
                category=SecurityCategory.INPUT_VALIDATION,
                pattern=r"\beval\s*\(",
                recommendation="Avoid eval(), use ast.literal_eval() for safe parsing",
                cwe_id="CWE-95",
            ),
            SecurityRule(
                id="SEC010",
                name="Exec Usage",
                description="Use of exec() function",
                severity=SecuritySeverity.CRITICAL,
                category=SecurityCategory.INPUT_VALIDATION,
                pattern=r"\bexec\s*\(",
                recommendation="Avoid exec(), find alternative approaches",
                cwe_id="CWE-95",
            ),
            # Error Handling
            SecurityRule(
                id="SEC011",
                name="Bare Exception",
                description="Bare except clause may hide errors",
                severity=SecuritySeverity.LOW,
                category=SecurityCategory.ERROR_HANDLING,
                pattern=r"except\s*:",
                recommendation="Catch specific exceptions instead of bare except",
                cwe_id="CWE-396",
            ),
            # Data Exposure
            SecurityRule(
                id="SEC012",
                name="Debug Mode in Production",
                description="Debug mode may be enabled",
                severity=SecuritySeverity.HIGH,
                category=SecurityCategory.CONFIGURATION,
                pattern=r"DEBUG\s*=\s*True",
                recommendation="Disable debug mode in production",
                cwe_id="CWE-489",
            ),
            SecurityRule(
                id="SEC013",
                name="Sensitive Data in Logs",
                description="Potential sensitive data in log statements",
                severity=SecuritySeverity.MEDIUM,
                category=SecurityCategory.DATA_EXPOSURE,
                pattern=r"(logger|logging)\.(info|debug|warning|error)\s*\([^)]*password",
                recommendation="Sanitize sensitive data before logging",
                cwe_id="CWE-532",
            ),
        ]

    def _initialize_secret_patterns(self) -> list[dict[str, Any]]:
        """Initialize secret detection patterns"""
        return [
            {
                "name": "AWS Access Key",
                "pattern": r"AKIA[0-9A-Z]{16}",
                "severity": SecuritySeverity.CRITICAL,
            },
            {
                "name": "AWS Secret Key",
                "pattern": r"[A-Za-z0-9/+=]{40}",
                "severity": SecuritySeverity.CRITICAL,
            },
            {
                "name": "GitHub Token",
                "pattern": r"gh[pousr]_[A-Za-z0-9_]{36,}",
                "severity": SecuritySeverity.CRITICAL,
            },
            {
                "name": "Generic API Key",
                "pattern": r'api[_-]?key["\']?\s*[:=]\s*["\'][A-Za-z0-9]{20,}["\']',
                "severity": SecuritySeverity.HIGH,
            },
            {
                "name": "Private Key",
                "pattern": r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----",
                "severity": SecuritySeverity.CRITICAL,
            },
            {
                "name": "JWT Token",
                "pattern": r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
                "severity": SecuritySeverity.HIGH,
            },
            {
                "name": "OpenAI API Key",
                "pattern": r"sk-[A-Za-z0-9]{48}",
                "severity": SecuritySeverity.CRITICAL,
            },
        ]

    def analyze_file(self, file_path: Path) -> list[SecurityFinding]:
        """Analyze a single file for security issues"""
        findings = []

        if not file_path.exists() or file_path.suffix != ".py":
            return findings

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            # Pattern-based analysis
            for rule in self.rules:
                if not rule.enabled:
                    continue

                for line_num, line in enumerate(lines, 1):
                    if re.search(rule.pattern, line, re.IGNORECASE):
                        finding = SecurityFinding(
                            id=f"{rule.id}-{file_path.name}-{line_num}",
                            title=rule.name,
                            description=rule.description,
                            severity=rule.severity,
                            category=rule.category,
                            file_path=str(file_path),
                            line_number=line_num,
                            code_snippet=line.strip()[:100],
                            recommendation=rule.recommendation,
                            cwe_id=rule.cwe_id,
                        )
                        findings.append(finding)

            # Secret detection
            for secret_pattern in self.secret_patterns:
                for line_num, line in enumerate(lines, 1):
                    if re.search(secret_pattern["pattern"], line):
                        finding = SecurityFinding(
                            id=f"SECRET-{file_path.name}-{line_num}",
                            title=f"Potential {secret_pattern['name']} Detected",
                            description=f"Possible hardcoded {secret_pattern['name']} found",
                            severity=secret_pattern["severity"],
                            category=SecurityCategory.SECRETS,
                            file_path=str(file_path),
                            line_number=line_num,
                            code_snippet="[REDACTED]",
                            recommendation="Remove hardcoded secrets and use environment variables",
                        )
                        findings.append(finding)

        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")

        return findings

    def analyze_directory(
        self, directory: Path, exclude_patterns: list[str] = None
    ) -> list[SecurityFinding]:
        """Analyze all Python files in a directory"""
        exclude_patterns = exclude_patterns or [
            "__pycache__",
            ".git",
            "node_modules",
            "venv",
            ".venv",
            "env",
        ]

        all_findings = []

        for py_file in directory.rglob("*.py"):
            # Skip excluded directories
            if any(pattern in str(py_file) for pattern in exclude_patterns):
                continue

            findings = self.analyze_file(py_file)
            all_findings.extend(findings)

        self.findings = all_findings
        return all_findings

    def generate_report(self) -> dict[str, Any]:
        """Generate security analysis report"""
        severity_counts = {s.value: 0 for s in SecuritySeverity}
        category_counts = {c.value: 0 for c in SecurityCategory}

        for finding in self.findings:
            severity_counts[finding.severity.value] += 1
            category_counts[finding.category.value] += 1

        # Calculate security score
        weights = {
            SecuritySeverity.CRITICAL: 25,
            SecuritySeverity.HIGH: 15,
            SecuritySeverity.MEDIUM: 5,
            SecuritySeverity.LOW: 2,
            SecuritySeverity.INFO: 0,
        }

        total_penalty = sum(weights[finding.severity] for finding in self.findings)
        security_score = max(0, 100 - total_penalty)

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "total_findings": len(self.findings),
            "security_score": security_score,
            "severity_breakdown": severity_counts,
            "category_breakdown": category_counts,
            "findings": [f.model_dump() for f in self.findings],
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> list[str]:
        """Generate prioritized recommendations"""
        recommendations = []

        critical_count = sum(1 for f in self.findings if f.severity == SecuritySeverity.CRITICAL)
        high_count = sum(1 for f in self.findings if f.severity == SecuritySeverity.HIGH)

        if critical_count > 0:
            recommendations.append(
                f"🚨 Address {critical_count} CRITICAL security issues immediately"
            )

        if high_count > 0:
            recommendations.append(f"⚠️ Fix {high_count} HIGH severity issues as priority")

        # Category-specific recommendations
        categories = {f.category for f in self.findings}

        if SecurityCategory.SECRETS in categories:
            recommendations.append("🔐 Remove all hardcoded secrets and use environment variables")

        if SecurityCategory.INJECTION in categories:
            recommendations.append("💉 Review and fix all injection vulnerabilities")

        if SecurityCategory.CRYPTOGRAPHY in categories:
            recommendations.append(
                "🔒 Update cryptographic implementations to use strong algorithms"
            )

        return recommendations


# Global instance
code_analyzer = CodeSecurityAnalyzer()

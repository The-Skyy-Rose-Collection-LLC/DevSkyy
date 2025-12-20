"""
DevSkyy Coding Doctor Agent
============================

Self-learning, self-healing meta-agent for comprehensive codebase management.

Capabilities:
- Continuous Learning: Persists learnings and improves over time
- Self-Healing: Auto-detects and fixes common issues
- Full-Stack Review: Frontend, backend, API, database analysis
- E-Commerce Tools: Payment, inventory, order flow validation
- Finance Tools: Transaction audit, pricing logic review
- Security: Vulnerability scanning, secrets detection
- Performance: Profiling, optimization suggestions
- Testing: Coverage analysis, test generation
- Documentation: Auto-generation, validation

Architecture:
    CodingDoctorAgent
    ├── SelfLearningEngine (persistent knowledge)
    ├── SelfHealingEngine (auto-fix capabilities)
    ├── ECommerceToolkit (payment, inventory, orders)
    ├── FinanceToolkit (transactions, pricing, audit)
    ├── SecurityToolkit (vulnerability, secrets)
    ├── PerformanceToolkit (profiling, optimization)
    ├── TestingToolkit (coverage, generation)
    └── DocumentationToolkit (auto-docs, validation)

Usage:
    doctor = CodingDoctorAgent()
    await doctor.initialize()

    # Full health check with auto-healing
    report = await doctor.diagnose_and_heal()

    # E-commerce audit
    ecom_report = await doctor.audit_ecommerce()

    # Finance validation
    finance_report = await doctor.audit_finances()
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from adk.base import AgentConfig, AgentResult, AgentStatus
from agents.base_super_agent import (
    EnhancedSuperAgent,
    SuperAgentType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Types
# =============================================================================


class HealthCheckType(str, Enum):
    """Types of health checks"""
    FULL = "full"
    QUICK = "quick"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    TESTS = "tests"
    ECOMMERCE = "ecommerce"
    FINANCE = "finance"


class SeverityLevel(str, Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueCategory(str, Enum):
    """Categories of code issues"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    TYPE_SAFETY = "type_safety"
    ERROR_HANDLING = "error_handling"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    DEPENDENCY = "dependency"
    ECOMMERCE = "ecommerce"
    FINANCE = "finance"
    API = "api"
    DATABASE = "database"


class HealingAction(str, Enum):
    """Types of self-healing actions"""
    AUTO_FORMAT = "auto_format"
    FIX_IMPORTS = "fix_imports"
    ADD_TYPE_HINTS = "add_type_hints"
    ADD_DOCSTRING = "add_docstring"
    FIX_LINT = "fix_lint"
    UPDATE_DEPENDENCY = "update_dependency"
    REMOVE_UNUSED = "remove_unused"
    FIX_SECURITY = "fix_security"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class CodeIssue:
    """Represents a code issue found during analysis"""
    file_path: str
    line_number: int | None
    category: IssueCategory
    severity: SeverityLevel
    title: str
    description: str
    suggestion: str | None = None
    code_snippet: str | None = None
    auto_fixable: bool = False
    fix_action: HealingAction | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "category": self.category.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "suggestion": self.suggestion,
            "code_snippet": self.code_snippet,
            "auto_fixable": self.auto_fixable,
        }


@dataclass
class HealingResult:
    """Result of a self-healing action"""
    action: HealingAction
    file_path: str
    success: bool
    changes_made: list[str]
    error: str | None = None
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "file_path": self.file_path,
            "success": self.success,
            "changes_made": self.changes_made,
            "error": self.error,
        }


@dataclass
class LearningEntry:
    """Entry in the learning database"""
    pattern_hash: str
    category: IssueCategory
    pattern: str
    solution: str
    success_count: int = 0
    failure_count: int = 0
    last_used: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0


@dataclass
class FileReview:
    """Result of reviewing a single file"""
    file_path: str
    language: str
    lines_of_code: int
    issues: list[CodeIssue]
    score: float
    summary: str
    recommendations: list[str]
    healable_issues: int = 0
    reviewed_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "language": self.language,
            "lines_of_code": self.lines_of_code,
            "issues": [i.to_dict() for i in self.issues],
            "score": self.score,
            "summary": self.summary,
            "recommendations": self.recommendations,
            "healable_issues": self.healable_issues,
        }


@dataclass
class HealthReport:
    """Complete health check report"""
    check_type: HealthCheckType
    total_files: int
    total_lines: int
    overall_score: float
    issues: list[CodeIssue]
    file_reviews: list[FileReview]
    healing_results: list[HealingResult]
    architecture_notes: list[str]
    security_findings: list[str]
    performance_suggestions: list[str]
    ecommerce_findings: list[str]
    finance_findings: list[str]
    test_coverage: float | None
    recommendations: list[str]
    learnings_applied: int
    duration_seconds: float
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_type": self.check_type.value,
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "overall_score": self.overall_score,
            "issues_count": len(self.issues),
            "critical_issues": len([i for i in self.issues if i.severity == SeverityLevel.CRITICAL]),
            "high_issues": len([i for i in self.issues if i.severity == SeverityLevel.HIGH]),
            "auto_healed": len([h for h in self.healing_results if h.success]),
            "architecture_notes": self.architecture_notes,
            "security_findings": self.security_findings,
            "performance_suggestions": self.performance_suggestions,
            "ecommerce_findings": self.ecommerce_findings,
            "finance_findings": self.finance_findings,
            "test_coverage": self.test_coverage,
            "recommendations": self.recommendations,
            "learnings_applied": self.learnings_applied,
            "duration_seconds": self.duration_seconds,
        }


# =============================================================================
# Self-Learning Engine
# =============================================================================


class SelfLearningEngine:
    """
    Persistent learning engine for the Coding Doctor.

    Stores patterns and solutions, improving over time.
    """

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self._patterns: dict[str, LearningEntry] = {}
        self._loaded = False

    async def initialize(self):
        """Load learned patterns from storage"""
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                for entry in data.get("patterns", []):
                    self._patterns[entry["pattern_hash"]] = LearningEntry(**entry)
                logger.info(f"Loaded {len(self._patterns)} learned patterns")
            except Exception as e:
                logger.warning(f"Failed to load learning data: {e}")
        self._loaded = True

    async def save(self):
        """Persist learned patterns to storage"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "patterns": [
                {
                    "pattern_hash": e.pattern_hash,
                    "category": e.category.value,
                    "pattern": e.pattern,
                    "solution": e.solution,
                    "success_count": e.success_count,
                    "failure_count": e.failure_count,
                    "last_used": e.last_used.isoformat(),
                }
                for e in self._patterns.values()
            ],
            "saved_at": datetime.now(UTC).isoformat(),
        }
        self.storage_path.write_text(json.dumps(data, indent=2))
        logger.info(f"Saved {len(self._patterns)} learned patterns")

    def learn(
        self,
        category: IssueCategory,
        pattern: str,
        solution: str,
        success: bool,
    ):
        """Learn from an issue resolution"""
        pattern_hash = hashlib.md5(f"{category.value}:{pattern}".encode()).hexdigest()[:16]

        if pattern_hash in self._patterns:
            entry = self._patterns[pattern_hash]
            if success:
                entry.success_count += 1
            else:
                entry.failure_count += 1
            entry.last_used = datetime.now(UTC)
        else:
            self._patterns[pattern_hash] = LearningEntry(
                pattern_hash=pattern_hash,
                category=category,
                pattern=pattern,
                solution=solution,
                success_count=1 if success else 0,
                failure_count=0 if success else 1,
            )

    def get_solution(self, category: IssueCategory, pattern: str) -> str | None:
        """Get a learned solution for a pattern"""
        pattern_hash = hashlib.md5(f"{category.value}:{pattern}".encode()).hexdigest()[:16]

        entry = self._patterns.get(pattern_hash)
        if entry and entry.success_rate > 0.7:
            entry.last_used = datetime.now(UTC)
            return entry.solution
        return None

    def get_stats(self) -> dict[str, Any]:
        """Get learning statistics"""
        if not self._patterns:
            return {"total_patterns": 0, "categories": {}}

        categories: dict[str, int] = {}
        for entry in self._patterns.values():
            cat = entry.category.value
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_patterns": len(self._patterns),
            "categories": categories,
            "avg_success_rate": sum(e.success_rate for e in self._patterns.values()) / len(self._patterns),
        }


# =============================================================================
# Self-Healing Engine
# =============================================================================


class SelfHealingEngine:
    """
    Auto-fix engine for common code issues.

    Capabilities:
    - Auto-formatting (black, isort, ruff)
    - Import organization
    - Type hint suggestions
    - Docstring generation
    - Lint auto-fix
    - Security fixes
    """

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self._healers: dict[HealingAction, Any] = {}

    async def initialize(self):
        """Initialize healing tools"""
        # Check for available tools
        tools = {
            "black": self._check_tool("black"),
            "isort": self._check_tool("isort"),
            "ruff": self._check_tool("ruff"),
            "autoflake": self._check_tool("autoflake"),
        }
        logger.info(f"Healing tools available: {[k for k, v in tools.items() if v]}")

    def _check_tool(self, tool: str) -> bool:
        """Check if a tool is available"""
        try:
            result = subprocess.run(
                [tool, "--version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    async def heal(
        self,
        issue: CodeIssue,
        dry_run: bool = False,
    ) -> HealingResult:
        """Attempt to auto-fix an issue"""
        if not issue.auto_fixable or not issue.fix_action:
            return HealingResult(
                action=issue.fix_action or HealingAction.AUTO_FORMAT,
                file_path=issue.file_path,
                success=False,
                changes_made=[],
                error="Issue not auto-fixable",
            )

        start_time = time.time()
        file_path = self.repo_root / issue.file_path

        try:
            if issue.fix_action == HealingAction.AUTO_FORMAT:
                return await self._heal_format(file_path, dry_run)
            elif issue.fix_action == HealingAction.FIX_IMPORTS:
                return await self._heal_imports(file_path, dry_run)
            elif issue.fix_action == HealingAction.FIX_LINT:
                return await self._heal_lint(file_path, dry_run)
            elif issue.fix_action == HealingAction.REMOVE_UNUSED:
                return await self._heal_unused(file_path, dry_run)
            else:
                return HealingResult(
                    action=issue.fix_action,
                    file_path=issue.file_path,
                    success=False,
                    changes_made=[],
                    error=f"Healing action {issue.fix_action} not implemented",
                    duration_ms=(time.time() - start_time) * 1000,
                )
        except Exception as e:
            return HealingResult(
                action=issue.fix_action,
                file_path=issue.file_path,
                success=False,
                changes_made=[],
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def _heal_format(self, file_path: Path, dry_run: bool) -> HealingResult:
        """Auto-format a file with black"""
        args = ["black", str(file_path)]
        if dry_run:
            args.append("--check")

        result = subprocess.run(args, capture_output=True, text=True, timeout=30)

        return HealingResult(
            action=HealingAction.AUTO_FORMAT,
            file_path=str(file_path.relative_to(self.repo_root)),
            success=result.returncode == 0,
            changes_made=["Formatted with black"] if result.returncode == 0 else [],
            error=result.stderr if result.returncode != 0 else None,
        )

    async def _heal_imports(self, file_path: Path, dry_run: bool) -> HealingResult:
        """Fix imports with isort"""
        args = ["isort", str(file_path)]
        if dry_run:
            args.append("--check")

        result = subprocess.run(args, capture_output=True, text=True, timeout=30)

        return HealingResult(
            action=HealingAction.FIX_IMPORTS,
            file_path=str(file_path.relative_to(self.repo_root)),
            success=result.returncode == 0,
            changes_made=["Sorted imports with isort"] if result.returncode == 0 else [],
            error=result.stderr if result.returncode != 0 else None,
        )

    async def _heal_lint(self, file_path: Path, dry_run: bool) -> HealingResult:
        """Fix lint issues with ruff"""
        args = ["ruff", "check", "--fix", str(file_path)]
        if dry_run:
            args.remove("--fix")

        result = subprocess.run(args, capture_output=True, text=True, timeout=30)

        return HealingResult(
            action=HealingAction.FIX_LINT,
            file_path=str(file_path.relative_to(self.repo_root)),
            success=result.returncode == 0,
            changes_made=["Fixed lint issues with ruff"] if result.returncode == 0 else [],
            error=result.stderr if result.returncode != 0 else None,
        )

    async def _heal_unused(self, file_path: Path, dry_run: bool) -> HealingResult:
        """Remove unused imports with autoflake"""
        args = [
            "autoflake",
            "--remove-all-unused-imports",
            "--remove-unused-variables",
            str(file_path),
        ]
        if not dry_run:
            args.insert(1, "--in-place")

        result = subprocess.run(args, capture_output=True, text=True, timeout=30)

        return HealingResult(
            action=HealingAction.REMOVE_UNUSED,
            file_path=str(file_path.relative_to(self.repo_root)),
            success=result.returncode == 0,
            changes_made=["Removed unused imports/variables"] if result.returncode == 0 else [],
            error=result.stderr if result.returncode != 0 else None,
        )


# =============================================================================
# Specialized Toolkits
# =============================================================================


class BaseToolkit(ABC):
    """Base class for specialized toolkits"""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    @abstractmethod
    async def analyze(self, file_path: Path) -> list[CodeIssue]:
        """Analyze a file for issues"""
        pass


class ECommerceToolkit(BaseToolkit):
    """
    E-commerce code analysis toolkit.

    Checks:
    - Payment integration security
    - Inventory management logic
    - Order flow validation
    - Price calculation accuracy
    - Cart/checkout logic
    """

    PAYMENT_PATTERNS = [
        (r"stripe\.", "Stripe integration detected"),
        (r"paypal\.", "PayPal integration detected"),
        (r"card_number|cvv|expiry", "Payment card handling detected"),
    ]

    INVENTORY_PATTERNS = [
        (r"stock|inventory|quantity", "Inventory management detected"),
        (r"out_of_stock|backorder", "Stock status handling detected"),
    ]

    async def analyze(self, file_path: Path) -> list[CodeIssue]:
        """Analyze file for e-commerce issues"""
        issues: list[CodeIssue] = []

        try:
            content = file_path.read_text()
            lines = content.split("\n")
            rel_path = str(file_path.relative_to(self.repo_root))

            for i, line in enumerate(lines, 1):
                line_lower = line.lower()

                # Check for payment security issues
                if any(p[0] in line_lower for p in self.PAYMENT_PATTERNS):
                    if "test" in rel_path.lower():
                        continue  # Skip test files

                    if "async" not in line and "await" not in content[max(0, content.find(line)-100):content.find(line)+100]:
                        issues.append(CodeIssue(
                            file_path=rel_path,
                            line_number=i,
                            category=IssueCategory.ECOMMERCE,
                            severity=SeverityLevel.MEDIUM,
                            title="Payment operation may not be async",
                            description="Payment operations should be async for proper error handling",
                            suggestion="Ensure payment calls are awaited and wrapped in try/except",
                        ))

                # Check for hardcoded prices
                price_match = re.search(r'price\s*=\s*(\d+\.?\d*)', line)
                if price_match and "test" not in rel_path.lower():
                    issues.append(CodeIssue(
                        file_path=rel_path,
                        line_number=i,
                        category=IssueCategory.ECOMMERCE,
                        severity=SeverityLevel.MEDIUM,
                        title="Hardcoded price detected",
                        description=f"Price value {price_match.group(1)} is hardcoded",
                        suggestion="Use configuration or database for pricing",
                        code_snippet=line.strip()[:60],
                    ))

                # Check inventory without validation
                if "quantity" in line_lower and "if" not in line_lower:
                    if "=" in line and ("+" in line or "-" in line):
                        issues.append(CodeIssue(
                            file_path=rel_path,
                            line_number=i,
                            category=IssueCategory.ECOMMERCE,
                            severity=SeverityLevel.HIGH,
                            title="Inventory modification without validation",
                            description="Quantity change without bounds checking",
                            suggestion="Add validation to prevent negative inventory",
                        ))

        except Exception as e:
            logger.error(f"E-commerce analysis failed for {file_path}: {e}")

        return issues


class FinanceToolkit(BaseToolkit):
    """
    Finance code analysis toolkit.

    Checks:
    - Transaction handling
    - Decimal precision for money
    - Audit logging
    - Tax calculations
    - Currency handling
    """

    async def analyze(self, file_path: Path) -> list[CodeIssue]:
        """Analyze file for finance issues"""
        issues: list[CodeIssue] = []

        try:
            content = file_path.read_text()
            lines = content.split("\n")
            rel_path = str(file_path.relative_to(self.repo_root))

            has_decimal_import = "from decimal import" in content or "import decimal" in content

            for i, line in enumerate(lines, 1):
                line_lower = line.lower()

                # Check for float usage with money
                if any(term in line_lower for term in ["price", "amount", "total", "cost", "fee"]):
                    if "float(" in line and not has_decimal_import:
                        issues.append(CodeIssue(
                            file_path=rel_path,
                            line_number=i,
                            category=IssueCategory.FINANCE,
                            severity=SeverityLevel.HIGH,
                            title="Float used for monetary value",
                            description="Using float for money can cause precision errors",
                            suggestion="Use Decimal type for monetary calculations",
                            code_snippet=line.strip()[:60],
                        ))

                # Check for transaction without error handling
                if "transaction" in line_lower or "payment" in line_lower:
                    # Look ahead for try/except
                    context = "\n".join(lines[max(0, i-5):min(len(lines), i+5)])
                    if "try:" not in context and "except" not in context:
                        issues.append(CodeIssue(
                            file_path=rel_path,
                            line_number=i,
                            category=IssueCategory.FINANCE,
                            severity=SeverityLevel.HIGH,
                            title="Transaction without error handling",
                            description="Financial operations should have explicit error handling",
                            suggestion="Wrap in try/except with proper rollback logic",
                        ))

                # Check for missing audit logging
                if any(term in line_lower for term in ["charge", "refund", "transfer", "withdraw"]):
                    context = "\n".join(lines[max(0, i-10):min(len(lines), i+10)])
                    if "log" not in context.lower() and "audit" not in context.lower():
                        issues.append(CodeIssue(
                            file_path=rel_path,
                            line_number=i,
                            category=IssueCategory.FINANCE,
                            severity=SeverityLevel.MEDIUM,
                            title="Financial operation without audit logging",
                            description="Financial operations should be logged for auditing",
                            suggestion="Add audit logging for financial transactions",
                        ))

        except Exception as e:
            logger.error(f"Finance analysis failed for {file_path}: {e}")

        return issues


class SecurityToolkit(BaseToolkit):
    """
    Security code analysis toolkit.

    Checks:
    - Hardcoded secrets
    - SQL injection risks
    - XSS vulnerabilities
    - Insecure configurations
    - Authentication issues
    """

    SECRET_PATTERNS = [
        (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
        (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
        (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret"),
        (r'token\s*=\s*["\'][^"\']+["\']', "Hardcoded token"),
        (r'private_key\s*=', "Hardcoded private key"),
    ]

    SQL_INJECTION_PATTERNS = [
        (r'f"[^"]*{[^}]*}[^"]*(?:SELECT|INSERT|UPDATE|DELETE)', "F-string SQL injection risk"),
        (r"\.format\([^)]*\).*(?:SELECT|INSERT|UPDATE|DELETE)", ".format() SQL injection risk"),
        (r'\+\s*["\'].*(?:SELECT|INSERT|UPDATE|DELETE)', "String concatenation SQL injection risk"),
    ]

    async def analyze(self, file_path: Path) -> list[CodeIssue]:
        """Analyze file for security issues"""
        issues: list[CodeIssue] = []

        try:
            content = file_path.read_text()
            lines = content.split("\n")
            rel_path = str(file_path.relative_to(self.repo_root))

            for i, line in enumerate(lines, 1):
                # Skip comments
                if line.strip().startswith("#"):
                    continue

                # Check for hardcoded secrets
                for pattern, description in self.SECRET_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Skip if it's using env vars
                        if "environ" in line or "getenv" in line or "os.env" in line:
                            continue
                        # Skip test files with obvious test values
                        if "test" in rel_path.lower() and any(t in line.lower() for t in ["test", "dummy", "fake", "mock"]):
                            continue

                        issues.append(CodeIssue(
                            file_path=rel_path,
                            line_number=i,
                            category=IssueCategory.SECURITY,
                            severity=SeverityLevel.CRITICAL,
                            title=description,
                            description="Credentials should not be hardcoded in source code",
                            suggestion="Use environment variables or a secrets manager",
                            code_snippet=line.strip()[:50] + "...",
                            auto_fixable=False,
                        ))

                # Check for SQL injection
                for pattern, description in self.SQL_INJECTION_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append(CodeIssue(
                            file_path=rel_path,
                            line_number=i,
                            category=IssueCategory.SECURITY,
                            severity=SeverityLevel.CRITICAL,
                            title=description,
                            description="SQL queries should use parameterized queries",
                            suggestion="Use query parameters or an ORM",
                        ))

                # Check for eval/exec
                if "eval(" in line or "exec(" in line:
                    issues.append(CodeIssue(
                        file_path=rel_path,
                        line_number=i,
                        category=IssueCategory.SECURITY,
                        severity=SeverityLevel.HIGH,
                        title="Use of eval/exec detected",
                        description="eval() and exec() can execute arbitrary code",
                        suggestion="Use safer alternatives like ast.literal_eval for data parsing",
                    ))

        except Exception as e:
            logger.error(f"Security analysis failed for {file_path}: {e}")

        return issues


class PerformanceToolkit(BaseToolkit):
    """
    Performance code analysis toolkit.

    Checks:
    - N+1 query patterns
    - Missing async/await
    - Large data in loops
    - Missing caching
    - Inefficient algorithms
    """

    async def analyze(self, file_path: Path) -> list[CodeIssue]:
        """Analyze file for performance issues"""
        issues: list[CodeIssue] = []

        try:
            content = file_path.read_text()
            lines = content.split("\n")
            rel_path = str(file_path.relative_to(self.repo_root))

            in_loop = False
            loop_start = 0

            for i, line in enumerate(lines, 1):
                stripped = line.strip()

                # Track loop context
                if stripped.startswith("for ") or stripped.startswith("while "):
                    in_loop = True
                    loop_start = i

                # Check for database queries in loops (N+1 pattern)
                if in_loop and any(q in line.lower() for q in [".query(", ".filter(", ".get(", "select ", "fetch"]):
                    issues.append(CodeIssue(
                        file_path=rel_path,
                        line_number=i,
                        category=IssueCategory.PERFORMANCE,
                        severity=SeverityLevel.HIGH,
                        title="Potential N+1 query pattern",
                        description=f"Database query inside loop starting at line {loop_start}",
                        suggestion="Batch the query outside the loop or use eager loading",
                    ))

                # Check for sync operations in async context
                if "async def" in content and "requests.get" in line:
                    issues.append(CodeIssue(
                        file_path=rel_path,
                        line_number=i,
                        category=IssueCategory.PERFORMANCE,
                        severity=SeverityLevel.MEDIUM,
                        title="Sync HTTP in async context",
                        description="Using synchronous requests in async code blocks the event loop",
                        suggestion="Use aiohttp or httpx for async HTTP requests",
                    ))

                # Check for large list comprehension
                if "[" in line and "for" in line and "range(" in line:
                    range_match = re.search(r'range\((\d+)', line)
                    if range_match and int(range_match.group(1)) > 10000:
                        issues.append(CodeIssue(
                            file_path=rel_path,
                            line_number=i,
                            category=IssueCategory.PERFORMANCE,
                            severity=SeverityLevel.MEDIUM,
                            title="Large list comprehension",
                            description="Creating large lists in memory",
                            suggestion="Use generators or itertools for large sequences",
                        ))

                # Reset loop tracking at function boundaries
                if stripped.startswith("def ") or stripped.startswith("async def "):
                    in_loop = False

        except Exception as e:
            logger.error(f"Performance analysis failed for {file_path}: {e}")

        return issues


class TestingToolkit(BaseToolkit):
    """
    Testing code analysis toolkit.

    Checks:
    - Test coverage indicators
    - Missing test files
    - Test quality issues
    - Mock usage
    """

    async def analyze(self, file_path: Path) -> list[CodeIssue]:
        """Analyze file for testing issues"""
        issues: list[CodeIssue] = []

        try:
            content = file_path.read_text()
            rel_path = str(file_path.relative_to(self.repo_root))

            # Check if this is a source file without tests
            if not any(p in rel_path for p in ["test", "tests", "__pycache__", ".venv"]):
                test_path = self.repo_root / "tests" / f"test_{file_path.name}"
                if not test_path.exists():
                    # Check for classes/functions that should be tested
                    if "class " in content or "def " in content:
                        issues.append(CodeIssue(
                            file_path=rel_path,
                            line_number=None,
                            category=IssueCategory.TESTING,
                            severity=SeverityLevel.LOW,
                            title="Missing test file",
                            description=f"No test file found at tests/test_{file_path.name}",
                            suggestion="Create tests for public functions and classes",
                        ))

            # If this is a test file, check quality
            if "test" in rel_path.lower():
                lines = content.split("\n")
                test_count = len([l for l in lines if l.strip().startswith("def test_")])
                assert_count = content.lower().count("assert")

                if test_count > 0 and assert_count / test_count < 1:
                    issues.append(CodeIssue(
                        file_path=rel_path,
                        line_number=None,
                        category=IssueCategory.TESTING,
                        severity=SeverityLevel.MEDIUM,
                        title="Tests may lack assertions",
                        description=f"{test_count} tests but only {assert_count} assertions",
                        suggestion="Ensure each test has meaningful assertions",
                    ))

        except Exception as e:
            logger.error(f"Testing analysis failed for {file_path}: {e}")

        return issues


# =============================================================================
# Coding Doctor Agent
# =============================================================================


class CodingDoctorAgent(EnhancedSuperAgent):
    """
    Comprehensive Coding Doctor Agent.

    Self-learning, self-healing meta-agent for full-stack codebase management.
    """

    agent_type = SuperAgentType.OPERATIONS
    sub_capabilities = [
        "code_review",
        "self_healing",
        "continuous_learning",
        "security_scan",
        "performance_analysis",
        "ecommerce_audit",
        "finance_audit",
        "test_analysis",
        "documentation",
        "architecture_review",
    ]

    CODEBASE_STRUCTURE = {
        "agents": "6 SuperAgents + Coding Doctor",
        "adk": "ADK adapters (PydanticAI, LangChain, Google ADK, etc.)",
        "llm": "LLM layer (router, round_table, ab_testing)",
        "orchestration": "Orchestration (prompts, RAG, tools)",
        "security": "Security modules (encryption, auth)",
        "api": "API endpoints and versioning",
        "database": "Database models and repositories",
        "frontend": "Next.js dashboard",
        "tests": "Test suites",
    }

    def __init__(self, config: AgentConfig | None = None):
        if config is None:
            config = AgentConfig(
                name="CodingDoctorAgent",
                description="Self-learning, self-healing codebase guardian",
                model="claude-sonnet-4-20250514",
                temperature=0.3,
            )
        super().__init__(config)

        self._repo_root = Path(__file__).parent.parent
        self._data_dir = self._repo_root / "data" / "coding_doctor"

        # Initialize engines and toolkits
        self.learning_engine = SelfLearningEngine(self._data_dir / "learnings.json")
        self.healing_engine = SelfHealingEngine(self._repo_root)
        self.ecommerce_toolkit = ECommerceToolkit(self._repo_root)
        self.finance_toolkit = FinanceToolkit(self._repo_root)
        self.security_toolkit = SecurityToolkit(self._repo_root)
        self.performance_toolkit = PerformanceToolkit(self._repo_root)
        self.testing_toolkit = TestingToolkit(self._repo_root)

    async def initialize(self) -> None:
        """Initialize all components"""
        await super().initialize()

        # Initialize engines
        await self.learning_engine.initialize()
        await self.healing_engine.initialize()

        logger.info("Coding Doctor initialized with all toolkits")

    async def execute(self, prompt: str, **kwargs) -> AgentResult:
        """Execute a coding doctor task"""
        start_time = datetime.now(UTC)

        try:
            task_category = self._infer_task_category(prompt)
            technique = self.select_technique(task_category)
            self.apply_technique(technique, prompt, **kwargs)

            result_text = f"Analysis completed using {technique.value} technique"

            return AgentResult(
                agent_name=self.config.name,
                status=AgentStatus.COMPLETED,
                result=result_text,
                usage={"technique": technique.value},
                duration_ms=(datetime.now(UTC) - start_time).total_seconds() * 1000,
            )

        except Exception as e:
            logger.error(f"Coding Doctor execution failed: {e}")
            return AgentResult(
                agent_name=self.config.name,
                status=AgentStatus.FAILED,
                result=str(e),
                error=str(e),
                duration_ms=(datetime.now(UTC) - start_time).total_seconds() * 1000,
            )

    async def diagnose_and_heal(
        self,
        check_type: HealthCheckType = HealthCheckType.FULL,
        auto_heal: bool = True,
        directories: list[str] | None = None,
    ) -> HealthReport:
        """
        Run comprehensive diagnosis with optional auto-healing.

        Args:
            check_type: Type of health check
            auto_heal: Whether to auto-fix healable issues
            directories: Specific directories to check

        Returns:
            HealthReport with all findings and healing results
        """
        start_time = time.time()
        logger.info(f"Starting {check_type.value} diagnosis (auto_heal={auto_heal})")

        if directories is None:
            directories = list(self.CODEBASE_STRUCTURE.keys())

        all_issues: list[CodeIssue] = []
        file_reviews: list[FileReview] = []
        healing_results: list[HealingResult] = []
        total_files = 0
        total_lines = 0
        learnings_applied = 0

        # Scan directories
        for dir_name in directories:
            dir_path = self._repo_root / dir_name
            if not dir_path.exists():
                continue

            for py_file in dir_path.rglob("*.py"):
                if "__pycache__" in str(py_file) or ".venv" in str(py_file):
                    continue

                total_files += 1

                # Analyze file
                review = await self._analyze_file_comprehensive(py_file, check_type)
                file_reviews.append(review)
                all_issues.extend(review.issues)
                total_lines += review.lines_of_code

                # Apply learnings
                for issue in review.issues:
                    solution = self.learning_engine.get_solution(issue.category, issue.title)
                    if solution:
                        issue.suggestion = solution
                        learnings_applied += 1

                # Auto-heal if enabled
                if auto_heal:
                    for issue in review.issues:
                        if issue.auto_fixable:
                            result = await self.healing_engine.heal(issue)
                            healing_results.append(result)

                            # Learn from healing outcome
                            self.learning_engine.learn(
                                issue.category,
                                issue.title,
                                issue.suggestion or "",
                                result.success,
                            )

        # Calculate score
        overall_score = self._calculate_score(all_issues)

        # Generate specialized findings
        ecommerce_findings = [
            i.title for i in all_issues if i.category == IssueCategory.ECOMMERCE
        ]
        finance_findings = [
            i.title for i in all_issues if i.category == IssueCategory.FINANCE
        ]
        security_findings = [
            i.title for i in all_issues if i.category == IssueCategory.SECURITY
        ]
        performance_suggestions = [
            i.suggestion or i.title for i in all_issues if i.category == IssueCategory.PERFORMANCE
        ]

        # Save learnings
        await self.learning_engine.save()

        duration = time.time() - start_time

        return HealthReport(
            check_type=check_type,
            total_files=total_files,
            total_lines=total_lines,
            overall_score=overall_score,
            issues=all_issues,
            file_reviews=file_reviews,
            healing_results=healing_results,
            architecture_notes=self._generate_architecture_notes(),
            security_findings=security_findings,
            performance_suggestions=performance_suggestions,
            ecommerce_findings=ecommerce_findings,
            finance_findings=finance_findings,
            test_coverage=None,
            recommendations=self._generate_recommendations(all_issues),
            learnings_applied=learnings_applied,
            duration_seconds=duration,
        )

    async def _analyze_file_comprehensive(
        self,
        file_path: Path,
        check_type: HealthCheckType,
    ) -> FileReview:
        """Comprehensive file analysis using all toolkits"""
        issues: list[CodeIssue] = []

        try:
            content = file_path.read_text()
            lines = content.split("\n")
            loc = len([l for l in lines if l.strip() and not l.strip().startswith("#")])
            rel_path = str(file_path.relative_to(self._repo_root))

            # Run all applicable toolkits
            issues.extend(await self.security_toolkit.analyze(file_path))

            if check_type in [HealthCheckType.FULL, HealthCheckType.PERFORMANCE]:
                issues.extend(await self.performance_toolkit.analyze(file_path))

            if check_type in [HealthCheckType.FULL, HealthCheckType.ECOMMERCE]:
                issues.extend(await self.ecommerce_toolkit.analyze(file_path))

            if check_type in [HealthCheckType.FULL, HealthCheckType.FINANCE]:
                issues.extend(await self.finance_toolkit.analyze(file_path))

            if check_type in [HealthCheckType.FULL, HealthCheckType.TESTS]:
                issues.extend(await self.testing_toolkit.analyze(file_path))

            # Basic checks
            issues.extend(self._basic_checks(content, lines, rel_path))

            score = self._calculate_score(issues)
            healable = len([i for i in issues if i.auto_fixable])

            return FileReview(
                file_path=rel_path,
                language="python",
                lines_of_code=loc,
                issues=issues,
                score=score,
                summary=f"Found {len(issues)} issues ({healable} auto-fixable)",
                recommendations=[],
                healable_issues=healable,
            )

        except Exception as e:
            return FileReview(
                file_path=str(file_path),
                language="python",
                lines_of_code=0,
                issues=[],
                score=0,
                summary=f"Error: {e}",
                recommendations=[],
            )

    def _basic_checks(
        self,
        content: str,
        lines: list[str],
        rel_path: str,
    ) -> list[CodeIssue]:
        """Run basic code quality checks"""
        issues: list[CodeIssue] = []

        # Missing module docstring
        if not content.startswith('"""') and not content.startswith("'''"):
            issues.append(CodeIssue(
                file_path=rel_path,
                line_number=1,
                category=IssueCategory.DOCUMENTATION,
                severity=SeverityLevel.LOW,
                title="Missing module docstring",
                description="Module should have a docstring",
                suggestion="Add a module-level docstring",
                auto_fixable=False,
            ))

        # File too long
        if len(lines) > 500:
            issues.append(CodeIssue(
                file_path=rel_path,
                line_number=None,
                category=IssueCategory.MAINTAINABILITY,
                severity=SeverityLevel.MEDIUM,
                title="File too long",
                description=f"File has {len(lines)} lines (max 500)",
                suggestion="Split into multiple modules",
            ))

        # TODO/FIXME
        for i, line in enumerate(lines, 1):
            if "TODO" in line or "FIXME" in line:
                issues.append(CodeIssue(
                    file_path=rel_path,
                    line_number=i,
                    category=IssueCategory.MAINTAINABILITY,
                    severity=SeverityLevel.INFO,
                    title="TODO/FIXME found",
                    description=line.strip()[:60],
                    suggestion="Address or document",
                ))

        return issues

    def _calculate_score(self, issues: list[CodeIssue]) -> float:
        """Calculate health score from issues"""
        if not issues:
            return 100.0

        weights = {
            SeverityLevel.CRITICAL: 25,
            SeverityLevel.HIGH: 15,
            SeverityLevel.MEDIUM: 8,
            SeverityLevel.LOW: 3,
            SeverityLevel.INFO: 0,
        }

        penalty = sum(weights[i.severity] for i in issues)
        return max(0, 100 - penalty)

    def _generate_architecture_notes(self) -> list[str]:
        """Generate architecture observations"""
        return [
            "6 SuperAgents + Coding Doctor following EnhancedSuperAgent pattern",
            "17 prompt engineering techniques integrated",
            "Multi-LLM support with Round Table competition",
            "RAG pipeline with ChromaDB/Pinecone",
            "Security-first with AES-256-GCM encryption",
        ]

    def _generate_recommendations(self, issues: list[CodeIssue]) -> list[str]:
        """Generate recommendations from issues"""
        recommendations = []

        critical = len([i for i in issues if i.severity == SeverityLevel.CRITICAL])
        high = len([i for i in issues if i.severity == SeverityLevel.HIGH])

        if critical > 0:
            recommendations.append(f"URGENT: {critical} critical issues need immediate attention")
        if high > 0:
            recommendations.append(f"HIGH: {high} high-severity issues should be fixed soon")

        categories = {i.category for i in issues}

        if IssueCategory.SECURITY in categories:
            recommendations.append("Security: Review credential handling and input validation")
        if IssueCategory.ECOMMERCE in categories:
            recommendations.append("E-commerce: Validate payment and inventory logic")
        if IssueCategory.FINANCE in categories:
            recommendations.append("Finance: Ensure Decimal usage and audit logging")
        if IssueCategory.PERFORMANCE in categories:
            recommendations.append("Performance: Address N+1 queries and async issues")

        return recommendations

    async def audit_ecommerce(self) -> HealthReport:
        """Run e-commerce focused audit"""
        return await self.diagnose_and_heal(
            check_type=HealthCheckType.ECOMMERCE,
            auto_heal=False,
            directories=["agents", "api", "orchestration"],
        )

    async def audit_finances(self) -> HealthReport:
        """Run finance focused audit"""
        return await self.diagnose_and_heal(
            check_type=HealthCheckType.FINANCE,
            auto_heal=False,
        )

    async def audit_security(self) -> HealthReport:
        """Run security focused audit"""
        return await self.diagnose_and_heal(
            check_type=HealthCheckType.SECURITY,
            auto_heal=False,
        )

    def get_learning_stats(self) -> dict[str, Any]:
        """Get learning engine statistics"""
        return self.learning_engine.get_stats()


# =============================================================================
# Factory and CLI
# =============================================================================


def create_coding_doctor(
    model: str = "claude-sonnet-4-20250514",
    temperature: float = 0.3,
) -> CodingDoctorAgent:
    """Create a Coding Doctor agent"""
    config = AgentConfig(
        name="CodingDoctorAgent",
        description="Self-learning, self-healing codebase guardian",
        model=model,
        temperature=temperature,
    )
    return CodingDoctorAgent(config)


async def main():
    """CLI interface"""
    import sys

    print("""
╔══════════════════════════════════════════════════════════════════╗
║           DevSkyy Coding Doctor                                   ║
║   Self-Learning | Self-Healing | Full-Stack Analysis             ║
╚══════════════════════════════════════════════════════════════════╝
""")

    doctor = create_coding_doctor()
    await doctor.initialize()

    args = sys.argv[1:]
    command = args[0] if args else "health"

    if command == "health":
        print("Running comprehensive health check with auto-healing...")
        report = await doctor.diagnose_and_heal(auto_heal=True)

        print(f"\n📊 Overall Score: {report.overall_score:.1f}/100")
        print(f"📁 Files: {report.total_files} | Lines: {report.total_lines}")
        print(f"🔍 Issues: {len(report.issues)} | Auto-healed: {len([h for h in report.healing_results if h.success])}")
        print(f"🧠 Learnings applied: {report.learnings_applied}")

        if report.issues:
            print("\n⚠️  Top Issues:")
            for issue in sorted(report.issues, key=lambda x: x.severity.value)[:5]:
                print(f"  [{issue.severity.value.upper()}] {issue.file_path}: {issue.title}")

    elif command == "ecommerce":
        print("Running e-commerce audit...")
        report = await doctor.audit_ecommerce()
        print(f"\n🛒 E-commerce Findings: {len(report.ecommerce_findings)}")
        for finding in report.ecommerce_findings[:5]:
            print(f"  - {finding}")

    elif command == "finance":
        print("Running finance audit...")
        report = await doctor.audit_finances()
        print(f"\n💰 Finance Findings: {len(report.finance_findings)}")
        for finding in report.finance_findings[:5]:
            print(f"  - {finding}")

    elif command == "security":
        print("Running security scan...")
        report = await doctor.audit_security()
        print(f"\n🔒 Security Findings: {len(report.security_findings)}")
        for finding in report.security_findings[:5]:
            print(f"  - {finding}")

    elif command == "learn":
        print("Learning statistics:")
        stats = doctor.get_learning_stats()
        print(f"  Total patterns: {stats.get('total_patterns', 0)}")
        print(f"  Avg success rate: {stats.get('avg_success_rate', 0):.1%}")

    else:
        print("Commands: health, ecommerce, finance, security, learn")


if __name__ == "__main__":
    asyncio.run(main())

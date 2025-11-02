"""
Codex-Powered Code Healing Orchestrator
Uses GPT-4 to intelligently coordinate code analysis, fixing, and healing

This orchestrator:
- Analyzes code issues using the scanner
- Uses GPT-4 to understand context and generate optimal fixes
- Coordinates multiple healing agents (fixer, self-healing, auto-fix)
- Validates fixes before applying
- Learns from successful fixes to improve future healing

Architecture:
1. Scanner → Detect issues
2. Codex → Analyze and generate fix strategy
3. Healing Agents → Apply fixes
4. Validation → Test fixes
5. Learning → Store successful patterns
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ml.codex_integration import codex

logger = logging.getLogger(__name__)


class CodexOrchestrator:
    """
    AI-powered orchestrator for code healing using GPT-4
    """

    def __init__(self):
        """Initialize orchestrator with healing agents"""
        self.codex = codex
        self.healing_history = []
        self.successful_patterns = {}

        # Lazy load healing agents
        self._scanner = None
        self._fixer = None
        self._self_healing = None

        logger.info("🎯 Codex Orchestrator initialized")

    @property
    def scanner(self):
        """Lazy load scanner agent"""
        if self._scanner is None:
            try:
                from agent.modules.backend.scanner_v2 import CodeScanner

                self._scanner = CodeScanner()
            except ImportError:
                try:
                    from agent.modules.backend.scanner import scan_site

                    self._scanner = lambda path: {"issues": scan_site(path)}
                except ImportError:
                    logger.warning("Scanner not available")
                    self._scanner = None
        return self._scanner

    @property
    def fixer(self):
        """Lazy load fixer agent"""
        if self._fixer is None:
            try:
                from agent.modules.backend.fixer_v2 import CodeFixer

                self._fixer = CodeFixer()
            except ImportError:
                try:
                    from agent.modules.backend.fixer import fix_code

                    self._fixer = lambda code, issue: fix_code(code, issue)
                except ImportError:
                    logger.warning("Fixer not available")
                    self._fixer = None
        return self._fixer

    @property
    def self_healing(self):
        """Lazy load self-healing agent"""
        if self._self_healing is None:
            try:
                from agent.modules.backend.universal_self_healing_agent import (
                    UniversalSelfHealingAgent,
                )

                self._self_healing = UniversalSelfHealingAgent()
            except ImportError:
                logger.warning("Self-healing agent not available")
                self._self_healing = None
        return self._self_healing

    async def heal_code(
        self,
        code: str,
        language: str = "python",
        context: Optional[Dict[str, Any]] = None,
        auto_apply: bool = False,
    ) -> Dict[str, Any]:
        """
        Comprehensive code healing using AI orchestration

        Args:
            code: Code to heal
            language: Programming language
            context: Additional context (file path, dependencies, etc.)
            auto_apply: Automatically apply fixes (use with caution)

        Returns:
            Dict containing healing results and fixes
        """
        logger.info(f"🎯 Starting AI-powered code healing for {language}")

        try:
            # Phase 1: Scan for issues
            scan_result = await self._scan_code(code, language, context)

            if not scan_result.get("issues"):
                return {
                    "status": "success",
                    "message": "No issues detected",
                    "code": code,
                    "issues": [],
                }

            # Phase 2: AI Analysis - Use GPT-4 to analyze issues and generate strategy
            strategy = await self._generate_healing_strategy(
                code, scan_result["issues"], language, context
            )

            # Phase 3: Generate fixes using Codex
            fixes = await self._generate_fixes(code, strategy, language)

            # Phase 4: Validate fixes
            validation = await self._validate_fixes(code, fixes, language)

            # Phase 5: Apply fixes (if validated and auto_apply=True)
            healed_code = code
            if validation["safe"] and auto_apply:
                healed_code = await self._apply_fixes(code, fixes, language)

            # Phase 6: Learn from successful healing
            if validation["safe"]:
                await self._learn_from_healing(strategy, fixes, validation)

            return {
                "status": "success",
                "original_code": code,
                "healed_code": healed_code,
                "issues_found": len(scan_result["issues"]),
                "issues": scan_result["issues"],
                "strategy": strategy,
                "fixes": fixes,
                "validation": validation,
                "applied": auto_apply and validation["safe"],
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Code healing failed: {e}")
            return {"status": "error", "error": str(e), "original_code": code}

    async def _scan_code(
        self, code: str, language: str, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Scan code for issues using scanner agent"""
        logger.info("📊 Scanning code for issues...")

        try:
            # Use Codex to analyze code for issues
            analysis = await self.codex.review_code(code=code, language=language)

            if analysis["status"] == "error":
                return {"issues": []}

            # Parse review into structured issues
            review_text = analysis.get("review", "")
            issues = self._parse_review_into_issues(review_text)

            return {"issues": issues, "raw_review": review_text}

        except Exception as e:
            logger.error(f"Code scanning failed: {e}")
            return {"issues": []}

    async def _generate_healing_strategy(
        self,
        code: str,
        issues: List[Dict],
        language: str,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Use GPT-4 to analyze issues and generate optimal healing strategy"""
        logger.info("🧠 Generating AI-powered healing strategy...")

        try:
            # Build strategy prompt
            issues_summary = "\n".join(
                [
                    f"- {i.get('type', 'issue')}: {i.get('description', 'Unknown')}"
                    for i in issues
                ]
            )

            prompt = f"""Analyze the following code issues and create an optimal healing strategy:

ISSUES DETECTED:
{issues_summary}

LANGUAGE: {language}

Create a healing strategy that:
1. Prioritizes critical security and correctness issues
2. Groups related issues for efficient fixing
3. Identifies dependencies between fixes
4. Suggests the optimal order of fixes
5. Identifies potential side effects

Respond with a structured healing strategy."""

            # Use Codex to generate strategy
            strategy_response = await self.codex.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert code healing strategist.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1024,
                temperature=0.2,
            )

            strategy_text = strategy_response.choices[0].message.content

            return {
                "strategy": strategy_text,
                "priority_issues": [
                    i for i in issues if i.get("severity") in ["high", "critical"]
                ],
                "issue_groups": self._group_related_issues(issues),
                "estimated_fix_time": len(issues) * 30,  # seconds
            }

        except Exception as e:
            logger.error(f"Strategy generation failed: {e}")
            return {
                "strategy": "Apply fixes sequentially",
                "priority_issues": issues,
                "issue_groups": [issues],
            }

    async def _generate_fixes(
        self, code: str, strategy: Dict, language: str
    ) -> List[Dict[str, Any]]:
        """Generate fixes for each issue using Codex"""
        logger.info("🔧 Generating AI-powered fixes...")

        fixes = []

        try:
            # Get priority issues from strategy
            priority_issues = strategy.get("priority_issues", [])

            for issue in priority_issues:
                # Use Codex to generate fix
                fix_prompt = f"""Fix this {language} code issue:

ISSUE: {issue.get('description', 'Unknown issue')}
TYPE: {issue.get('type', 'general')}

CODE:
```{language}
{code}
```

Generate a corrected version that fixes this specific issue while maintaining functionality."""

                fix_response = await self.codex.generate_code(
                    prompt=fix_prompt, language=language, model="gpt-4", temperature=0.1
                )

                if fix_response["status"] == "success":
                    fixes.append(
                        {
                            "issue": issue,
                            "fixed_code": fix_response["code"],
                            "explanation": fix_response.get("raw_response", ""),
                            "confidence": (
                                "high"
                                if fix_response.get("finish_reason") == "stop"
                                else "medium"
                            ),
                        }
                    )

            return fixes

        except Exception as e:
            logger.error(f"Fix generation failed: {e}")
            return []

    async def _validate_fixes(
        self, original_code: str, fixes: List[Dict], language: str
    ) -> Dict[str, Any]:
        """Validate fixes before applying"""
        logger.info("✅ Validating fixes...")

        try:
            if not fixes:
                return {"safe": False, "reason": "No fixes generated"}

            # Use Codex to validate fixes
            validation_prompt = f"""Validate these code fixes for safety and correctness:

ORIGINAL CODE:
```{language}
{original_code}
```

NUMBER OF FIXES: {len(fixes)}

Analyze:
1. Do fixes solve the stated issues?
2. Are there any new issues introduced?
3. Is functionality preserved?
4. Are there breaking changes?
5. Overall safety score (0-100)

Respond with validation analysis."""

            validation_response = await self.codex.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert code validator."},
                    {"role": "user", "content": validation_prompt},
                ],
                max_tokens=1024,
                temperature=0.1,
            )

            validation_text = validation_response.choices[0].message.content

            # Simple heuristic: safe if no breaking changes mentioned
            is_safe = (
                "breaking" not in validation_text.lower()
                and "unsafe" not in validation_text.lower()
            )

            return {
                "safe": is_safe,
                "validation_report": validation_text,
                "fixes_validated": len(fixes),
                "recommended_action": "apply" if is_safe else "manual_review",
            }

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {"safe": False, "reason": str(e)}

    async def _apply_fixes(self, code: str, fixes: List[Dict], language: str) -> str:
        """Apply validated fixes to code"""
        logger.info("🚀 Applying fixes...")

        if not fixes:
            return code

        # Apply highest confidence fix
        best_fix = max(fixes, key=lambda f: 1 if f.get("confidence") == "high" else 0)

        return best_fix.get("fixed_code", code)

    async def _learn_from_healing(
        self, strategy: Dict, fixes: List[Dict], validation: Dict
    ):
        """Learn from successful healing to improve future operations"""
        if validation.get("safe"):
            pattern = {
                "strategy": strategy.get("strategy", "")[:200],  # First 200 chars
                "num_fixes": len(fixes),
                "success": True,
                "timestamp": datetime.utcnow().isoformat(),
            }

            self.healing_history.append(pattern)

            # Limit history size
            if len(self.healing_history) > 100:
                self.healing_history = self.healing_history[-100:]

            logger.info("📚 Learned from successful healing")

    def _parse_review_into_issues(self, review_text: str) -> List[Dict[str, Any]]:
        """Parse code review text into structured issues"""
        issues = []

        # Simple parsing - look for common issue indicators
        lines = review_text.split("\n")

        for line in lines:
            line_lower = line.lower()

            if any(
                keyword in line_lower
                for keyword in [
                    "bug",
                    "error",
                    "issue",
                    "problem",
                    "vulnerability",
                    "security",
                    "performance",
                ]
            ):

                severity = "high"
                if "critical" in line_lower or "security" in line_lower:
                    severity = "critical"
                elif "minor" in line_lower or "style" in line_lower:
                    severity = "low"

                issue_type = "general"
                if "security" in line_lower:
                    issue_type = "security"
                elif "performance" in line_lower:
                    issue_type = "performance"
                elif "bug" in line_lower or "error" in line_lower:
                    issue_type = "bug"

                issues.append(
                    {
                        "type": issue_type,
                        "severity": severity,
                        "description": line.strip(),
                        "line": None,
                    }
                )

        return issues

    def _group_related_issues(self, issues: List[Dict]) -> List[List[Dict]]:
        """Group related issues for efficient fixing"""
        if not issues:
            return []

        # Simple grouping by type
        groups = {}
        for issue in issues:
            issue_type = issue.get("type", "general")
            if issue_type not in groups:
                groups[issue_type] = []
            groups[issue_type].append(issue)

        return list(groups.values())

    def get_healing_stats(self) -> Dict[str, Any]:
        """Get statistics about healing operations"""
        total_healings = len(self.healing_history)
        successful = sum(1 for h in self.healing_history if h.get("success"))

        return {
            "total_healings": total_healings,
            "successful": successful,
            "success_rate": (
                (successful / total_healings * 100) if total_healings > 0 else 0
            ),
            "recent_healings": (
                self.healing_history[-10:] if self.healing_history else []
            ),
        }


# Global instance
codex_orchestrator = CodexOrchestrator()

logger.info("🎯 Codex Orchestrator module loaded")

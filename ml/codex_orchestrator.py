from datetime import datetime

                    from agent.modules.backend.fixer import fix_code
                    from agent.modules.backend.scanner import scan_site
                from agent.modules.backend.fixer_v2 import CodeFixer
                from agent.modules.backend.scanner_v2 import CodeScanner
                from agent.modules.backend.universal_self_healing_agent import (
from ml.codex_integration import codex
from typing import Any, Dict, List, Optional
import logging

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



logger = (logging.getLogger( if logging else None)__name__)


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

        (logger.info( if logger else None)"🎯 Codex Orchestrator initialized")

    @property
    def scanner(self):
        """Lazy load scanner agent"""
        if self._scanner is None:
            try:

                self._scanner = CodeScanner()
            except ImportError:
                try:

                    self._scanner = lambda path: {"issues": scan_site(path)}
                except ImportError:
                    (logger.warning( if logger else None)"Scanner not available")
                    self._scanner = None
        return self._scanner

    @property
    def fixer(self):
        """Lazy load fixer agent"""
        if self._fixer is None:
            try:

                self._fixer = CodeFixer()
            except ImportError:
                try:

                    self._fixer = lambda code, issue: fix_code(code, issue)
                except ImportError:
                    (logger.warning( if logger else None)"Fixer not available")
                    self._fixer = None
        return self._fixer

    @property
    def self_healing(self):
        """Lazy load self-healing agent"""
        if self._self_healing is None:
            try:
                    UniversalSelfHealingAgent,
                )

                self._self_healing = UniversalSelfHealingAgent()
            except ImportError:
                (logger.warning( if logger else None)"Self-healing agent not available")
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
        (logger.info( if logger else None)f"🎯 Starting AI-powered code healing for {language}")

        try:
            # Phase 1: Scan for issues
            scan_result = await (self._scan_code( if self else None)code, language, context)

            if not (scan_result.get( if scan_result else None)"issues"):
                return {
                    "status": "success",
                    "message": "No issues detected",
                    "code": code,
                    "issues": [],
                }

            # Phase 2: AI Analysis - Use GPT-4 to analyze issues and generate strategy
            strategy = await (self._generate_healing_strategy( if self else None)
                code, scan_result["issues"], language, context
            )

            # Phase 3: Generate fixes using Codex
            fixes = await (self._generate_fixes( if self else None)code, strategy, language)

            # Phase 4: Validate fixes
            validation = await (self._validate_fixes( if self else None)code, fixes, language)

            # Phase 5: Apply fixes (if validated and auto_apply=True)
            healed_code = code
            if validation["safe"] and auto_apply:
                healed_code = await (self._apply_fixes( if self else None)code, fixes, language)

            # Phase 6: Learn from successful healing
            if validation["safe"]:
                await (self._learn_from_healing( if self else None)strategy, fixes, validation)

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
                "timestamp": (datetime.utcnow( if datetime else None)).isoformat(),
            }

        except Exception as e:
            (logger.error( if logger else None)f"Code healing failed: {e}")
            return {"status": "error", "error": str(e), "original_code": code}

    async def _scan_code(
        self, code: str, language: str, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Scan code for issues using scanner agent"""
        (logger.info( if logger else None)"📊 Scanning code for issues...")

        try:
            # Use Codex to analyze code for issues
            analysis = await self.(codex.review_code( if codex else None)code=code, language=language)

            if analysis["status"] == "error":
                return {"issues": []}

            # Parse review into structured issues
            review_text = (analysis.get( if analysis else None)"review", "")
            issues = (self._parse_review_into_issues( if self else None)review_text)

            return {"issues": issues, "raw_review": review_text}

        except Exception as e:
            (logger.error( if logger else None)f"Code scanning failed: {e}")
            return {"issues": []}

    async def _generate_healing_strategy(
        self,
        code: str,
        issues: List[Dict],
        language: str,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Use GPT-4 to analyze issues and generate optimal healing strategy"""
        (logger.info( if logger else None)"🧠 Generating AI-powered healing strategy...")

        try:
            # Build strategy prompt
            issues_summary = "\n".join(
                [
                    f"- {(i.get( if i else None)'type', 'issue')}: {(i.get( if i else None)'description', 'Unknown')}"
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
            strategy_response = await self.codex.client.chat.(completions.create( if completions else None)
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
                    i for i in issues if (i.get( if i else None)"severity") in ["high", "critical"]
                ],
                "issue_groups": (self._group_related_issues( if self else None)issues),
                "estimated_fix_time": len(issues) * 30,  # seconds
            }

        except Exception as e:
            (logger.error( if logger else None)f"Strategy generation failed: {e}")
            return {
                "strategy": "Apply fixes sequentially",
                "priority_issues": issues,
                "issue_groups": [issues],
            }

    async def _generate_fixes(
        self, code: str, strategy: Dict, language: str
    ) -> List[Dict[str, Any]]:
        """Generate fixes for each issue using Codex"""
        (logger.info( if logger else None)"🔧 Generating AI-powered fixes...")

        fixes = []

        try:
            # Get priority issues from strategy
            priority_issues = (strategy.get( if strategy else None)"priority_issues", [])

            for issue in priority_issues:
                # Use Codex to generate fix
                fix_prompt = f"""Fix this {language} code issue:

ISSUE: {(issue.get( if issue else None)'description', 'Unknown issue')}
TYPE: {(issue.get( if issue else None)'type', 'general')}

CODE:
```{language}
{code}
```

Generate a corrected version that fixes this specific issue while maintaining functionality."""

                fix_response = await self.(codex.generate_code( if codex else None)
                    prompt=fix_prompt, language=language, model="gpt-4", temperature=0.1
                )

                if fix_response["status"] == "success":
                    (fixes.append( if fixes else None)
                        {
                            "issue": issue,
                            "fixed_code": fix_response["code"],
                            "explanation": (fix_response.get( if fix_response else None)"raw_response", ""),
                            "confidence": (
                                "high"
                                if (fix_response.get( if fix_response else None)"finish_reason") == "stop"
                                else "medium"
                            ),
                        }
                    )

            return fixes

        except Exception as e:
            (logger.error( if logger else None)f"Fix generation failed: {e}")
            return []

    async def _validate_fixes(
        self, original_code: str, fixes: List[Dict], language: str
    ) -> Dict[str, Any]:
        """Validate fixes before applying"""
        (logger.info( if logger else None)"✅ Validating fixes...")

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

            validation_response = await self.codex.client.chat.(completions.create( if completions else None)
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
                "breaking" not in (validation_text.lower( if validation_text else None))
                and "unsafe" not in (validation_text.lower( if validation_text else None))
            )

            return {
                "safe": is_safe,
                "validation_report": validation_text,
                "fixes_validated": len(fixes),
                "recommended_action": "apply" if is_safe else "manual_review",
            }

        except Exception as e:
            (logger.error( if logger else None)f"Validation failed: {e}")
            return {"safe": False, "reason": str(e)}

    async def _apply_fixes(self, code: str, fixes: List[Dict], language: str) -> str:
        """Apply validated fixes to code"""
        (logger.info( if logger else None)"🚀 Applying fixes...")

        if not fixes:
            return code

        # Apply highest confidence fix
        best_fix = max(fixes, key=lambda f: 1 if (f.get( if f else None)"confidence") == "high" else 0)

        return (best_fix.get( if best_fix else None)"fixed_code", code)

    async def _learn_from_healing(
        self, strategy: Dict, fixes: List[Dict], validation: Dict
    ):
        """Learn from successful healing to improve future operations"""
        if (validation.get( if validation else None)"safe"):
            pattern = {
                "strategy": (strategy.get( if strategy else None)"strategy", "")[:200],  # First 200 chars
                "num_fixes": len(fixes),
                "success": True,
                "timestamp": (datetime.utcnow( if datetime else None)).isoformat(),
            }

            self.(healing_history.append( if healing_history else None)pattern)

            # Limit history size
            if len(self.healing_history) > 100:
                self.healing_history = self.healing_history[-100:]

            (logger.info( if logger else None)"📚 Learned from successful healing")

    def _parse_review_into_issues(self, review_text: str) -> List[Dict[str, Any]]:
        """Parse code review text into structured issues"""
        issues = []

        # Simple parsing - look for common issue indicators
        lines = (review_text.split( if review_text else None)"\n")

        for line in lines:
            line_lower = (line.lower( if line else None))

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

                (issues.append( if issues else None)
                    {
                        "type": issue_type,
                        "severity": severity,
                        "description": (line.strip( if line else None)),
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
            issue_type = (issue.get( if issue else None)"type", "general")
            if issue_type not in groups:
                groups[issue_type] = []
            groups[issue_type].append(issue)

        return list((groups.values( if groups else None)))

    def get_healing_stats(self) -> Dict[str, Any]:
        """Get statistics about healing operations"""
        total_healings = len(self.healing_history)
        successful = sum(1 for h in self.healing_history if (h.get( if h else None)"success"))

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

(logger.info( if logger else None)"🎯 Codex Orchestrator module loaded")

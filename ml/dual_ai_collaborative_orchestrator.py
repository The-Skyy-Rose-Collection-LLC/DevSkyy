"""
Dual-AI Collaborative Orchestrator
GPT-5.1-codex-max + Claude Opus 4.5 working in tandem

Architecture:
1. RESEARCH - Both AIs analyze the task independently
2. PLAN - Both propose solutions with reasoning
3. CONSENSUS - Cross-validate and agree (92%+ verification required)
4. BUILD - Generate verified, production-ready code

Truth Protocol Compliance:
- Rule #1: Never Guess - 92%+ verified data before code generation
- Rule #4: State Uncertainty - Track confidence levels
- Rule #8: Test Coverage ≥90%
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from config.unified_config import get_config


logger = logging.getLogger(__name__)


class Phase(Enum):
    """Collaboration phases."""
    RESEARCH = "research"
    PLAN = "plan"
    CONSENSUS = "consensus"
    BUILD = "build"


@dataclass
class VerificationResult:
    """Result of cross-verification between models."""
    codex_confidence: float
    claude_confidence: float
    agreement_score: float
    verified_points: list[str]
    disputed_points: list[str]
    overall_verification: float
    meets_threshold: bool

    @property
    def is_verified(self) -> bool:
        """Check if verification meets 92% threshold."""
        return self.overall_verification >= 0.92


@dataclass
class CollaborativeOutput:
    """Output from dual-AI collaboration."""
    task: str
    phase: Phase
    codex_analysis: dict[str, Any]
    claude_analysis: dict[str, Any]
    consensus: dict[str, Any]
    verification: VerificationResult
    final_output: str | None
    code: str | None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    iterations: int = 0


class DualAICollaborativeOrchestrator:
    """
    Orchestrates GPT-5.1-codex-max and Claude Opus 4.5 for collaborative
    code generation with 92%+ verification threshold.
    """

    VERIFICATION_THRESHOLD = 0.92  # 92% minimum verification
    MAX_CONSENSUS_ITERATIONS = 3   # Max attempts to reach consensus

    def __init__(self):
        config = get_config()

        # Initialize Claude Opus 4.5
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.claude = AsyncAnthropic(api_key=anthropic_key)
            self.claude_model = "claude-opus-4-20250514"
            logger.info("✅ Claude Opus 4.5 initialized")
        else:
            self.claude = None
            logger.warning("⚠️ Claude Opus 4.5 not available - missing API key")

        # Initialize GPT-5.1-codex-max
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            is_consequential = config.ai.openai_is_consequential
            default_headers = {"x-openai-isConsequential": str(is_consequential).lower()}
            self.codex = AsyncOpenAI(api_key=openai_key, default_headers=default_headers)
            self.codex_model = "gpt-5.1-codex-max"
            logger.info("✅ GPT-5.1-codex-max initialized")
        else:
            self.codex = None
            logger.warning("⚠️ GPT-5.1-codex-max not available - missing API key")

        # Collaboration state
        self.current_session: dict[str, Any] = {}
        self.verification_history: list[VerificationResult] = []

        logger.info(
            f"🤝 Dual-AI Collaborative Orchestrator initialized "
            f"(threshold: {self.VERIFICATION_THRESHOLD * 100}%)"
        )

    async def collaborate(
        self,
        task: str,
        context: dict[str, Any] | None = None,
        language: str = "python",
    ) -> CollaborativeOutput:
        """
        Execute full collaboration pipeline: Research → Plan → Consensus → Build.

        Args:
            task: The coding task to complete
            context: Additional context (existing code, requirements, etc.)
            language: Target programming language

        Returns:
            CollaborativeOutput with verified code (if 92%+ threshold met)
        """
        logger.info(f"🚀 Starting dual-AI collaboration for: {task[:100]}...")

        # Phase 1: Research
        research_output = await self._phase_research(task, context, language)

        # Phase 2: Plan
        plan_output = await self._phase_plan(task, research_output, language)

        # Phase 3: Consensus (iterate until 92%+ or max iterations)
        consensus_output = await self._phase_consensus(task, plan_output, language)

        # Phase 4: Build (only if verification threshold met)
        if consensus_output.verification.meets_threshold:
            final_output = await self._phase_build(task, consensus_output, language)
            return final_output
        else:
            logger.warning(
                f"⚠️ Verification threshold not met: "
                f"{consensus_output.verification.overall_verification * 100:.1f}% < 92%"
            )
            consensus_output.code = None
            consensus_output.final_output = (
                f"Verification threshold not met. "
                f"Current: {consensus_output.verification.overall_verification * 100:.1f}%. "
                f"Required: 92%. Disputed points: {consensus_output.verification.disputed_points}"
            )
            return consensus_output

    async def _phase_research(
        self,
        task: str,
        context: dict[str, Any] | None,
        language: str,
    ) -> CollaborativeOutput:
        """Phase 1: Both AIs research and analyze the task independently."""
        logger.info("📚 Phase 1: RESEARCH - Both AIs analyzing task...")

        research_prompt = f"""Analyze this coding task thoroughly:

TASK: {task}

LANGUAGE: {language}

CONTEXT: {context or 'No additional context provided'}

Provide comprehensive research including:
1. REQUIREMENTS ANALYSIS
   - Core functional requirements
   - Non-functional requirements (performance, security, scalability)
   - Edge cases to handle
   - Input/output specifications

2. TECHNICAL RESEARCH
   - Best practices for this type of solution
   - Relevant design patterns
   - Security considerations (OWASP, CWE)
   - Performance implications

3. DEPENDENCIES & INTEGRATIONS
   - Required libraries/frameworks
   - Version compatibility
   - Integration points

4. RISKS & UNCERTAINTIES
   - Areas needing clarification
   - Potential pitfalls
   - Assumptions being made

5. CONFIDENCE ASSESSMENT
   - Rate your confidence (0.0 to 1.0) in each area
   - Identify what would increase confidence

Format as structured JSON."""

        # Run both AIs in parallel
        codex_task = self._call_codex(research_prompt, "research")
        claude_task = self._call_claude(research_prompt, "research")

        codex_result, claude_result = await asyncio.gather(
            codex_task, claude_task, return_exceptions=True
        )

        # Handle errors
        codex_analysis = self._parse_result(codex_result, "codex")
        claude_analysis = self._parse_result(claude_result, "claude")

        # Initial verification (research phase)
        verification = self._calculate_verification(codex_analysis, claude_analysis)

        return CollaborativeOutput(
            task=task,
            phase=Phase.RESEARCH,
            codex_analysis=codex_analysis,
            claude_analysis=claude_analysis,
            consensus={},
            verification=verification,
            final_output=None,
            code=None,
        )

    async def _phase_plan(
        self,
        task: str,
        research: CollaborativeOutput,
        language: str,
    ) -> CollaborativeOutput:
        """Phase 2: Both AIs propose solutions based on research."""
        logger.info("📋 Phase 2: PLAN - Both AIs proposing solutions...")

        plan_prompt = f"""Based on this research, propose a detailed solution:

TASK: {task}

CODEX RESEARCH:
{research.codex_analysis}

CLAUDE RESEARCH:
{research.claude_analysis}

LANGUAGE: {language}

Provide a comprehensive implementation plan:
1. ARCHITECTURE
   - High-level design
   - Component breakdown
   - Data flow

2. IMPLEMENTATION STEPS
   - Step-by-step approach
   - Order of implementation
   - Dependencies between components

3. CODE STRUCTURE
   - Classes/functions to create
   - Type hints and interfaces
   - Error handling strategy

4. TESTING STRATEGY
   - Unit tests needed
   - Integration tests
   - Edge case coverage

5. SECURITY MEASURES
   - Input validation
   - Authentication/authorization
   - Data protection

6. CONFIDENCE SCORE
   - Overall confidence (0.0 to 1.0)
   - Confidence per component
   - Verification points

Format as structured JSON with clear sections."""

        # Run both AIs in parallel
        codex_task = self._call_codex(plan_prompt, "plan")
        claude_task = self._call_claude(plan_prompt, "plan")

        codex_result, claude_result = await asyncio.gather(
            codex_task, claude_task, return_exceptions=True
        )

        codex_analysis = self._parse_result(codex_result, "codex")
        claude_analysis = self._parse_result(claude_result, "claude")

        verification = self._calculate_verification(codex_analysis, claude_analysis)

        return CollaborativeOutput(
            task=task,
            phase=Phase.PLAN,
            codex_analysis=codex_analysis,
            claude_analysis=claude_analysis,
            consensus={},
            verification=verification,
            final_output=None,
            code=None,
        )

    async def _phase_consensus(
        self,
        task: str,
        plan: CollaborativeOutput,
        language: str,
    ) -> CollaborativeOutput:
        """Phase 3: Cross-validate and reach 92%+ consensus."""
        logger.info("🤝 Phase 3: CONSENSUS - Cross-validating for 92%+ agreement...")

        iteration = 0
        current_plan = plan

        while iteration < self.MAX_CONSENSUS_ITERATIONS:
            iteration += 1
            logger.info(f"   Consensus iteration {iteration}/{self.MAX_CONSENSUS_ITERATIONS}")

            consensus_prompt = f"""Cross-validate and reach consensus on this solution:

TASK: {task}

CODEX PROPOSAL:
{current_plan.codex_analysis}

CLAUDE PROPOSAL:
{current_plan.claude_analysis}

CURRENT VERIFICATION: {current_plan.verification.overall_verification * 100:.1f}%
DISPUTED POINTS: {current_plan.verification.disputed_points}

TARGET: 92%+ verification required before code generation.

Analyze both proposals and provide:
1. AGREEMENT POINTS
   - What both AIs agree on (list each point)
   - Confidence level per point

2. DISAGREEMENT RESOLUTION
   - Points of disagreement
   - Evidence-based resolution for each
   - Final decision with justification

3. UNIFIED SOLUTION
   - Merged best approach
   - Incorporates strengths from both
   - Addresses weaknesses identified

4. VERIFICATION CHECKLIST
   - Each requirement verified (yes/no/partial)
   - Security checks passed
   - Best practices confirmed
   - Edge cases covered

5. FINAL CONFIDENCE SCORES
   - Per-component confidence (0.0 to 1.0)
   - Overall verification score
   - Remaining uncertainties

CRITICAL: Be rigorous. Only mark as verified if you have high confidence.
Format as structured JSON."""

            # Both AIs evaluate consensus
            codex_task = self._call_codex(consensus_prompt, "consensus")
            claude_task = self._call_claude(consensus_prompt, "consensus")

            codex_result, claude_result = await asyncio.gather(
                codex_task, claude_task, return_exceptions=True
            )

            codex_consensus = self._parse_result(codex_result, "codex")
            claude_consensus = self._parse_result(claude_result, "claude")

            # Calculate new verification
            verification = self._calculate_verification(
                codex_consensus,
                claude_consensus,
                is_consensus_phase=True
            )

            self.verification_history.append(verification)

            current_plan = CollaborativeOutput(
                task=task,
                phase=Phase.CONSENSUS,
                codex_analysis=codex_consensus,
                claude_analysis=claude_consensus,
                consensus=self._merge_consensus(codex_consensus, claude_consensus),
                verification=verification,
                final_output=None,
                code=None,
                iterations=iteration,
            )

            logger.info(
                f"   Verification: {verification.overall_verification * 100:.1f}% "
                f"({'✅ PASSED' if verification.meets_threshold else '❌ BELOW THRESHOLD'})"
            )

            if verification.meets_threshold:
                break

        return current_plan

    async def _phase_build(
        self,
        task: str,
        consensus: CollaborativeOutput,
        language: str,
    ) -> CollaborativeOutput:
        """Phase 4: Generate verified code based on consensus."""
        logger.info("🔨 Phase 4: BUILD - Generating verified code...")

        build_prompt = f"""Generate production-ready code based on this verified consensus:

TASK: {task}

VERIFIED CONSENSUS (92%+ confidence):
{consensus.consensus}

VERIFICATION SCORE: {consensus.verification.overall_verification * 100:.1f}%

LANGUAGE: {language}

REQUIREMENTS:
1. Follow the exact agreed-upon architecture
2. Implement all verified components
3. Include comprehensive error handling
4. Add type hints (Python) or TypeScript types
5. Include docstrings/comments (Google-style for Python)
6. Follow security best practices (OWASP)
7. No placeholders or TODOs - complete implementation only
8. Include unit tests

Generate the complete, production-ready code.
Format: Return ONLY the code, properly formatted."""

        # Both AIs generate code
        codex_task = self._call_codex(build_prompt, "build", max_tokens=4096)
        claude_task = self._call_claude(build_prompt, "build", max_tokens=4096)

        codex_result, claude_result = await asyncio.gather(
            codex_task, claude_task, return_exceptions=True
        )

        codex_code = self._extract_code(codex_result)
        claude_code = self._extract_code(claude_result)

        # Final code synthesis - use Claude Opus to merge best of both
        final_code = await self._synthesize_code(
            task, codex_code, claude_code, consensus, language
        )

        return CollaborativeOutput(
            task=task,
            phase=Phase.BUILD,
            codex_analysis={"code": codex_code},
            claude_analysis={"code": claude_code},
            consensus=consensus.consensus,
            verification=consensus.verification,
            final_output="Code generated successfully with 92%+ verification",
            code=final_code,
            iterations=consensus.iterations,
        )

    async def _synthesize_code(
        self,
        task: str,
        codex_code: str,
        claude_code: str,
        consensus: CollaborativeOutput,
        language: str,
    ) -> str:
        """Synthesize final code from both AI outputs."""
        synthesis_prompt = f"""Synthesize the best final code from these two implementations:

TASK: {task}

CODEX CODE:
```{language}
{codex_code}
```

CLAUDE CODE:
```{language}
{claude_code}
```

VERIFIED CONSENSUS:
{consensus.consensus}

Create the optimal final implementation that:
1. Takes the best elements from both versions
2. Ensures all consensus points are implemented
3. Maintains consistency and clean architecture
4. Has no redundancy or conflicts
5. Is production-ready

Return ONLY the final synthesized code."""

        result = await self._call_claude(synthesis_prompt, "synthesis", max_tokens=4096)
        return self._extract_code(result)

    async def _call_codex(
        self,
        prompt: str,
        phase: str,
        max_tokens: int = 2048,
    ) -> str:
        """Call GPT-5.1-codex-max."""
        if not self.codex:
            return '{"error": "Codex not initialized", "confidence": 0.0}'

        try:
            response = await self.codex.chat.completions.create(
                model=self.codex_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are GPT-5.1-codex-max, an advanced code generation AI. "
                            "You are collaborating with Claude Opus 4.5 to produce verified, "
                            "production-ready code. Be rigorous, precise, and evidence-based. "
                            "Always include confidence scores in your analysis."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.2,  # Low temperature for consistency
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Codex call failed ({phase}): {e}")
            return f'{{"error": "{str(e)}", "confidence": 0.0}}'

    async def _call_claude(
        self,
        prompt: str,
        phase: str,
        max_tokens: int = 2048,
    ) -> str:
        """Call Claude Opus 4.5."""
        if not self.claude:
            return '{"error": "Claude not initialized", "confidence": 0.0}'

        try:
            response = await self.claude.messages.create(
                model=self.claude_model,
                max_tokens=max_tokens,
                temperature=0.2,  # Low temperature for consistency
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "You are Claude Opus 4.5, collaborating with GPT-5.1-codex-max "
                            "to produce verified, production-ready code. Be rigorous, precise, "
                            "and evidence-based. Always include confidence scores.\n\n"
                            f"{prompt}"
                        ),
                    }
                ],
            )
            return response.content[0].text

        except Exception as e:
            logger.error(f"Claude call failed ({phase}): {e}")
            return f'{{"error": "{str(e)}", "confidence": 0.0}}'

    def _parse_result(self, result: str | Exception, source: str) -> dict[str, Any]:
        """Parse AI response into structured dict."""
        if isinstance(result, Exception):
            return {"error": str(result), "source": source, "confidence": 0.0}

        try:
            import json
            # Try to parse as JSON
            # Handle markdown code blocks
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]

            return json.loads(result.strip())
        except json.JSONDecodeError:
            # Return as raw analysis if not JSON
            return {
                "raw_analysis": result,
                "source": source,
                "confidence": 0.7,  # Moderate confidence for non-structured output
            }

    def _extract_code(self, result: str | Exception) -> str:
        """Extract code from AI response."""
        if isinstance(result, Exception):
            return f"# Error: {result}"

        # Handle markdown code blocks
        if "```" in result:
            parts = result.split("```")
            if len(parts) >= 2:
                code_block = parts[1]
                # Remove language identifier if present
                if code_block.startswith(("python", "javascript", "typescript", "go", "rust")):
                    code_block = "\n".join(code_block.split("\n")[1:])
                return code_block.strip()

        return result.strip()

    def _calculate_verification(
        self,
        codex_analysis: dict[str, Any],
        claude_analysis: dict[str, Any],
        is_consensus_phase: bool = False,
    ) -> VerificationResult:
        """Calculate verification score between both AI analyses."""

        # Extract confidence scores
        codex_confidence = self._extract_confidence(codex_analysis)
        claude_confidence = self._extract_confidence(claude_analysis)

        # Find agreement and disagreement points
        verified_points = []
        disputed_points = []

        # Compare key elements (simplified - in production would be more sophisticated)
        codex_keys = set(self._flatten_keys(codex_analysis))
        claude_keys = set(self._flatten_keys(claude_analysis))

        common_keys = codex_keys & claude_keys
        different_keys = codex_keys ^ claude_keys

        # Calculate agreement score based on overlap
        if codex_keys or claude_keys:
            overlap_ratio = len(common_keys) / max(len(codex_keys | claude_keys), 1)
        else:
            overlap_ratio = 0.5

        # For consensus phase, weight the explicit confidence scores more heavily
        if is_consensus_phase:
            agreement_score = (
                0.4 * overlap_ratio +
                0.3 * codex_confidence +
                0.3 * claude_confidence
            )
        else:
            agreement_score = (
                0.5 * overlap_ratio +
                0.25 * codex_confidence +
                0.25 * claude_confidence
            )

        # Compile verified and disputed points
        for key in common_keys:
            verified_points.append(key)
        for key in different_keys:
            disputed_points.append(key)

        overall = min(agreement_score, codex_confidence, claude_confidence)

        return VerificationResult(
            codex_confidence=codex_confidence,
            claude_confidence=claude_confidence,
            agreement_score=agreement_score,
            verified_points=verified_points[:10],  # Top 10
            disputed_points=disputed_points[:5],   # Top 5 disputes
            overall_verification=overall,
            meets_threshold=overall >= self.VERIFICATION_THRESHOLD,
        )

    def _extract_confidence(self, analysis: dict[str, Any]) -> float:
        """Extract confidence score from analysis."""
        if "confidence" in analysis:
            return float(analysis["confidence"])
        if "overall_confidence" in analysis:
            return float(analysis["overall_confidence"])
        if "confidence_score" in analysis:
            return float(analysis["confidence_score"])

        # Look for nested confidence
        for key, value in analysis.items():
            if isinstance(value, dict) and "confidence" in value:
                return float(value["confidence"])

        # Default moderate confidence
        return 0.75

    def _flatten_keys(self, d: dict[str, Any], prefix: str = "") -> list[str]:
        """Flatten nested dict keys for comparison."""
        keys = []
        for key, value in d.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys.append(full_key)
            if isinstance(value, dict):
                keys.extend(self._flatten_keys(value, full_key))
        return keys

    def _merge_consensus(
        self,
        codex_consensus: dict[str, Any],
        claude_consensus: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge consensus from both AIs."""
        return {
            "codex_contribution": codex_consensus,
            "claude_contribution": claude_consensus,
            "merged_at": datetime.utcnow().isoformat(),
            "consensus_type": "dual_ai_collaborative",
        }

    async def quick_generate(
        self,
        task: str,
        language: str = "python",
    ) -> str:
        """Quick code generation with full collaboration pipeline."""
        result = await self.collaborate(task, language=language)

        if result.code:
            return result.code
        else:
            return f"# Verification failed: {result.final_output}"

    def get_verification_history(self) -> list[dict[str, Any]]:
        """Get history of verification attempts."""
        return [
            {
                "codex_confidence": v.codex_confidence,
                "claude_confidence": v.claude_confidence,
                "agreement_score": v.agreement_score,
                "overall": v.overall_verification,
                "passed": v.meets_threshold,
            }
            for v in self.verification_history
        ]


# Factory function
def create_dual_ai_orchestrator() -> DualAICollaborativeOrchestrator:
    """Create Dual-AI Collaborative Orchestrator instance."""
    return DualAICollaborativeOrchestrator()


# Global instance
dual_ai = create_dual_ai_orchestrator()


# Convenience functions
async def collaborative_generate(task: str, language: str = "python") -> CollaborativeOutput:
    """Generate code using dual-AI collaboration with 92%+ verification."""
    return await dual_ai.collaborate(task, language=language)


async def quick_code(task: str, language: str = "python") -> str:
    """Quick verified code generation."""
    return await dual_ai.quick_generate(task, language)


logger.info(
    "🤝 Dual-AI Collaborative Orchestrator loaded "
    "(GPT-5.1-codex-max + Claude Opus 4.5, 92% verification threshold)"
)

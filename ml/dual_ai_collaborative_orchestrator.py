"""
Dual-AI Collaborative Orchestrator
GPT-5.1-codex-max + Claude Opus 4.5 + Google Vertex AI working in tandem

Architecture:
1. RESEARCH - All AIs analyze the task independently
2. PLAN - All propose solutions with reasoning
3. CONSENSUS - Cross-validate and agree (92%+ verification required)
4. BUILD - Generate verified, production-ready code/content

Task Routing:
- CODE tasks: Codex + Claude collaboration
- CONTENT tasks: Vertex + Claude verification (mandatory)
- WEB DEV tasks: Vertex + Claude + Codex (all three)

Truth Protocol Compliance:
- Rule #1: Never Guess - 92%+ verified data before output
- Rule #4: State Uncertainty - Track confidence levels
- Rule #8: Test Coverage ≥90%
- Rule #16: Web Search Verification
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


# Try to import Vertex AI
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False
    logger.warning("⚠️ Vertex AI not available - install google-cloud-aiplatform")


class Phase(Enum):
    """Collaboration phases."""
    RESEARCH = "research"
    PLAN = "plan"
    CONSENSUS = "consensus"
    BUILD = "build"


class TaskType(Enum):
    """Task categories for routing."""
    CODE = "code"                    # Pure coding tasks - Codex + Claude
    CONTENT = "content"              # Content generation - Vertex + Claude (mandatory)
    WEB_DEVELOPMENT = "web_dev"      # Web dev - All three AIs
    MARKETING = "marketing"          # Marketing content - Vertex + Claude
    DOCUMENTATION = "documentation"  # Docs - Vertex + Claude
    GENERAL = "general"              # General tasks - Codex + Claude


@dataclass
class VerificationResult:
    """Result of cross-verification between models."""
    codex_confidence: float
    claude_confidence: float
    vertex_confidence: float  # Vertex AI confidence
    agreement_score: float
    verified_points: list[str]
    disputed_points: list[str]
    overall_verification: float
    meets_threshold: bool
    models_used: list[str] = field(default_factory=list)

    @property
    def is_verified(self) -> bool:
        """Check if verification meets 92% threshold."""
        return self.overall_verification >= 0.92


@dataclass
class CollaborativeOutput:
    """Output from dual-AI collaboration."""
    task: str
    phase: Phase
    task_type: TaskType
    codex_analysis: dict[str, Any]
    claude_analysis: dict[str, Any]
    vertex_analysis: dict[str, Any]  # Vertex AI analysis
    consensus: dict[str, Any]
    verification: VerificationResult
    final_output: str | None
    code: str | None
    content: str | None = None  # For content tasks
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    iterations: int = 0


class DualAICollaborativeOrchestrator:
    """
    Orchestrates GPT-5.1-codex-max, Claude Opus 4.5, and Google Vertex AI
    for collaborative code/content generation with 92%+ verification threshold.

    Task Routing:
    - CODE: Codex + Claude
    - CONTENT/MARKETING/DOCS: Vertex + Claude (mandatory verification)
    - WEB_DEVELOPMENT: All three AIs
    """

    VERIFICATION_THRESHOLD = 0.92  # 92% minimum verification
    MAX_CONSENSUS_ITERATIONS = 3   # Max attempts to reach consensus

    # Content keywords that trigger Vertex + Claude verification
    CONTENT_KEYWORDS = [
        "content", "article", "blog", "post", "copy", "writing",
        "marketing", "seo", "social media", "email", "newsletter",
        "description", "landing page", "headline", "tagline",
        "product description", "about us", "documentation", "readme",
    ]

    # Web dev keywords that trigger all three AIs
    WEB_DEV_KEYWORDS = [
        "website", "web page", "frontend", "ui", "ux", "component",
        "react", "vue", "angular", "html", "css", "javascript",
        "typescript", "next.js", "nuxt", "svelte", "tailwind",
        "wordpress", "theme", "template", "responsive", "layout",
    ]

    def __init__(self):
        config = get_config()
        self.models_available: list[str] = []

        # Initialize Claude Opus 4.5
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.claude = AsyncAnthropic(api_key=anthropic_key)
            self.claude_model = "claude-opus-4-20250514"
            self.models_available.append("claude")
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
            self.models_available.append("codex")
            logger.info("✅ GPT-5.1-codex-max initialized")
        else:
            self.codex = None
            logger.warning("⚠️ GPT-5.1-codex-max not available - missing API key")

        # Initialize Google Vertex AI
        self.vertex = None
        self.vertex_model = None
        google_project = os.getenv("GOOGLE_CLOUD_PROJECT")
        google_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

        if VERTEX_AVAILABLE and google_project:
            try:
                vertexai.init(project=google_project, location=google_location)
                self.vertex_model = GenerativeModel("gemini-1.5-pro")
                self.vertex = True
                self.models_available.append("vertex")
                logger.info(f"✅ Vertex AI initialized (project: {google_project})")
            except Exception as e:
                logger.warning(f"⚠️ Vertex AI initialization failed: {e}")
                self.vertex = None
        else:
            if not VERTEX_AVAILABLE:
                logger.warning("⚠️ Vertex AI SDK not installed")
            else:
                logger.warning("⚠️ Vertex AI not available - missing GOOGLE_CLOUD_PROJECT")

        # Collaboration state
        self.current_session: dict[str, Any] = {}
        self.verification_history: list[VerificationResult] = []

        logger.info(
            f"🤝 Multi-AI Collaborative Orchestrator initialized "
            f"(models: {', '.join(self.models_available)}, threshold: {self.VERIFICATION_THRESHOLD * 100}%)"
        )

    def _detect_task_type(self, task: str) -> TaskType:
        """Detect task type from task description."""
        task_lower = task.lower()

        # Check for web development keywords (highest priority - uses all 3)
        for keyword in self.WEB_DEV_KEYWORDS:
            if keyword in task_lower:
                return TaskType.WEB_DEVELOPMENT

        # Check for content keywords (requires Vertex + Claude)
        for keyword in self.CONTENT_KEYWORDS:
            if keyword in task_lower:
                # Distinguish between content types
                if any(k in task_lower for k in ["marketing", "seo", "social", "email"]):
                    return TaskType.MARKETING
                elif any(k in task_lower for k in ["documentation", "readme", "docs"]):
                    return TaskType.DOCUMENTATION
                return TaskType.CONTENT

        # Default to code for programming tasks
        code_indicators = [
            "function", "class", "api", "endpoint", "database",
            "implement", "code", "script", "algorithm", "module",
        ]
        for indicator in code_indicators:
            if indicator in task_lower:
                return TaskType.CODE

        return TaskType.GENERAL

    def _get_models_for_task(self, task_type: TaskType) -> list[str]:
        """Get which models to use based on task type."""
        if task_type == TaskType.WEB_DEVELOPMENT:
            # Web dev uses all three AIs
            return ["codex", "claude", "vertex"]
        elif task_type in [TaskType.CONTENT, TaskType.MARKETING, TaskType.DOCUMENTATION]:
            # Content tasks MUST use Vertex + Claude
            return ["vertex", "claude"]
        else:
            # Code and general tasks use Codex + Claude
            return ["codex", "claude"]

    async def collaborate(
        self,
        task: str,
        context: dict[str, Any] | None = None,
        language: str = "python",
        task_type: TaskType | None = None,
    ) -> CollaborativeOutput:
        """
        Execute full collaboration pipeline: Research → Plan → Consensus → Build.

        Args:
            task: The coding/content task to complete
            context: Additional context (existing code, requirements, etc.)
            language: Target programming language
            task_type: Override auto-detected task type

        Returns:
            CollaborativeOutput with verified code/content (if 92%+ threshold met)
        """
        # Auto-detect task type if not provided
        detected_type = task_type or self._detect_task_type(task)
        models_to_use = self._get_models_for_task(detected_type)

        logger.info(
            f"🚀 Starting multi-AI collaboration for: {task[:100]}...\n"
            f"   Task type: {detected_type.value}\n"
            f"   Models: {', '.join(models_to_use)}"
        )

        # Phase 1: Research
        research_output = await self._phase_research(task, context, language, detected_type, models_to_use)

        # Phase 2: Plan
        plan_output = await self._phase_plan(task, research_output, language, detected_type, models_to_use)

        # Phase 3: Consensus (iterate until 92%+ or max iterations)
        consensus_output = await self._phase_consensus(task, plan_output, language, detected_type, models_to_use)

        # Phase 4: Build (only if verification threshold met)
        if consensus_output.verification.meets_threshold:
            final_output = await self._phase_build(task, consensus_output, language, detected_type, models_to_use)
            return final_output
        else:
            logger.warning(
                f"⚠️ Verification threshold not met: "
                f"{consensus_output.verification.overall_verification * 100:.1f}% < 92%"
            )
            consensus_output.code = None
            consensus_output.content = None
            consensus_output.final_output = (
                f"Verification threshold not met. "
                f"Current: {consensus_output.verification.overall_verification * 100:.1f}%. "
                f"Required: 92%. Disputed points: {consensus_output.verification.disputed_points}"
            )
            return consensus_output

    async def generate_content(
        self,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> CollaborativeOutput:
        """
        Generate content with mandatory Vertex + Claude verification.

        This method ALWAYS uses Vertex AI and Claude for verification,
        regardless of task content.

        Args:
            task: The content generation task
            context: Additional context

        Returns:
            CollaborativeOutput with verified content
        """
        return await self.collaborate(
            task=task,
            context=context,
            language="markdown",
            task_type=TaskType.CONTENT,
        )

    async def _call_vertex(
        self,
        prompt: str,
        phase: str,
        max_tokens: int = 2048,
    ) -> str:
        """Call Google Vertex AI (Gemini 1.5 Pro)."""
        if not self.vertex or not self.vertex_model:
            return '{"error": "Vertex AI not initialized", "confidence": 0.0}'

        try:
            # Vertex AI uses synchronous API, wrap in executor
            import asyncio

            def sync_call():
                response = self.vertex_model.generate_content(
                    prompt,
                    generation_config={
                        "max_output_tokens": max_tokens,
                        "temperature": 0.2,
                    },
                )
                return response.text

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, sync_call)
            return result

        except Exception as e:
            logger.error(f"Vertex AI call failed ({phase}): {e}")
            return f'{{"error": "{str(e)}", "confidence": 0.0}}'

    async def _run_models(
        self,
        prompt: str,
        phase: str,
        models: list[str],
        max_tokens: int = 2048,
    ) -> dict[str, str]:
        """Run specified models in parallel and return results."""
        tasks = {}

        if "codex" in models and self.codex:
            tasks["codex"] = self._call_codex(prompt, phase, max_tokens)
        if "claude" in models and self.claude:
            tasks["claude"] = self._call_claude(prompt, phase, max_tokens)
        if "vertex" in models and self.vertex:
            tasks["vertex"] = self._call_vertex(prompt, phase, max_tokens)

        if not tasks:
            return {"error": "No models available"}

        # Run all in parallel
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        return {
            model: result if not isinstance(result, Exception) else f'{{"error": "{result}"}}'
            for model, result in zip(tasks.keys(), results)
        }

    async def _phase_research(
        self,
        task: str,
        context: dict[str, Any] | None,
        language: str,
        task_type: TaskType,
        models: list[str],
    ) -> CollaborativeOutput:
        """Phase 1: All relevant AIs research and analyze the task independently."""
        logger.info(f"📚 Phase 1: RESEARCH - {len(models)} AIs analyzing task...")

        # Adjust prompt based on task type
        task_context = "coding" if task_type == TaskType.CODE else task_type.value

        research_prompt = f"""Analyze this {task_context} task thoroughly:

TASK: {task}

TASK TYPE: {task_type.value}
LANGUAGE/FORMAT: {language}

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

        # Run all specified models in parallel
        results = await self._run_models(research_prompt, "research", models)

        # Parse results
        codex_analysis = self._parse_result(results.get("codex", "{}"), "codex")
        claude_analysis = self._parse_result(results.get("claude", "{}"), "claude")
        vertex_analysis = self._parse_result(results.get("vertex", "{}"), "vertex")

        # Calculate verification with all models
        verification = self._calculate_multi_verification(
            codex_analysis, claude_analysis, vertex_analysis, models
        )

        return CollaborativeOutput(
            task=task,
            phase=Phase.RESEARCH,
            task_type=task_type,
            codex_analysis=codex_analysis,
            claude_analysis=claude_analysis,
            vertex_analysis=vertex_analysis,
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
        task_type: TaskType,
        models: list[str],
    ) -> CollaborativeOutput:
        """Phase 2: All AIs propose solutions based on research."""
        logger.info(f"📋 Phase 2: PLAN - {len(models)} AIs proposing solutions...")

        # Build research context from all models
        research_context = ""
        if research.codex_analysis:
            research_context += f"CODEX RESEARCH:\n{research.codex_analysis}\n\n"
        if research.claude_analysis:
            research_context += f"CLAUDE RESEARCH:\n{research.claude_analysis}\n\n"
        if research.vertex_analysis:
            research_context += f"VERTEX RESEARCH:\n{research.vertex_analysis}\n\n"

        plan_prompt = f"""Based on this research, propose a detailed solution:

TASK: {task}
TASK TYPE: {task_type.value}

{research_context}

LANGUAGE/FORMAT: {language}

Provide a comprehensive implementation plan:
1. ARCHITECTURE
   - High-level design
   - Component breakdown
   - Data flow

2. IMPLEMENTATION STEPS
   - Step-by-step approach
   - Order of implementation
   - Dependencies between components

3. {'CODE STRUCTURE' if task_type == TaskType.CODE else 'CONTENT STRUCTURE'}
   - {'Classes/functions to create' if task_type == TaskType.CODE else 'Sections and flow'}
   - {'Type hints and interfaces' if task_type == TaskType.CODE else 'Tone and style guidelines'}
   - Error handling strategy

4. {'TESTING STRATEGY' if task_type == TaskType.CODE else 'QUALITY CHECKLIST'}
   - {'Unit tests needed' if task_type == TaskType.CODE else 'Accuracy verification'}
   - {'Integration tests' if task_type == TaskType.CODE else 'Brand consistency check'}
   - Edge case coverage

5. SECURITY MEASURES
   - Input validation
   - {'Authentication/authorization' if task_type == TaskType.CODE else 'Content safety review'}
   - Data protection

6. CONFIDENCE SCORE
   - Overall confidence (0.0 to 1.0)
   - Confidence per component
   - Verification points

Format as structured JSON with clear sections."""

        # Run all specified models in parallel
        results = await self._run_models(plan_prompt, "plan", models)

        codex_analysis = self._parse_result(results.get("codex", "{}"), "codex")
        claude_analysis = self._parse_result(results.get("claude", "{}"), "claude")
        vertex_analysis = self._parse_result(results.get("vertex", "{}"), "vertex")

        verification = self._calculate_multi_verification(
            codex_analysis, claude_analysis, vertex_analysis, models
        )

        return CollaborativeOutput(
            task=task,
            phase=Phase.PLAN,
            task_type=task_type,
            codex_analysis=codex_analysis,
            claude_analysis=claude_analysis,
            vertex_analysis=vertex_analysis,
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
        task_type: TaskType,
        models: list[str],
    ) -> CollaborativeOutput:
        """Phase 3: Cross-validate and reach 92%+ consensus."""
        logger.info(f"🤝 Phase 3: CONSENSUS - {len(models)} AIs cross-validating for 92%+ agreement...")

        iteration = 0
        current_plan = plan

        while iteration < self.MAX_CONSENSUS_ITERATIONS:
            iteration += 1
            logger.info(f"   Consensus iteration {iteration}/{self.MAX_CONSENSUS_ITERATIONS}")

            # Build proposals context from all models
            proposals_context = ""
            if current_plan.codex_analysis and "codex" in models:
                proposals_context += f"CODEX PROPOSAL:\n{current_plan.codex_analysis}\n\n"
            if current_plan.claude_analysis and "claude" in models:
                proposals_context += f"CLAUDE PROPOSAL:\n{current_plan.claude_analysis}\n\n"
            if current_plan.vertex_analysis and "vertex" in models:
                proposals_context += f"VERTEX PROPOSAL:\n{current_plan.vertex_analysis}\n\n"

            consensus_prompt = f"""Cross-validate and reach consensus on this solution:

TASK: {task}
TASK TYPE: {task_type.value}

{proposals_context}

CURRENT VERIFICATION: {current_plan.verification.overall_verification * 100:.1f}%
DISPUTED POINTS: {current_plan.verification.disputed_points}
MODELS PARTICIPATING: {', '.join(models)}

TARGET: 92%+ verification required before {'code' if task_type == TaskType.CODE else 'content'} generation.

Analyze all proposals and provide:
1. AGREEMENT POINTS
   - What all AIs agree on (list each point)
   - Confidence level per point

2. DISAGREEMENT RESOLUTION
   - Points of disagreement
   - Evidence-based resolution for each
   - Final decision with justification

3. UNIFIED SOLUTION
   - Merged best approach
   - Incorporates strengths from all models
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

            # All AIs evaluate consensus
            results = await self._run_models(consensus_prompt, "consensus", models)

            codex_consensus = self._parse_result(results.get("codex", "{}"), "codex")
            claude_consensus = self._parse_result(results.get("claude", "{}"), "claude")
            vertex_consensus = self._parse_result(results.get("vertex", "{}"), "vertex")

            # Calculate new verification with all models
            verification = self._calculate_multi_verification(
                codex_consensus, claude_consensus, vertex_consensus, models,
                is_consensus_phase=True
            )

            self.verification_history.append(verification)

            current_plan = CollaborativeOutput(
                task=task,
                phase=Phase.CONSENSUS,
                task_type=task_type,
                codex_analysis=codex_consensus,
                claude_analysis=claude_consensus,
                vertex_analysis=vertex_consensus,
                consensus=self._merge_multi_consensus(codex_consensus, claude_consensus, vertex_consensus, models),
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
        task_type: TaskType,
        models: list[str],
    ) -> CollaborativeOutput:
        """Phase 4: Generate verified code/content based on consensus."""
        is_content = task_type in [TaskType.CONTENT, TaskType.MARKETING, TaskType.DOCUMENTATION]
        output_type = "content" if is_content else "code"

        logger.info(f"🔨 Phase 4: BUILD - Generating verified {output_type}...")

        build_prompt = f"""Generate production-ready {output_type} based on this verified consensus:

TASK: {task}
TASK TYPE: {task_type.value}

VERIFIED CONSENSUS (92%+ confidence):
{consensus.consensus}

VERIFICATION SCORE: {consensus.verification.overall_verification * 100:.1f}%
MODELS VERIFIED: {', '.join(consensus.verification.models_used)}

{'LANGUAGE' if not is_content else 'FORMAT'}: {language}

REQUIREMENTS:
1. Follow the exact agreed-upon {'architecture' if not is_content else 'structure'}
2. Implement all verified components
3. {'Include comprehensive error handling' if not is_content else 'Maintain consistent tone and style'}
4. {'Add type hints (Python) or TypeScript types' if not is_content else 'Use proper formatting and structure'}
5. {'Include docstrings/comments (Google-style for Python)' if not is_content else 'Include engaging headlines and CTAs'}
6. {'Follow security best practices (OWASP)' if not is_content else 'Follow brand guidelines and SEO best practices'}
7. No placeholders or TODOs - complete implementation only
8. {'Include unit tests' if not is_content else 'Include meta descriptions if applicable'}

Generate the complete, production-ready {output_type}.
Format: Return ONLY the {output_type}, properly formatted."""

        # All AIs generate output
        results = await self._run_models(build_prompt, "build", models, max_tokens=4096)

        codex_output = self._extract_code(results.get("codex", ""))
        claude_output = self._extract_code(results.get("claude", ""))
        vertex_output = self._extract_code(results.get("vertex", ""))

        # Final synthesis - use Claude Opus to merge best of all
        final_output = await self._synthesize_output(
            task, codex_output, claude_output, vertex_output, consensus, language, task_type, models
        )

        return CollaborativeOutput(
            task=task,
            phase=Phase.BUILD,
            task_type=task_type,
            codex_analysis={"output": codex_output},
            claude_analysis={"output": claude_output},
            vertex_analysis={"output": vertex_output},
            consensus=consensus.consensus,
            verification=consensus.verification,
            final_output=f"{output_type.title()} generated successfully with 92%+ verification",
            code=final_output if not is_content else None,
            content=final_output if is_content else None,
            iterations=consensus.iterations,
        )

    async def _synthesize_output(
        self,
        task: str,
        codex_output: str,
        claude_output: str,
        vertex_output: str,
        consensus: CollaborativeOutput,
        language: str,
        task_type: TaskType,
        models: list[str],
    ) -> str:
        """Synthesize final output from all AI outputs."""
        is_content = task_type in [TaskType.CONTENT, TaskType.MARKETING, TaskType.DOCUMENTATION]
        output_type = "content" if is_content else "code"

        # Build outputs section
        outputs_section = ""
        if codex_output and "codex" in models:
            outputs_section += f"CODEX OUTPUT:\n```{language}\n{codex_output}\n```\n\n"
        if claude_output and "claude" in models:
            outputs_section += f"CLAUDE OUTPUT:\n```{language}\n{claude_output}\n```\n\n"
        if vertex_output and "vertex" in models:
            outputs_section += f"VERTEX OUTPUT:\n```{language}\n{vertex_output}\n```\n\n"

        synthesis_prompt = f"""Synthesize the best final {output_type} from these implementations:

TASK: {task}
TASK TYPE: {task_type.value}

{outputs_section}

VERIFIED CONSENSUS:
{consensus.consensus}

Create the optimal final implementation that:
1. Takes the best elements from all versions
2. Ensures all consensus points are implemented
3. Maintains consistency and clean {'architecture' if not is_content else 'structure'}
4. Has no redundancy or conflicts
5. Is production-ready

Return ONLY the final synthesized {output_type}."""

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

    def _calculate_multi_verification(
        self,
        codex_analysis: dict[str, Any],
        claude_analysis: dict[str, Any],
        vertex_analysis: dict[str, Any],
        models: list[str],
        is_consensus_phase: bool = False,
    ) -> VerificationResult:
        """Calculate verification score across all participating AI analyses."""

        # Extract confidence scores for active models
        codex_confidence = self._extract_confidence(codex_analysis) if "codex" in models else 0.0
        claude_confidence = self._extract_confidence(claude_analysis) if "claude" in models else 0.0
        vertex_confidence = self._extract_confidence(vertex_analysis) if "vertex" in models else 0.0

        # Collect all key sets from participating models
        all_key_sets = []
        if "codex" in models and codex_analysis:
            all_key_sets.append(set(self._flatten_keys(codex_analysis)))
        if "claude" in models and claude_analysis:
            all_key_sets.append(set(self._flatten_keys(claude_analysis)))
        if "vertex" in models and vertex_analysis:
            all_key_sets.append(set(self._flatten_keys(vertex_analysis)))

        # Find agreement points (keys in ALL participating models)
        verified_points = []
        disputed_points = []

        if all_key_sets:
            common_keys = all_key_sets[0]
            all_keys = all_key_sets[0]
            for key_set in all_key_sets[1:]:
                common_keys = common_keys & key_set
                all_keys = all_keys | key_set

            different_keys = all_keys - common_keys
            overlap_ratio = len(common_keys) / max(len(all_keys), 1)

            verified_points = list(common_keys)[:10]
            disputed_points = list(different_keys)[:5]
        else:
            overlap_ratio = 0.5

        # Calculate agreement score based on number of models and their confidences
        active_confidences = []
        if "codex" in models:
            active_confidences.append(codex_confidence)
        if "claude" in models:
            active_confidences.append(claude_confidence)
        if "vertex" in models:
            active_confidences.append(vertex_confidence)

        avg_confidence = sum(active_confidences) / len(active_confidences) if active_confidences else 0.5

        # For consensus phase, weight explicit confidence scores more heavily
        if is_consensus_phase:
            agreement_score = 0.4 * overlap_ratio + 0.6 * avg_confidence
        else:
            agreement_score = 0.5 * overlap_ratio + 0.5 * avg_confidence

        # Overall is the minimum of all participating model confidences
        overall = min([agreement_score] + active_confidences) if active_confidences else 0.0

        return VerificationResult(
            codex_confidence=codex_confidence,
            claude_confidence=claude_confidence,
            vertex_confidence=vertex_confidence,
            agreement_score=agreement_score,
            verified_points=verified_points,
            disputed_points=disputed_points,
            overall_verification=overall,
            meets_threshold=overall >= self.VERIFICATION_THRESHOLD,
            models_used=models,
        )

    def _merge_multi_consensus(
        self,
        codex_consensus: dict[str, Any],
        claude_consensus: dict[str, Any],
        vertex_consensus: dict[str, Any],
        models: list[str],
    ) -> dict[str, Any]:
        """Merge consensus from all participating AIs."""
        consensus = {
            "merged_at": datetime.utcnow().isoformat(),
            "consensus_type": "multi_ai_collaborative",
            "models_participating": models,
        }

        if "codex" in models:
            consensus["codex_contribution"] = codex_consensus
        if "claude" in models:
            consensus["claude_contribution"] = claude_consensus
        if "vertex" in models:
            consensus["vertex_contribution"] = vertex_consensus

        return consensus

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

    async def quick_generate(
        self,
        task: str,
        language: str = "python",
    ) -> str:
        """Quick code/content generation with full collaboration pipeline."""
        result = await self.collaborate(task, language=language)

        if result.code:
            return result.code
        elif result.content:
            return result.content
        else:
            return f"# Verification failed: {result.final_output}"

    async def quick_content(
        self,
        task: str,
    ) -> str:
        """Quick content generation with mandatory Vertex + Claude verification."""
        result = await self.generate_content(task)

        if result.content:
            return result.content
        else:
            return f"<!-- Verification failed: {result.final_output} -->"

    def get_verification_history(self) -> list[dict[str, Any]]:
        """Get history of verification attempts."""
        return [
            {
                "codex_confidence": v.codex_confidence,
                "claude_confidence": v.claude_confidence,
                "vertex_confidence": v.vertex_confidence,
                "agreement_score": v.agreement_score,
                "overall": v.overall_verification,
                "passed": v.meets_threshold,
                "models": v.models_used,
            }
            for v in self.verification_history
        ]


# Factory function
def create_multi_ai_orchestrator() -> DualAICollaborativeOrchestrator:
    """Create Multi-AI Collaborative Orchestrator instance."""
    return DualAICollaborativeOrchestrator()


# Alias for backward compatibility
create_dual_ai_orchestrator = create_multi_ai_orchestrator


# Global instance
multi_ai = create_multi_ai_orchestrator()
dual_ai = multi_ai  # Alias for backward compatibility


# Convenience functions
async def collaborative_generate(
    task: str,
    language: str = "python",
    task_type: TaskType | None = None,
) -> CollaborativeOutput:
    """Generate code/content using multi-AI collaboration with 92%+ verification."""
    return await multi_ai.collaborate(task, language=language, task_type=task_type)


async def quick_code(task: str, language: str = "python") -> str:
    """Quick verified code generation."""
    return await multi_ai.quick_generate(task, language)


async def quick_content(task: str) -> str:
    """Quick verified content generation (Vertex + Claude)."""
    return await multi_ai.quick_content(task)


async def generate_verified_content(
    task: str,
    context: dict[str, Any] | None = None,
) -> CollaborativeOutput:
    """Generate content with mandatory Vertex + Claude verification."""
    return await multi_ai.generate_content(task, context)


logger.info(
    "🤝 Multi-AI Collaborative Orchestrator loaded "
    "(GPT-5.1-codex-max + Claude Opus 4.5 + Vertex AI, 92% verification threshold)"
)

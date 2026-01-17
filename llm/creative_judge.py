"""
Elite Creative Judging System
==============================

Three-Pillar LLM-as-Judge evaluation for creative outputs.

Pillars:
1. PROMPT QUALITY - Was the agent properly set up to succeed?
2. EXECUTION QUALITY - Did they deliver exactly what was asked?
3. BRAND DNA - Will the target market recognize the brand?

Usage:
    judge = CreativeJudge()
    await judge.initialize()

    verdict = await judge.evaluate(
        prompt=original_prompt,
        response=llm_response,
        brand_context=SKYYROSE_DNA,
        task_requirements=requirements,
    )

    print(f"Total Score: {verdict.total_score}/100")
    print(f"Verdict: {verdict.verdict}")  # ELITE / EXCELLENT / GOOD / NEEDS_WORK / FAIL
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# PYDANTIC SCHEMAS FOR STRUCTURED OUTPUT (Context7 Pattern)
# =============================================================================


class CriterionEval(BaseModel):
    """Pydantic model for criterion-level evaluation."""

    name: str = Field(..., description="Criterion name (e.g., 'clarity_of_instructions')")
    score: float = Field(..., ge=0, le=100, description="Score 0-100")
    completeness: float = Field(
        default=1.0, ge=0, le=1, description="How complete is the coverage (0-1)"
    )
    quality_modifier: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description="Quality multiplier (0-1). Final = completeness × quality_modifier × 100",
    )
    reasoning: str = Field(..., description="Why this score was given")
    strengths: list[str] = Field(default_factory=list, description="What worked well")
    weaknesses: list[str] = Field(default_factory=list, description="What needs improvement")


class PillarEval(BaseModel):
    """Pydantic model for pillar-level evaluation."""

    name: str = Field(
        ..., description="Pillar name: PROMPT_QUALITY, EXECUTION_QUALITY, or BRAND_DNA"
    )
    criteria: list[CriterionEval] = Field(..., description="Individual criterion scores")


class JudgeOutput(BaseModel):
    """
    Pydantic schema for structured judge output.

    This enforces the exact output format from the LLM judge.
    Context7 pattern: Use json_schema with strict=true for guaranteed parsing.
    """

    pillars: list[PillarEval] = Field(..., description="Three pillar evaluations")
    total_score: float = Field(..., ge=0, le=100, description="Weighted total score 0-100")
    verdict: str = Field(..., description="ELITE, EXCELLENT, GOOD, NEEDS_WORK, or FAIL")
    summary: str = Field(..., description="Executive summary of the evaluation")
    recommendations: list[str] = Field(..., description="Actionable improvement suggestions")

    class Config:
        json_schema_extra = {
            "example": {
                "pillars": [
                    {
                        "name": "PROMPT_QUALITY",
                        "criteria": [
                            {
                                "name": "clarity_of_instructions",
                                "score": 85,
                                "completeness": 0.9,
                                "quality_modifier": 0.95,
                                "reasoning": "Clear instructions with specific deliverables",
                                "strengths": ["Explicit format requirement"],
                                "weaknesses": ["Missing mobile specs"],
                            }
                        ],
                    }
                ],
                "total_score": 82.5,
                "verdict": "EXCELLENT",
                "summary": "Strong creative execution...",
                "recommendations": ["Add mobile requirements"],
            }
        }


# JSON Schema for OpenAI structured output
JUDGE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "pillars": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "criteria": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "score": {"type": "number"},
                                "completeness": {"type": "number"},
                                "quality_modifier": {"type": "number"},
                                "reasoning": {"type": "string"},
                                "strengths": {"type": "array", "items": {"type": "string"}},
                                "weaknesses": {"type": "array", "items": {"type": "string"}},
                            },
                            "required": ["name", "score", "reasoning"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["name", "criteria"],
                "additionalProperties": False,
            },
        },
        "total_score": {"type": "number"},
        "verdict": {"type": "string", "enum": ["ELITE", "EXCELLENT", "GOOD", "NEEDS_WORK", "FAIL"]},
        "summary": {"type": "string"},
        "recommendations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["pillars", "total_score", "verdict", "summary", "recommendations"],
    "additionalProperties": False,
}


class Verdict(str, Enum):
    """Final verdict classification."""

    ELITE = "ELITE"  # 90-100: Exceptional, production-ready
    EXCELLENT = "EXCELLENT"  # 80-89: High quality, minor polish needed
    GOOD = "GOOD"  # 70-79: Solid work, some improvements needed
    NEEDS_WORK = "NEEDS_WORK"  # 50-69: Significant issues to address
    FAIL = "FAIL"  # 0-49: Does not meet requirements


@dataclass
class CriterionScore:
    """
    Individual criterion evaluation with quality modifier pattern.

    Context7 Pattern: Final score = completeness × quality_modifier × 100
    - Completeness: How much of the requirement was addressed (0-1)
    - Quality: How well it was done (0-1)
    - This gives more nuanced scoring than a single 0-100 number
    """

    name: str
    score: float  # 0-100 (can be computed or direct)
    weight: float  # 0.0-1.0 (criterion weight within pillar)
    reasoning: str
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    completeness: float = 1.0  # 0-1: coverage
    quality_modifier: float = 1.0  # 0-1: quality multiplier

    @property
    def computed_score(self) -> float:
        """Score using quality modifier pattern."""
        return self.completeness * self.quality_modifier * 100

    @property
    def weighted_score(self) -> float:
        """Use provided score or computed score."""
        effective_score = self.score if self.score > 0 else self.computed_score
        return effective_score * self.weight


@dataclass
class PillarScore:
    """Pillar-level evaluation (Prompt/Execution/Brand)."""

    pillar: str
    criteria: list[CriterionScore]
    weight: float  # Pillar weight in final score

    @property
    def pillar_score(self) -> float:
        """Weighted average of all criteria in this pillar (0-100 scale)."""
        if not self.criteria:
            return 0.0
        total_weight = sum(c.weight for c in self.criteria)
        if total_weight == 0:
            return 0.0
        # weighted_score = score * weight, so sum/total_weight = weighted avg
        # Scores are already 0-100, no need to multiply by 100
        return sum(c.weighted_score for c in self.criteria) / total_weight

    @property
    def weighted_score(self) -> float:
        return self.pillar_score * self.weight


@dataclass
class JudgeVerdict:
    """Complete evaluation verdict."""

    pillars: list[PillarScore]
    total_score: float
    verdict: Verdict
    summary: str
    recommendations: list[str]
    judge_model: str
    evaluation_time_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_score": self.total_score,
            "verdict": self.verdict.value,
            "summary": self.summary,
            "recommendations": self.recommendations,
            "pillars": [
                {
                    "name": p.pillar,
                    "score": p.pillar_score,
                    "weight": p.weight,
                    "criteria": [
                        {
                            "name": c.name,
                            "score": c.score,
                            "weight": c.weight,
                            "reasoning": c.reasoning,
                            "strengths": c.strengths,
                            "weaknesses": c.weaknesses,
                        }
                        for c in p.criteria
                    ],
                }
                for p in self.pillars
            ],
            "judge_model": self.judge_model,
            "evaluation_time_ms": self.evaluation_time_ms,
        }


# =============================================================================
# EVALUATION RUBRICS - Elite Scoring Guidelines
# =============================================================================

PROMPT_QUALITY_RUBRIC = """
## PILLAR 1: PROMPT QUALITY EVALUATION

You are evaluating whether the PROMPT properly set up the agent for success.

### Elite Scoring Method (Context7 Pattern)
For each criterion, evaluate TWO dimensions:
1. **Completeness** (0.0-1.0): How much of the requirement was addressed?
2. **Quality Modifier** (0.0-1.0): How well was it done?

**Final Score = Completeness × Quality × 100**

Example:
- 90% complete + 95% quality = 0.90 × 0.95 × 100 = 85.5

### Criteria to Score (each 0-100):

**1.1 Clarity of Instructions (weight: 0.30)**
- 90-100: Crystal clear, unambiguous, any competent agent would understand exactly what to do
- 70-89: Clear overall, minor ambiguities that skilled agents can infer
- 50-69: Some confusion possible, key details missing or vague
- 30-49: Significant ambiguity, multiple valid interpretations exist
- 0-29: Confusing, contradictory, or missing critical instructions

**1.2 Specificity of Requirements (weight: 0.25)**
- 90-100: All requirements explicitly stated with measurable success criteria
- 70-89: Most requirements clear, success criteria mostly defined
- 50-69: General requirements stated but success criteria vague
- 30-49: Requirements implied rather than stated
- 0-29: No clear requirements, open to interpretation

**1.3 Brand Context Injection (weight: 0.25)**
- 90-100: Complete brand DNA provided (colors, themes, mood, target market, competitors)
- 70-89: Good brand context with most key elements
- 50-69: Basic brand info but missing nuances
- 30-49: Minimal brand context, agent must guess
- 0-29: No brand context or wrong brand info

**1.4 Technical Constraints (weight: 0.20)**
- 90-100: All technical requirements, formats, and constraints clearly specified
- 70-89: Main technical specs clear, some minor details assumed
- 50-69: General technical direction but specifics missing
- 30-49: Technical requirements vague or incomplete
- 0-29: No technical guidance provided
"""

EXECUTION_QUALITY_RUBRIC = """
## PILLAR 2: EXECUTION QUALITY EVALUATION

You are evaluating whether the RESPONSE delivered exactly what was asked.

### Elite Scoring Method
For each criterion: **Final Score = Completeness × Quality × 100**

### Criteria to Score (each 0-100):

**2.1 Task Completeness (weight: 0.30)**
- 90-100: Every single requirement addressed, nothing missing
- 70-89: All major requirements met, minor elements may be light
- 50-69: Most requirements addressed but notable gaps
- 30-49: Significant requirements missing
- 0-29: Failed to address core requirements

**2.2 Instruction Following (weight: 0.25)**
- 90-100: Followed all instructions precisely, no deviations
- 70-89: Followed instructions well with minor creative liberties
- 50-69: Generally followed but some instructions ignored
- 30-49: Significant deviation from instructions
- 0-29: Ignored or contradicted instructions

**2.3 Format Compliance (weight: 0.20)**
- 90-100: Perfect format (JSON valid, structure correct, all fields present)
- 70-89: Format mostly correct, minor issues
- 50-69: Format has issues but usable
- 30-49: Significant format problems
- 0-29: Wrong format or unparseable

**2.4 Innovation Within Constraints (weight: 0.25)**
- 90-100: Creative excellence while respecting all constraints
- 70-89: Good creativity within bounds
- 50-69: Safe/generic but acceptable
- 30-49: Either too conservative or broke constraints
- 0-29: No creativity or completely off-brief
"""

BRAND_DNA_RUBRIC = """
## PILLAR 3: BRAND DNA EVALUATION (HIGHEST WEIGHT - 45%)

You are evaluating whether the TARGET MARKET would instantly recognize the brand.
This is the MOST IMPORTANT pillar for creative market success.

### Elite Scoring Method
For each criterion: **Final Score = Completeness × Quality × 100**

### Criteria to Score (each 0-100):

**3.1 Visual Identity Alignment (weight: 0.25)**
- 90-100: Colors, typography, imagery perfectly match brand guidelines
- 70-89: Strong brand alignment with minor deviations
- 50-69: Recognizable as brand but inconsistencies present
- 30-49: Weak brand presence, could be any brand
- 0-29: Contradicts brand identity

**3.2 Emotional Tone Match (weight: 0.25)**
- 90-100: Perfectly captures brand emotion (luxury, passion, exclusivity)
- 70-89: Strong emotional alignment
- 50-69: Correct general tone but missing nuance
- 30-49: Tone inconsistent with brand
- 0-29: Wrong emotional register entirely

**3.3 Target Market Recognition (weight: 0.30)**
- 90-100: Target audience would INSTANTLY know this is [BRAND]
- 70-89: Target audience would recognize brand quickly
- 50-69: Would need brand name to identify
- 30-49: Could confuse with competitors
- 0-29: Target market would not recognize or reject

**3.4 Competitive Differentiation (weight: 0.20)**
- 90-100: Clearly stands apart from competitors with unique brand voice
- 70-89: Differentiated, some unique elements
- 50-69: Generic luxury feel, not distinctly THIS brand
- 30-49: Could be mistaken for competitor
- 0-29: Looks like competitor or commodity brand
"""

# =============================================================================
# JUDGE SYSTEM PROMPT
# =============================================================================

JUDGE_SYSTEM_PROMPT = """You are an ELITE creative director and brand strategist serving as a judge.

## THREE PILLARS (MANDATORY - USE EXACT NAMES)

Evaluate exactly these THREE pillars:

1. PROMPT_QUALITY (20% of total) - Was the agent properly set up?
   - clarity_of_instructions
   - specificity_of_requirements
   - brand_context_injection
   - technical_constraints

2. EXECUTION_QUALITY (35% of total) - Did they deliver what was asked?
   - task_completeness
   - instruction_following
   - format_compliance
   - innovation_within_constraints

3. BRAND_DNA (45% of total) - Will customers recognize the brand?
   - visual_identity_alignment
   - emotional_tone_match
   - target_market_recognition
   - competitive_differentiation

## SCORING SCALE
- 90-100: ELITE - Exceptional, production-ready
- 80-89: EXCELLENT - High quality
- 70-79: GOOD - Solid work
- 50-69: NEEDS_WORK - Issues to fix
- 0-49: FAIL - Does not meet requirements

## OUTPUT (STRICT JSON FORMAT)

Return ONLY valid JSON. The "pillars" MUST be an ARRAY with exactly 3 objects.
Each pillar object MUST have "name" (string) and "criteria" (array) fields.

{
  "pillars": [
    {
      "name": "PROMPT_QUALITY",
      "criteria": [
        {"name": "clarity_of_instructions", "score": 85, "reasoning": "...", "strengths": ["..."], "weaknesses": ["..."]},
        {"name": "specificity_of_requirements", "score": 80, "reasoning": "...", "strengths": [], "weaknesses": []},
        {"name": "brand_context_injection", "score": 90, "reasoning": "...", "strengths": [], "weaknesses": []},
        {"name": "technical_constraints", "score": 75, "reasoning": "...", "strengths": [], "weaknesses": []}
      ]
    },
    {
      "name": "EXECUTION_QUALITY",
      "criteria": [
        {"name": "task_completeness", "score": 88, "reasoning": "...", "strengths": [], "weaknesses": []},
        {"name": "instruction_following", "score": 85, "reasoning": "...", "strengths": [], "weaknesses": []},
        {"name": "format_compliance", "score": 95, "reasoning": "...", "strengths": [], "weaknesses": []},
        {"name": "innovation_within_constraints", "score": 78, "reasoning": "...", "strengths": [], "weaknesses": []}
      ]
    },
    {
      "name": "BRAND_DNA",
      "criteria": [
        {"name": "visual_identity_alignment", "score": 82, "reasoning": "...", "strengths": [], "weaknesses": []},
        {"name": "emotional_tone_match", "score": 80, "reasoning": "...", "strengths": [], "weaknesses": []},
        {"name": "target_market_recognition", "score": 75, "reasoning": "...", "strengths": [], "weaknesses": []},
        {"name": "competitive_differentiation", "score": 70, "reasoning": "...", "strengths": [], "weaknesses": []}
      ]
    }
  ],
  "total_score": 81.5,
  "verdict": "EXCELLENT",
  "summary": "Evaluation summary...",
  "recommendations": ["Recommendation 1", "Recommendation 2"]
}
"""

# =============================================================================
# BRAND DNA CONTEXT
# =============================================================================

SKYYROSE_BRAND_DNA = {
    "brand_name": "SkyyRose",
    "tagline": "Elevated Streetwear, Oakland Roots",
    "mission": "Bringing luxury to streetwear with rose gold elegance",
    "target_market": {
        "demographics": "25-40 year olds, urban professionals, fashion-forward",
        "psychographics": "Value quality over quantity, appreciate craftsmanship, seek exclusivity",
        "income": "Upper-middle to high income, willing to invest in statement pieces",
    },
    "collections": {
        "signature": {
            "theme": "Timeless Essentials",
            "mood": "Golden hour luxury garden, elegant pedestals, floating roses",
            "colors": {"primary": "#B76E79", "secondary": "#D4AF37", "accent": "#F5F5F0"},
            "style": "Classic, versatile, refined luxury",
        },
        "black-rose": {
            "theme": "Limited Edition Exclusivity",
            "mood": "Gothic night garden, moonlit, ethereal mystery",
            "colors": {"primary": "#C0C0C0", "secondary": "#0A0A0A", "accent": "#0a0a1a"},
            "style": "Mysterious, sophisticated, rare",
        },
        "love-hurts": {
            "theme": "Feel Everything",
            "mood": "Enchanted castle ballroom, Beauty & Beast inspiration",
            "colors": {"primary": "#DC143C", "secondary": "#800080", "accent": "#FFD700"},
            "style": "Passionate, vulnerable, powerful",
        },
    },
    "brand_voice": {
        "tone": "Confident but not arrogant, luxurious but accessible",
        "language": "Sophisticated, evocative, emotionally resonant",
        "avoid": ["cheap", "discount", "basic", "ordinary", "mass-produced"],
    },
    "visual_identity": {
        "primary_color": "#B76E79",  # Rose Gold
        "fonts": {"display": "Playfair Display", "body": "Inter"},
        "imagery": "High-contrast, editorial quality, rose motifs",
        "competitors_to_differentiate_from": ["Fashion Nova", "Shein", "Generic streetwear"],
    },
}


# =============================================================================
# CREATIVE JUDGE CLASS
# =============================================================================


class CreativeJudge:
    """
    Elite three-pillar LLM-as-judge for creative evaluations.

    Uses structured output to ensure consistent, parseable verdicts.
    """

    # Pillar weights (must sum to 1.0)
    PILLAR_WEIGHTS = {
        "PROMPT_QUALITY": 0.20,  # 20% - Setup matters
        "EXECUTION_QUALITY": 0.35,  # 35% - Did they do the job?
        "BRAND_DNA": 0.45,  # 45% - Creative market = brand is king
    }

    # Criteria weights within each pillar
    PROMPT_CRITERIA_WEIGHTS = {
        "clarity_of_instructions": 0.30,
        "specificity_of_requirements": 0.25,
        "brand_context_injection": 0.25,
        "technical_constraints": 0.20,
    }

    EXECUTION_CRITERIA_WEIGHTS = {
        "task_completeness": 0.30,
        "instruction_following": 0.25,
        "format_compliance": 0.20,
        "innovation_within_constraints": 0.25,
    }

    BRAND_CRITERIA_WEIGHTS = {
        "visual_identity_alignment": 0.25,
        "emotional_tone_match": 0.25,
        "target_market_recognition": 0.30,
        "competitive_differentiation": 0.20,
    }

    def __init__(
        self,
        judge_provider: str = "anthropic",  # or "openai"
        judge_model: str | None = None,
        brand_context: dict | None = None,
    ):
        """
        Initialize the Creative Judge.

        Args:
            judge_provider: Which LLM provider to use as judge
            judge_model: Specific model (defaults to best available)
            brand_context: Brand DNA to evaluate against (defaults to SkyyRose)
        """
        self.judge_provider = judge_provider
        self.judge_model = judge_model
        self.brand_context = brand_context or SKYYROSE_BRAND_DNA
        self._client = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the judge's LLM client."""
        if self._initialized:
            return

        if self.judge_provider == "anthropic":
            from llm.providers.anthropic import AnthropicClient

            self._client = AnthropicClient()
            self.judge_model = self.judge_model or "claude-sonnet-4-20250514"
        elif self.judge_provider == "openai":
            from llm.providers.openai import OpenAIClient

            self._client = OpenAIClient()
            self.judge_model = self.judge_model or "gpt-4o"
        else:
            raise ValueError(f"Unknown judge provider: {self.judge_provider}")

        self._initialized = True
        logger.info(f"CreativeJudge initialized with {self.judge_provider}/{self.judge_model}")

    async def evaluate(
        self,
        prompt: str,
        response: str,
        task_type: str = "creative_visual",
        collection: str | None = None,
        additional_context: dict | None = None,
    ) -> JudgeVerdict:
        """
        Evaluate a creative output using three-pillar LLM-as-judge.

        Args:
            prompt: The original prompt given to the agent
            response: The agent's response to evaluate
            task_type: Type of creative task (for context)
            collection: Specific collection being designed for
            additional_context: Any extra context for evaluation

        Returns:
            JudgeVerdict with scores, reasoning, and recommendations
        """
        import time

        start_time = time.time()

        if not self._initialized:
            await self.initialize()

        # Build the evaluation prompt
        eval_prompt = self._build_evaluation_prompt(
            prompt=prompt,
            response=response,
            task_type=task_type,
            collection=collection,
            additional_context=additional_context,
        )

        # Call the judge LLM
        from llm.base import Message

        messages = [Message.user(eval_prompt)]

        try:
            judge_response = await self._client.complete(
                messages=messages,
                system=JUDGE_SYSTEM_PROMPT,
                max_tokens=4096,
                temperature=0.1,  # Low temperature for consistent judging
            )

            # Parse the response
            verdict = self._parse_verdict(judge_response.content)
            verdict.judge_model = self.judge_model
            verdict.evaluation_time_ms = (time.time() - start_time) * 1000

            return verdict

        except Exception as e:
            logger.error(f"Judge evaluation failed: {e}")
            # Return a default verdict on error
            return JudgeVerdict(
                pillars=[],
                total_score=0.0,
                verdict=Verdict.FAIL,
                summary=f"Evaluation failed: {str(e)}",
                recommendations=["Fix evaluation error and retry"],
                judge_model=self.judge_model or "unknown",
                evaluation_time_ms=(time.time() - start_time) * 1000,
            )

    def _build_evaluation_prompt(
        self,
        prompt: str,
        response: str,
        task_type: str,
        collection: str | None,
        additional_context: dict | None,
    ) -> str:
        """Build the complete evaluation prompt for the judge."""

        # Get collection-specific brand context
        brand_info = self.brand_context.copy()
        if collection and collection in brand_info.get("collections", {}):
            brand_info["active_collection"] = brand_info["collections"][collection]

        return f"""
# CREATIVE OUTPUT EVALUATION

## Task Type
{task_type}

## Brand Context
```json
{json.dumps(brand_info, indent=2)}
```

## Original Prompt Given to Agent
```
{prompt}
```

## Agent's Response to Evaluate
```
{response}
```

{"## Additional Context" + chr(10) + json.dumps(additional_context, indent=2) if additional_context else ""}

---

# YOUR TASK

Evaluate this creative output using the THREE PILLARS:

{PROMPT_QUALITY_RUBRIC}

{EXECUTION_QUALITY_RUBRIC}

{BRAND_DNA_RUBRIC}

---

## PILLAR WEIGHTS FOR FINAL SCORE
- PROMPT_QUALITY: {self.PILLAR_WEIGHTS["PROMPT_QUALITY"] * 100}%
- EXECUTION_QUALITY: {self.PILLAR_WEIGHTS["EXECUTION_QUALITY"] * 100}%
- BRAND_DNA: {self.PILLAR_WEIGHTS["BRAND_DNA"] * 100}%

Calculate the weighted total score and provide your verdict.

**VERDICT SCALE:**
- ELITE (90-100): Exceptional, production-ready, award-worthy
- EXCELLENT (80-89): High quality, minor polish needed
- GOOD (70-79): Solid work, some improvements needed
- NEEDS_WORK (50-69): Significant issues to address
- FAIL (0-49): Does not meet requirements

Return your evaluation as a valid JSON object.
"""

    def _normalize_evaluation_format(self, eval_data: dict) -> dict:
        """
        Normalize various LLM response formats into standard format.

        Handles:
        - pillar_1_prompt_quality, pillar_2_execution_quality, pillar_3_brand_dna
        - criteria_scores vs criteria
        - Different naming conventions
        """
        pillar_mapping = {
            "pillar_1_prompt_quality": "PROMPT_QUALITY",
            "pillar_2_execution_quality": "EXECUTION_QUALITY",
            "pillar_3_brand_dna": "BRAND_DNA",
            "prompt_quality": "PROMPT_QUALITY",
            "execution_quality": "EXECUTION_QUALITY",
            "brand_dna": "BRAND_DNA",
        }

        pillars = []
        total_weighted_score = 0.0
        total_weight = 0.0

        for key, pillar_name in pillar_mapping.items():
            if key not in eval_data:
                continue

            pillar_data = eval_data[key]
            criteria_data = pillar_data.get("criteria_scores") or pillar_data.get("criteria", {})

            criteria = []
            for crit_name, crit_data in criteria_data.items():
                if isinstance(crit_data, dict):
                    score = crit_data.get("score", 0)
                    criteria.append(
                        {
                            "name": crit_name,
                            "score": float(score),
                            "reasoning": crit_data.get("reasoning", ""),
                            "strengths": crit_data.get("strengths", []),
                            "weaknesses": crit_data.get("weaknesses", []),
                            "completeness": crit_data.get("completeness", 1.0),
                            "quality_modifier": crit_data.get("quality", 1.0),
                        }
                    )

            pillar_weight = pillar_data.get("weight", self.PILLAR_WEIGHTS.get(pillar_name, 0.33))
            pillar_score = pillar_data.get("weighted_score", 0) or pillar_data.get("score", 0)

            # If no pillar score, compute from criteria
            if not pillar_score and criteria:
                pillar_score = sum(c["score"] for c in criteria) / len(criteria)

            pillars.append(
                {
                    "name": pillar_name,
                    "criteria": criteria,
                    "pillar_score": float(pillar_score),
                }
            )

            total_weighted_score += float(pillar_score) * float(pillar_weight)
            total_weight += float(pillar_weight)

        # Calculate total score
        total_score = total_weighted_score / total_weight if total_weight > 0 else 0.0

        # Determine verdict based on score
        if total_score >= 90:
            verdict = "ELITE"
        elif total_score >= 80:
            verdict = "EXCELLENT"
        elif total_score >= 70:
            verdict = "GOOD"
        elif total_score >= 50:
            verdict = "NEEDS_WORK"
        else:
            verdict = "FAIL"

        # Use final_weighted_score if present
        if "final_weighted_score" in eval_data:
            total_score = float(eval_data["final_weighted_score"])
            # Recalculate verdict from actual score
            if total_score >= 90:
                verdict = "ELITE"
            elif total_score >= 80:
                verdict = "EXCELLENT"
            elif total_score >= 70:
                verdict = "GOOD"
            elif total_score >= 50:
                verdict = "NEEDS_WORK"
            else:
                verdict = "FAIL"

        # Get verdict from response if present
        if "verdict" in eval_data:
            verdict = eval_data["verdict"]

        return {
            "pillars": pillars,
            "total_score": total_score,
            "verdict": verdict,
            "summary": eval_data.get("summary", eval_data.get("overall_assessment", "")),
            "recommendations": eval_data.get("recommendations", []),
        }

    def _normalize_pillars_object(self, data: dict) -> dict:
        """Handle when pillars is a dict instead of array."""
        pillars_obj = data.get("pillars", {})
        pillars = []

        for pillar_name, pillar_data in pillars_obj.items():
            criteria = []
            for crit_name, crit_data in pillar_data.get("criteria", {}).items():
                criteria.append(
                    {
                        "name": crit_name,
                        "score": float(crit_data.get("score", 0)),
                        "reasoning": crit_data.get("reasoning", ""),
                        "strengths": crit_data.get("strengths", []),
                        "weaknesses": crit_data.get("weaknesses", []),
                    }
                )

            pillars.append(
                {
                    "name": pillar_name,
                    "criteria": criteria,
                }
            )

        return {
            "pillars": pillars,
            "total_score": data.get("total_score", 0.0),
            "verdict": data.get("verdict", "FAIL"),
            "summary": data.get("summary", ""),
            "recommendations": data.get("recommendations", []),
        }

    def _parse_verdict(self, content: str) -> JudgeVerdict:
        """Parse the judge's response into a JudgeVerdict.

        Handles multiple response formats from different LLMs:
        - Standard: {"pillars": [{"name": "...", "criteria": [...]}]}
        - Alternative: {"evaluation": {"pillar_1_prompt_quality": {...}}}
        - Object style: {"pillars": {"PROMPT_QUALITY": {...}}}
        """

        # Extract JSON from response
        json_str = content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0]

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse judge response: {e}")
            logger.error(f"Content: {content[:500]}")
            raise ValueError(f"Judge returned invalid JSON: {e}")

        # Handle different response formats
        # Case 1: "evaluation" wrapper
        if "evaluation" in data and "pillars" not in data:
            data = self._normalize_evaluation_format(data["evaluation"])
        # Case 2: pillar_X keys at root level (no wrapper)
        elif "pillar_1_prompt_quality" in data or "pillar_2_execution_quality" in data:
            data = self._normalize_evaluation_format(data)
        # Case 3: pillars as object (not array)
        elif "pillars" in data and isinstance(data["pillars"], dict):
            data = self._normalize_pillars_object(data)

        # Build pillar scores
        pillars = []
        for pillar_data in data.get("pillars", []):
            pillar_name = pillar_data.get("name", "")
            pillar_weight = self.PILLAR_WEIGHTS.get(pillar_name, 0.33)

            # Get criteria weights for this pillar
            if pillar_name == "PROMPT_QUALITY":
                criteria_weights = self.PROMPT_CRITERIA_WEIGHTS
            elif pillar_name == "EXECUTION_QUALITY":
                criteria_weights = self.EXECUTION_CRITERIA_WEIGHTS
            elif pillar_name == "BRAND_DNA":
                criteria_weights = self.BRAND_CRITERIA_WEIGHTS
            else:
                criteria_weights = {}

            criteria = []
            for c in pillar_data.get("criteria", []):
                criterion_name = c.get("name", "")

                # Extract quality modifier components
                completeness = float(c.get("completeness", 1.0))
                quality_mod = float(c.get("quality_modifier", 1.0))

                # Use explicit score if provided, else compute from modifiers
                explicit_score = c.get("score")
                if explicit_score is not None:
                    score = float(explicit_score)
                else:
                    score = completeness * quality_mod * 100

                criteria.append(
                    CriterionScore(
                        name=criterion_name,
                        score=score,
                        weight=criteria_weights.get(criterion_name, 0.25),
                        reasoning=c.get("reasoning", ""),
                        strengths=c.get("strengths", []),
                        weaknesses=c.get("weaknesses", []),
                        completeness=completeness,
                        quality_modifier=quality_mod,
                    )
                )

            pillars.append(
                PillarScore(
                    pillar=pillar_name,
                    criteria=criteria,
                    weight=pillar_weight,
                )
            )

        # Calculate total score
        total_score = data.get("total_score", 0.0)
        if not total_score and pillars:
            # Calculate from pillars if not provided
            total_weight = sum(p.weight for p in pillars)
            if total_weight > 0:
                total_score = sum(p.weighted_score for p in pillars) / total_weight

        # Determine verdict
        verdict_str = data.get("verdict", "FAIL")
        try:
            verdict = Verdict(verdict_str)
        except ValueError:
            # Fallback based on score
            if total_score >= 90:
                verdict = Verdict.ELITE
            elif total_score >= 80:
                verdict = Verdict.EXCELLENT
            elif total_score >= 70:
                verdict = Verdict.GOOD
            elif total_score >= 50:
                verdict = Verdict.NEEDS_WORK
            else:
                verdict = Verdict.FAIL

        return JudgeVerdict(
            pillars=pillars,
            total_score=total_score,
            verdict=verdict,
            summary=data.get("summary", ""),
            recommendations=data.get("recommendations", []),
            judge_model="",  # Set by caller
            evaluation_time_ms=0.0,  # Set by caller
        )

    async def compare(
        self,
        prompt: str,
        responses: list[tuple[str, str]],  # [(provider_name, response), ...]
        task_type: str = "creative_visual",
        collection: str | None = None,
    ) -> list[tuple[str, JudgeVerdict]]:
        """
        Compare multiple responses and rank them.

        Args:
            prompt: The original prompt
            responses: List of (provider_name, response) tuples
            task_type: Type of creative task
            collection: Specific collection

        Returns:
            List of (provider_name, verdict) sorted by score descending
        """
        import asyncio

        # Evaluate all responses in parallel
        tasks = [
            self.evaluate(
                prompt=prompt,
                response=response,
                task_type=task_type,
                collection=collection,
                additional_context={"provider": provider},
            )
            for provider, response in responses
        ]

        verdicts = await asyncio.gather(*tasks, return_exceptions=True)

        # Pair with providers and filter errors - hardened
        results = []
        for (provider, _), verdict in zip(responses, verdicts, strict=False):
            if verdict is None:
                logger.error(f"Evaluation returned None for {provider}")
                continue
            if isinstance(verdict, Exception):
                logger.error(f"Evaluation failed for {provider}: {verdict}")
                continue
            if not hasattr(verdict, "total_score"):
                logger.error(f"Invalid verdict type for {provider}: {type(verdict)}")
                continue
            results.append((provider, verdict))

        if not results:
            logger.warning("All evaluations failed - returning empty results")
            return []

        # Sort by total score descending - with None guard
        def safe_score(item):
            _, verdict = item
            score = getattr(verdict, "total_score", None)
            return float(score) if score is not None else 0.0

        results.sort(key=safe_score, reverse=True)

        return results


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


async def judge_creative_output(
    prompt: str,
    response: str,
    collection: str | None = None,
    judge_provider: str = "anthropic",
) -> JudgeVerdict:
    """
    Convenience function to judge a single creative output.

    Example:
        verdict = await judge_creative_output(
            prompt="Design a Three.js scene for the Signature collection...",
            response='{"scene_name": "Golden Hour Garden", ...}',
            collection="signature",
        )
        print(f"Score: {verdict.total_score}, Verdict: {verdict.verdict}")
    """
    judge = CreativeJudge(judge_provider=judge_provider)
    await judge.initialize()
    return await judge.evaluate(
        prompt=prompt,
        response=response,
        collection=collection,
    )


async def compare_creative_outputs(
    prompt: str,
    responses: list[tuple[str, str]],
    collection: str | None = None,
    judge_provider: str = "anthropic",
) -> list[tuple[str, JudgeVerdict]]:
    """
    Convenience function to compare multiple creative outputs.

    Example:
        results = await compare_creative_outputs(
            prompt="Design a Three.js scene...",
            responses=[
                ("openai", '{"scene_name": "Sunset Rose"...}'),
                ("anthropic", '{"scene_name": "Twilight Garden"...}'),
            ],
            collection="signature",
        )

        for provider, verdict in results:
            print(f"{provider}: {verdict.total_score} - {verdict.verdict}")
    """
    judge = CreativeJudge(judge_provider=judge_provider)
    await judge.initialize()
    return await judge.compare(
        prompt=prompt,
        responses=responses,
        collection=collection,
    )

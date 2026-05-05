"""Tournament judging — 3-judge architecture (vision pair + synthesis).

Architecture:
- GPT-5.5-Pro and Gemini 3.1 Pro Preview run in parallel as VISION
  judges, each comparing the candidate image against the source spec
  image and producing a structured 7-axis score.
- Claude Opus 4.7 then runs as a TEXT-ONLY SYNTHESIS judge: it reads the
  two vision reports + the DNA spec and produces a final reasoned
  judgment, including a rationale, vision-consensus signal, and a
  hallucination veto. Opus is intentionally NOT given the images — its
  job is to leverage its reasoning strength over structured input, not
  duplicate the vision judges' work.

Aggregate score is Opus's `overall`. The vision-pair mean is exposed on
TournamentResult as a sanity check on Opus's reasoning, not as the
canonical aggregate. See scripts/nano_banana/CURRENT_MODELS.md for
verified model IDs and SDK contracts.
"""

from __future__ import annotations

import base64
import concurrent.futures
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

# Vision judges — evaluate source vs candidate images directly.
# Newest+best models from each provider (verified against live model
# catalogs on 2026-05-04 — see scripts/nano_banana/CURRENT_MODELS.md).
GPT_JUDGE_MODEL = "gpt-5.5-pro"
GEMINI_JUDGE_MODEL = "gemini-3.1-pro-preview"

# Synthesis judge — text-only. Opus reads the two vision reports + the DNA
# spec and returns a final verdict with rationale. Uses adaptive thinking
# with summarized display so the SDK returns visible reasoning blocks
# alongside the JSON answer. NO budget_tokens (removed on Opus 4.7); NO
# temperature/top_p/top_k (also removed).
OPUS_SYNTHESIS_MODEL = "claude-opus-4-7"


JUDGE_PROMPT = """You are a strict QA inspector for a luxury fashion brand.
Compare the GENERATED image to the SOURCE reference image + PRODUCT SPEC.

SOURCE (ground truth):
{spec}

Rate the generated image on these criteria (0-100 each):
- garment_type: Does the rendered garment match the specified type?
- color_accuracy: Does the base color match the target hex?
- text_accuracy: Is all specified text rendered correctly (spelling, placement, color)?
- logo_accuracy: Are logos at correct positions with correct size/material?
- construction_accuracy: Are construction details (panels, seams, buttons) correct?
- no_hallucinations: Does it AVOID adding text/logos/details NOT in the spec?

Return ONLY valid JSON (no markdown):
{{
  "garment_type": 0-100,
  "color_accuracy": 0-100,
  "text_accuracy": 0-100,
  "logo_accuracy": 0-100,
  "construction_accuracy": 0-100,
  "no_hallucinations": 0-100,
  "overall": 0-100,
  "issues": ["specific problem 1", "specific problem 2"],
  "suggested_fixes": ["fix 1", "fix 2"]
}}

Be strict. Give low scores for: wrong colors, misspelled text, missing logos,
hallucinated extras, wrong garment type, incorrect construction.
"""


SYNTHESIS_PROMPT = """You are the head QA inspector for a luxury fashion brand.
Two vision judges have already evaluated a generated product image against a
spec. They each looked at the SOURCE reference image and the GENERATED image
and produced 0-100 scores across six accuracy dimensions plus an overall
score, plus issues and suggested fixes. You will NOT see the images. Your
job is to reason over their structured reports + the canonical product spec
and produce the FINAL verdict.

Your role is synthesis, not duplication. Specifically:
- Reconcile disagreement between the two vision judges. If they diverge,
  reason about which is more credible given the spec and the issue lists.
- Apply a hallucination veto. If either vision judge flags hallucinated
  text, logos, or details that aren't in the spec, you MUST cap the overall
  score regardless of the vision judges' overall numbers — hallucinations
  are disqualifying for a luxury brand.
- Identify consensus signal. Where the vision judges agree on a problem,
  that's high-confidence and should drive the issues list.
- Be stricter than the vision pair when warranted. The vision judges score
  what they see; you score what ships.

PRODUCT SPEC (ground truth):
{spec}

--- VISION JUDGE 1: {gpt_model} ---
Overall: {gpt_overall}/100
garment_type: {gpt_garment_type}, color_accuracy: {gpt_color_accuracy},
text_accuracy: {gpt_text_accuracy}, logo_accuracy: {gpt_logo_accuracy},
construction_accuracy: {gpt_construction_accuracy}, no_hallucinations: {gpt_no_hallucinations}
Issues: {gpt_issues}
Suggested fixes: {gpt_fixes}

--- VISION JUDGE 2: {gemini_model} ---
Overall: {gemini_overall}/100
garment_type: {gemini_garment_type}, color_accuracy: {gemini_color_accuracy},
text_accuracy: {gemini_text_accuracy}, logo_accuracy: {gemini_logo_accuracy},
construction_accuracy: {gemini_construction_accuracy}, no_hallucinations: {gemini_no_hallucinations}
Issues: {gemini_issues}
Suggested fixes: {gemini_fixes}

Return ONLY valid JSON (no markdown):
{{
  "garment_type": 0-100,
  "color_accuracy": 0-100,
  "text_accuracy": 0-100,
  "logo_accuracy": 0-100,
  "construction_accuracy": 0-100,
  "no_hallucinations": 0-100,
  "overall": 0-100,
  "rationale": "2-3 sentence explanation of how you reconciled the two vision judges",
  "vision_consensus": "agree" | "partial" | "disagree",
  "hallucination_veto": true | false,
  "issues": ["consensus issue 1", "consensus issue 2"],
  "suggested_fixes": ["fix 1", "fix 2"]
}}
"""


@dataclass
class JudgmentScore:
    """A single judge's scoring of a candidate.

    Vision judges (GPT, Gemini) populate the six accuracy axes + overall +
    issues/fixes. The synthesis judge (Opus) additionally populates
    `rationale`, `vision_consensus`, and `hallucination_veto`; for vision
    judges those three fields stay at their defaults.
    """

    judge: str
    garment_type: int
    color_accuracy: int
    text_accuracy: int
    logo_accuracy: int
    construction_accuracy: int
    no_hallucinations: int
    overall: int
    issues: list[str]
    suggested_fixes: list[str]
    raw_response: str = ""
    rationale: str = ""
    vision_consensus: str = ""
    hallucination_veto: bool = False
    # `available=False` marks zero-score placeholder judgments
    # (missing client OR infrastructure failure). Filtering on this
    # boolean is more robust than parsing the judge string suffix.
    available: bool = True

    def to_dict(self) -> dict:
        d = {
            "judge": self.judge,
            "overall": self.overall,
            "scores": {
                "garment_type": self.garment_type,
                "color_accuracy": self.color_accuracy,
                "text_accuracy": self.text_accuracy,
                "logo_accuracy": self.logo_accuracy,
                "construction_accuracy": self.construction_accuracy,
                "no_hallucinations": self.no_hallucinations,
            },
            "issues": self.issues,
            "suggested_fixes": self.suggested_fixes,
        }
        if self.rationale or self.vision_consensus or self.hallucination_veto:
            d["synthesis"] = {
                "rationale": self.rationale,
                "vision_consensus": self.vision_consensus,
                "hallucination_veto": self.hallucination_veto,
            }
        return d


@dataclass
class TournamentResult:
    """Aggregate result from 3-judge tournament.

    `aggregate_score` is the canonical headline score:
    - With synthesis: equals `synthesis_overall` (Opus's reasoned verdict).
    - Without synthesis: equals `vision_pair_mean` as a coverage-degraded fallback.

    `vision_pair_mean` is exposed independently as a sanity check on the
    synthesis verdict — large divergence between the two signals a
    reasoning gap and is a useful production-monitoring tripwire.
    """

    candidate_path: str
    judges: list[JudgmentScore]
    aggregate_score: float  # 0-100
    passed_98: bool
    top_issues: list[str] = field(default_factory=list)
    all_fixes: list[str] = field(default_factory=list)
    vision_pair_mean: float = 0.0
    synthesis_overall: float | None = None

    @property
    def synthesis_judge(self) -> JudgmentScore | None:
        """Return the Opus synthesis judge if it ran, else None.

        Match by model label against OPUS_SYNTHESIS_MODEL. If synthesis
        failed, the JudgmentScore is still emitted with that label —
        callers can detect failure via `j.overall == 0` and `j.issues`.
        """
        return next((j for j in self.judges if j.judge == OPUS_SYNTHESIS_MODEL), None)

    def to_dict(self) -> dict:
        return {
            "candidate_path": self.candidate_path,
            "aggregate_score": self.aggregate_score,
            "vision_pair_mean": self.vision_pair_mean,
            "synthesis_overall": self.synthesis_overall,
            "passed_98": self.passed_98,
            "top_issues": self.top_issues,
            "all_fixes": self.all_fixes,
            "judges": [j.to_dict() for j in self.judges],
        }


# -- Image loading helpers --------------------------------------------------


def _load_image_b64(image_path: Path) -> tuple[str, str]:
    ext = image_path.suffix.lower()
    mime = (
        "image/jpeg"
        if ext in (".jpg", ".jpeg")
        else "image/webp" if ext == ".webp" else "image/png"
    )
    return base64.b64encode(image_path.read_bytes()).decode("utf-8"), mime


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fallback: try to repair truncated JSON by closing braces/brackets
    import re

    for suffix in ["}", "]}", '"]}']:
        try:
            # Find last complete key-value pair and close the object
            repaired = text.rstrip().rstrip(",") + suffix
            result = json.loads(repaired)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            continue
    # Last resort: extract individual numeric fields with regex
    fields = {}
    for key in (
        "garment_type",
        "color_accuracy",
        "text_accuracy",
        "logo_accuracy",
        "construction_accuracy",
        "no_hallucinations",
        "overall",
    ):
        m = re.search(rf'"{key}"\s*:\s*(\d+)', text)
        if m:
            fields[key] = int(m.group(1))
    return fields


def _dna_to_spec(dna: dict) -> str:
    """Convert DNA dict to human-readable spec for judge prompt.

    If `dna["spec"]` is a non-empty string, use it verbatim as the spec.
    This is the canonical-dossier path — `nano_banana.spec_builder.build_dna_from_sku`
    populates this field with the full multi-section dossier text so
    judges score against authored truth instead of inferred DNA.

    Without `spec` (legacy path), fall back to building prose from the
    flat fields. This path is lossy — it cannot represent per-element
    trim colors, the negative list, or technique distinctions
    (embossed vs embroidered vs printed). New code should populate
    `spec` instead.
    """
    spec_override = dna.get("spec")
    if isinstance(spec_override, str) and spec_override.strip():
        return spec_override

    lines = []
    lines.append(f"Garment: {dna.get('garment_type', 'N/A')}")
    lines.append(f"Base color: {dna.get('base_color', 'N/A')} ({dna.get('base_color_name', '')})")
    if dna.get("text_content"):
        text_items = []
        for t in dna["text_content"]:
            if isinstance(t, dict) and t.get("text"):
                text_items.append(f'"{t["text"]}" at {t.get("location", "?")}')
        if text_items:
            lines.append(f"Text: {'; '.join(text_items)}")
    if dna.get("logos"):
        logo_items = []
        for lg in dna["logos"]:
            if isinstance(lg, dict):
                logo_items.append(f"{lg.get('type', 'logo')} at {lg.get('position', '?')}")
        if logo_items:
            lines.append(f"Logos: {'; '.join(logo_items)}")
    if dna.get("construction"):
        construction = dna["construction"]
        if isinstance(construction, dict):
            lines.append(
                f"Construction: {', '.join(f'{k}: {v}' for k, v in list(construction.items())[:5])}"
            )
        elif isinstance(construction, list):
            lines.append(f"Construction: {', '.join(construction[:5])}")
    if dna.get("fabric"):
        lines.append(f"Fabric: {dna['fabric']}")
    return "\n".join(lines)


def _build_judgment_from_json(judge_name: str, data: dict, raw: str) -> JudgmentScore:
    """Convert parsed JSON response to JudgmentScore."""

    def _get(key, default=0):
        v = data.get(key, default)
        try:
            return int(v)
        except (ValueError, TypeError):
            return default

    return JudgmentScore(
        judge=judge_name,
        garment_type=_get("garment_type"),
        color_accuracy=_get("color_accuracy"),
        text_accuracy=_get("text_accuracy"),
        logo_accuracy=_get("logo_accuracy"),
        construction_accuracy=_get("construction_accuracy"),
        no_hallucinations=_get("no_hallucinations"),
        overall=_get("overall"),
        issues=data.get("issues", []) or [],
        suggested_fixes=data.get("suggested_fixes", []) or [],
        raw_response=raw,
        rationale=str(data.get("rationale", "") or ""),
        vision_consensus=str(data.get("vision_consensus", "") or ""),
        hallucination_veto=bool(data.get("hallucination_veto", False)),
    )


# -- Judge implementations --------------------------------------------------
#
# Each judge function (judge_with_gpt / _claude / _gemini) is a thin wrapper
# around the shared `judge_with` scaffold below. The scaffold handles image
# loading, JSON parsing, error logging, and zero-score construction; each
# provider supplies a small adapter (`_judge_call_*`) that knows how to
# call its specific API and extract the response text.


# Constrained-decoding schema for GPT — same shape as Gemini's so the
# JSON parser handles both identically. The Responses API's
# `text.format=json_schema` guarantees the output validates against this
# shape, eliminating the markdown-fence repair fallbacks.
_GPT_JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "garment_type": {"type": "integer"},
        "color_accuracy": {"type": "integer"},
        "text_accuracy": {"type": "integer"},
        "logo_accuracy": {"type": "integer"},
        "construction_accuracy": {"type": "integer"},
        "no_hallucinations": {"type": "integer"},
        "overall": {"type": "integer"},
        "issues": {"type": "array", "items": {"type": "string"}},
        "suggested_fixes": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "garment_type",
        "color_accuracy",
        "text_accuracy",
        "logo_accuracy",
        "construction_accuracy",
        "no_hallucinations",
        "overall",
        "issues",
        "suggested_fixes",
    ],
    "additionalProperties": False,
}


def _judge_call_gpt(
    client,
    source_path: Path,
    candidate_path: Path,
    src_b64: str,
    src_mime: str,
    cand_b64: str,
    cand_mime: str,
    spec: str,
) -> str:
    """Call GPT-5.5-pro vision judge via the Responses API.

    GPT-5.5-Pro SDK contract notes (verified via Context7 against the
    OpenAI Responses-API docs):
    - Pro-tier reasoning models route through `client.responses.create()`,
      NOT `chat.completions.create()`. The earlier empty-error failure
      came from using the wrong API surface.
    - Reasoning is configured via `reasoning={"effort": "high"}` (NOT
      `reasoning_effort="high"` like Chat Completions).
    - Vision input uses `{"type": "input_image", "image_url": "data:..."}`
      with the data URL inline. Text input uses `{"type": "input_text"}`.
      These differ from Chat Completions (`type: "image_url"` /
      `type: "text"`).
    - Token cap is `max_output_tokens` (NOT `max_tokens` /
      `max_completion_tokens`).
    - Structured JSON output via `text={"format": {"type": "json_schema",
      ...}}` — gives us schema-guaranteed output, mirroring Gemini's
      constrained decoding. No markdown fences to strip.
    - Output is read via `response.output_text` (the convenience
      accessor) which concatenates all text blocks across the output
      array, skipping reasoning blocks.
    """
    response = client.responses.create(
        model=GPT_JUDGE_MODEL,
        reasoning={"effort": "high"},
        max_output_tokens=16384,
        text={
            "format": {
                "type": "json_schema",
                "name": "judge_response",
                "strict": True,
                "schema": _GPT_JUDGE_SCHEMA,
            }
        },
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": JUDGE_PROMPT.format(spec=spec)
                        + "\n\nIMAGE 1 = SOURCE, IMAGE 2 = GENERATED",
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:{src_mime};base64,{src_b64}",
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:{cand_mime};base64,{cand_b64}",
                    },
                ],
            }
        ],
    )
    return response.output_text or ""


def _format_synthesis_prompt(spec: str, gpt: JudgmentScore, gemini: JudgmentScore) -> str:
    """Format the synthesis prompt with spec + the two vision reports.

    Issue/fix lists are joined with `; ` so they read inline; empty lists
    render as `(none)` so Opus can recognize the absence rather than
    pattern-match an empty string.
    """

    def _fmt_list(items: list[str]) -> str:
        return "; ".join(items) if items else "(none)"

    return SYNTHESIS_PROMPT.format(
        spec=spec,
        gpt_model=GPT_JUDGE_MODEL,
        gemini_model=GEMINI_JUDGE_MODEL,
        gpt_overall=gpt.overall,
        gpt_garment_type=gpt.garment_type,
        gpt_color_accuracy=gpt.color_accuracy,
        gpt_text_accuracy=gpt.text_accuracy,
        gpt_logo_accuracy=gpt.logo_accuracy,
        gpt_construction_accuracy=gpt.construction_accuracy,
        gpt_no_hallucinations=gpt.no_hallucinations,
        gpt_issues=_fmt_list(gpt.issues),
        gpt_fixes=_fmt_list(gpt.suggested_fixes),
        gemini_overall=gemini.overall,
        gemini_garment_type=gemini.garment_type,
        gemini_color_accuracy=gemini.color_accuracy,
        gemini_text_accuracy=gemini.text_accuracy,
        gemini_logo_accuracy=gemini.logo_accuracy,
        gemini_construction_accuracy=gemini.construction_accuracy,
        gemini_no_hallucinations=gemini.no_hallucinations,
        gemini_issues=_fmt_list(gemini.issues),
        gemini_fixes=_fmt_list(gemini.suggested_fixes),
    )


def _opus_synthesis_call(client, gpt: JudgmentScore, gemini: JudgmentScore, dna: dict) -> str:
    """Call Opus 4.7 in text-only synthesis mode.

    SDK contract notes (Opus 4.7, verified via Context7 against the
    Anthropic Python SDK + the migration guide):
    - Use `thinking={"type": "adaptive", "display": "summarized"}`. Adaptive
      is the only on-mode for 4.7; `enabled`+`budget_tokens` returns 400.
      `display: "summarized"` makes thinking-block text visible in the
      response (default is `omitted` on 4.7).
    - `effort` lives inside `output_config`, not at the top level. `xhigh`
      sits between `high` and `max` and is the recommended default for
      reasoning-heavy work on 4.7.
    - No `temperature`/`top_p`/`top_k` — those are removed on 4.7.
    """
    spec = _dna_to_spec(dna)
    prompt = _format_synthesis_prompt(spec, gpt, gemini)
    response = client.messages.create(
        model=OPUS_SYNTHESIS_MODEL,
        max_tokens=4096,
        thinking={"type": "adaptive", "display": "summarized"},
        output_config={"effort": "xhigh"},
        messages=[{"role": "user", "content": prompt}],
    )
    # Concatenate text blocks; ignore thinking blocks (they're for
    # transparency, not the structured answer).
    parts = []
    for block in response.content:
        block_type = getattr(block, "type", None)
        if block_type == "text":
            parts.append(getattr(block, "text", "") or "")
    return "\n".join(parts)


def judge_with_opus_synthesis(
    client,
    gpt: JudgmentScore,
    gemini: JudgmentScore,
    dna: dict,
) -> JudgmentScore:
    """Run the Opus synthesis judge over the two vision reports.

    On any failure (API error, JSON parse miss, empty response) returns a
    zero-score `JudgmentScore` mirroring the vision-scaffold contract so
    downstream aggregation stays uniform.
    """
    try:
        text = _opus_synthesis_call(client, gpt, gemini, dna)
        data = _parse_json(text)
        if not data:
            raise ValueError(f"Empty JSON parse from: {(text or '')[:200]}")
        return _build_judgment_from_json(OPUS_SYNTHESIS_MODEL, data, text)
    except Exception as exc:
        log.error("opus synthesis judge failed: %s", exc)
        return JudgmentScore(
            OPUS_SYNTHESIS_MODEL,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            [f"synthesis error: {exc}"],
            [],
            "",
        )


# Constrained decoding schema for Gemini — guarantees complete, valid JSON output
_GEMINI_JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "garment_type": {"type": "integer"},
        "color_accuracy": {"type": "integer"},
        "text_accuracy": {"type": "integer"},
        "logo_accuracy": {"type": "integer"},
        "construction_accuracy": {"type": "integer"},
        "no_hallucinations": {"type": "integer"},
        "overall": {"type": "integer"},
        "issues": {"type": "array", "items": {"type": "string"}},
        "suggested_fixes": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "garment_type",
        "color_accuracy",
        "text_accuracy",
        "logo_accuracy",
        "construction_accuracy",
        "no_hallucinations",
        "overall",
        "issues",
        "suggested_fixes",
    ],
}


def _judge_call_gemini(
    client,
    source_path: Path,
    candidate_path: Path,
    src_b64: str,
    src_mime: str,
    cand_b64: str,
    cand_mime: str,
    spec: str,
) -> str:
    """Call Gemini 3.1 Pro vision judge with dynamic thinking.

    Gemini 3 / 3.1 SDK contract notes:
    - `thinking_budget=-1` puts the model in dynamic mode where it
      self-allocates reasoning tokens based on task complexity. For
      Gemini 3+ thinking-native models this beats fixed budgets — the
      model knows better than we do how much reasoning a given image
      comparison needs. The old `8192` fixed cap was tuned for 2.5-flash;
      3.1-pro routinely wants more for fine-grained QA.
    - `max_output_tokens` bumped 4096 → 16384 because reasoning + the
      JSON answer share the budget. Constrained decoding via
      `response_schema` ensures the answer block is well-formed
      regardless of how much reasoning the model emits.
    - `temperature=1.0` retained — judging-as-sampling, not deterministic.
    """
    from google.genai import types

    response = client.models.generate_content(
        model=GEMINI_JUDGE_MODEL,
        contents=[
            "IMAGE 1 = SOURCE reference (ground truth):",
            types.Part.from_bytes(data=source_path.read_bytes(), mime_type=src_mime),
            "IMAGE 2 = GENERATED (evaluate against spec):",
            types.Part.from_bytes(data=candidate_path.read_bytes(), mime_type=cand_mime),
            JUDGE_PROMPT.format(spec=spec),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=_GEMINI_JUDGE_SCHEMA,
            max_output_tokens=16384,
            temperature=1.0,
            thinking_config=types.ThinkingConfig(thinking_budget=-1),
        ),
    )
    # Extract text from parts, skipping thought parts
    text_parts = []
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if hasattr(part, "text") and part.text:
                text_parts.append(part.text)
    return "\n".join(text_parts) if text_parts else (response.text or "")


def judge_with(
    model_label: str,
    call_fn,
    client,
    source_path: Path,
    candidate_path: Path,
    dna: dict,
) -> JudgmentScore:
    """Shared judge scaffold: load images, call provider adapter, parse JSON, build judgment.

    The adapter `call_fn` is a `_judge_call_*` function that takes the client,
    pre-loaded image data, and a spec string, then returns raw response text.
    This scaffold normalizes error handling: any exception (API failure, JSON
    parse miss, empty response) returns a zero-score `JudgmentScore` with the
    error encoded in `issues`. Empty-JSON detection used to be Gemini-only;
    now it applies to all three judges as a strict improvement (consistent
    zero-score on empty rather than silently passing empty data downstream).
    """
    src_b64, src_mime = _load_image_b64(source_path)
    cand_b64, cand_mime = _load_image_b64(candidate_path)
    spec = _dna_to_spec(dna)
    try:
        text = call_fn(
            client, source_path, candidate_path, src_b64, src_mime, cand_b64, cand_mime, spec
        )
        data = _parse_json(text)
        if not data:
            raise ValueError(f"Empty JSON parse from: {(text or '')[:200]}")
        return _build_judgment_from_json(model_label, data, text)
    except Exception as exc:
        log.error("%s judge failed: %s", model_label, exc)
        return JudgmentScore(model_label, 0, 0, 0, 0, 0, 0, 0, [f"judge error: {exc}"], [], "")


def judge_with_gpt(client, source_path: Path, candidate_path: Path, dna: dict) -> JudgmentScore:
    return judge_with(GPT_JUDGE_MODEL, _judge_call_gpt, client, source_path, candidate_path, dna)


def judge_with_gemini(client, source_path: Path, candidate_path: Path, dna: dict) -> JudgmentScore:
    return judge_with(
        GEMINI_JUDGE_MODEL, _judge_call_gemini, client, source_path, candidate_path, dna
    )


# -- Tournament orchestration -----------------------------------------------
#
# Two role groups now:
#   VISION_JUDGE_LABELS — providers that look at images directly. Run in
#                         parallel; each produces an independent judgment.
#   SYNTHESIS_JUDGE_LABEL — single text-only judge that reasons over the
#                           vision pair. Runs after both vision judges
#                           complete.
#
# The aggregate score is the synthesis judge's overall (it has the full
# picture). Vision-pair mean is exposed on TournamentResult as a sanity
# check, not the canonical aggregate.


VISION_JUDGE_LABELS = {
    "openai": GPT_JUDGE_MODEL,
    "gemini": GEMINI_JUDGE_MODEL,
}

SYNTHESIS_JUDGE_KEY = "anthropic"
SYNTHESIS_JUDGE_LABEL = OPUS_SYNTHESIS_MODEL


def _exception_repr(exc: BaseException) -> str:
    """Render an exception with both type and message.

    `concurrent.futures.TimeoutError` and a few other exception classes
    have empty `__str__` representations; naive `str(exc)` renders as
    blank, silently obscuring the failure mode.
    """
    msg = str(exc) or repr(exc)
    return f"{type(exc).__name__}: {msg}" if msg != repr(exc) else repr(exc)


def _zero_judgment(judge_label: str, reason: str) -> JudgmentScore:
    """Build a zero-score `available=False` JudgmentScore with a reason.

    Used for both missing-client placeholders (so the synthesis prompt
    has something to render in both vision slots) and infrastructure
    failures (timeout, API error). The `available` flag is the canonical
    filtering signal; `reason` is surfaced in `issues` so the synthesis
    judge can discount the slot and explain why.
    """
    return JudgmentScore(
        judge=judge_label,
        garment_type=0,
        color_accuracy=0,
        text_accuracy=0,
        logo_accuracy=0,
        construction_accuracy=0,
        no_hallucinations=0,
        overall=0,
        issues=[reason],
        suggested_fixes=[],
        raw_response="",
        available=False,
    )


def run_tournament(
    clients: dict,
    source_path: Path,
    candidate_path: Path,
    dna: dict,
    passing_threshold: float = 98.0,
    vision_timeout: float = 600.0,
) -> TournamentResult:
    """Run 3-judge tournament: 2 vision judges in parallel, then Opus synthesis.

    Flow:
    1. GPT-5.5-pro + Gemini-3.1-pro-preview run concurrently against both images.
    2. Their JudgmentScore results are passed to Opus 4.7 as text.
    3. Opus produces the canonical overall + reasoned rationale.

    Coverage rules:
    - Zero vision judges → ValueError. Synthesis without vision is meaningless.
    - One vision judge → warn loudly. Opus still runs but gets a flagged
      placeholder in the missing slot.
    - No synthesis client → warn; aggregate falls back to vision-pair mean.

    `vision_timeout` defaults to 600s (10 min). Reasoning-mode vision
    models with `effort=high` and dynamic thinking are highly
    stochastic — typical runs are 90–180s but tail latency on hard
    image-comparison tasks can exceed 5 minutes. The Layer 1 validation
    on 2026-05-04 hit 300s on GPT-5.5-pro post-refine, surfacing as an
    empty `concurrent.futures.TimeoutError`. 10 min is the empirical
    p99 ceiling we've observed; below this is real timeout territory
    (model genuinely stuck or API issue) where we'd rather fail fast
    than wait indefinitely.
    """
    vision_missing = [name for name in VISION_JUDGE_LABELS if not clients.get(name)]
    vision_available = [name for name in VISION_JUDGE_LABELS if clients.get(name)]
    synthesis_available = bool(clients.get(SYNTHESIS_JUDGE_KEY))

    if not vision_available:
        raise ValueError(
            "Cannot run tournament: no vision-judge clients configured. "
            "Set OPENAI_API_KEY and GOOGLE_API_KEY (or GEMINI_API_KEY) and "
            "rebuild the clients dict. The synthesis judge cannot reason "
            "over zero vision reports."
        )
    if vision_missing:
        log.warning(
            "Vision pair running with %d/%d judges. Missing: %s. "
            "Synthesis judge will be told this slot is unavailable.",
            len(vision_available),
            len(VISION_JUDGE_LABELS),
            ", ".join(f"{name} ({VISION_JUDGE_LABELS[name]})" for name in vision_missing),
        )
    if not synthesis_available:
        log.warning(
            "Synthesis judge (%s) unavailable — aggregate will fall back to "
            "vision-pair mean. Set ANTHROPIC_API_KEY for full 3-judge mode.",
            SYNTHESIS_JUDGE_LABEL,
        )

    # Stage 1: vision pair, in parallel
    vision_judges: dict[str, JudgmentScore] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = {}
        if clients.get("openai"):
            futures["openai"] = pool.submit(
                judge_with_gpt, clients["openai"], source_path, candidate_path, dna
            )
        if clients.get("gemini"):
            futures["gemini"] = pool.submit(
                judge_with_gemini, clients["gemini"], source_path, candidate_path, dna
            )
        for name, fut in futures.items():
            try:
                vision_judges[name] = fut.result(timeout=vision_timeout)
            except Exception as exc:
                log.error("Vision judge %s failed: %s", name, _exception_repr(exc))
                vision_judges[name] = _zero_judgment(
                    VISION_JUDGE_LABELS[name],
                    f"vision judge infrastructure failure: {_exception_repr(exc)}",
                )

    def _missing_vision_placeholder(provider: str) -> JudgmentScore:
        return _zero_judgment(
            VISION_JUDGE_LABELS[provider],
            f"{provider} client not configured — no vision report from this judge",
        )

    gpt_judgment = vision_judges.get("openai", _missing_vision_placeholder("openai"))
    gemini_judgment = vision_judges.get("gemini", _missing_vision_placeholder("gemini"))

    judges: list[JudgmentScore] = [
        j for j in (vision_judges.get("openai"), vision_judges.get("gemini")) if j is not None
    ]

    # Stage 2: synthesis
    synthesis_judgment: JudgmentScore | None = None
    if synthesis_available:
        synthesis_judgment = judge_with_opus_synthesis(
            clients[SYNTHESIS_JUDGE_KEY], gpt_judgment, gemini_judgment, dna
        )
        judges.append(synthesis_judgment)

    # Aggregate: synthesis overall is canonical. Without synthesis, fall
    # back to vision-pair mean of the available judges only — a missing
    # or failed slot would otherwise drag the mean to 0.
    vision_pair_overalls = [
        j.overall
        for j in (vision_judges.get("openai"), vision_judges.get("gemini"))
        if j is not None and j.available
    ]
    vision_pair_mean = (
        sum(vision_pair_overalls) / len(vision_pair_overalls) if vision_pair_overalls else 0.0
    )
    aggregate = float(synthesis_judgment.overall) if synthesis_judgment else vision_pair_mean

    # Collect issues + fixes from all participating judges
    all_fixes: list[str] = []
    for j in judges:
        all_fixes.extend(j.suggested_fixes)
    seen_fixes: set[str] = set()
    unique_fixes: list[str] = []
    for f in all_fixes:
        norm = f.lower().strip()
        if norm and norm not in seen_fixes:
            seen_fixes.add(norm)
            unique_fixes.append(f)

    # Top issues: synthesis judge's issues first (they're already
    # consensus-filtered), then any high-severity issues from the vision
    # pair that the synthesis didn't surface.
    critical_issues: list[str] = []
    if synthesis_judgment:
        critical_issues.extend(synthesis_judgment.issues)
    for j in (gpt_judgment, gemini_judgment):
        if not j.available:
            continue
        lowest_cat = min(
            ("color_accuracy", j.color_accuracy),
            ("text_accuracy", j.text_accuracy),
            ("logo_accuracy", j.logo_accuracy),
            ("garment_type", j.garment_type),
            ("construction_accuracy", j.construction_accuracy),
            ("no_hallucinations", j.no_hallucinations),
            key=lambda x: x[1],
        )
        if lowest_cat[1] < 80 and j.issues:
            critical_issues.extend(j.issues[:2])

    return TournamentResult(
        candidate_path=str(candidate_path),
        judges=judges,
        aggregate_score=aggregate,
        passed_98=aggregate >= passing_threshold,
        top_issues=list(dict.fromkeys(critical_issues))[:5],
        all_fixes=unique_fixes[:10],
        vision_pair_mean=vision_pair_mean,
        synthesis_overall=float(synthesis_judgment.overall) if synthesis_judgment else None,
    )


def pick_winner(results: list[TournamentResult]) -> TournamentResult | None:
    """Pick the winning candidate from tournament results."""
    if not results:
        return None
    return max(results, key=lambda r: r.aggregate_score)

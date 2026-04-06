"""Tournament judging — score candidates using 3 vision models as judges.

Complements quantitative metrics.py with semantic scoring: garment type match,
logo placement, hallucination detection via GPT-4o + Claude Opus 4.6 + Gemini 3 Pro.
"""

from __future__ import annotations

import base64
import concurrent.futures
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

# Judge models (same as DNA extractors for consistency)
GPT_JUDGE_MODEL = "gpt-4o"
CLAUDE_JUDGE_MODEL = "claude-opus-4-6"
GEMINI_JUDGE_MODEL = "gemini-3-pro-preview"


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


@dataclass
class JudgmentScore:
    """A single judge's scoring of a candidate."""
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

    def to_dict(self) -> dict:
        return {
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


@dataclass
class TournamentResult:
    """Aggregate result from 3-judge tournament."""
    candidate_path: str
    judges: list[JudgmentScore]
    aggregate_score: float  # 0-100
    passed_98: bool
    top_issues: list[str] = field(default_factory=list)
    all_fixes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "candidate_path": self.candidate_path,
            "aggregate_score": self.aggregate_score,
            "passed_98": self.passed_98,
            "top_issues": self.top_issues,
            "all_fixes": self.all_fixes,
            "judges": [j.to_dict() for j in self.judges],
        }


# -- Image loading helpers --------------------------------------------------

def _load_image_b64(image_path: Path) -> tuple[str, str]:
    ext = image_path.suffix.lower()
    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/webp" if ext == ".webp" else "image/png"
    return base64.b64encode(image_path.read_bytes()).decode("utf-8"), mime


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return {}


def _dna_to_spec(dna: dict) -> str:
    """Convert DNA dict to human-readable spec for judge prompt."""
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
        lines.append(f"Construction: {', '.join(dna['construction'][:5])}")
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
    )


# -- Judge implementations --------------------------------------------------

def judge_with_gpt(client, source_path: Path, candidate_path: Path, dna: dict) -> JudgmentScore:
    src_b64, src_mime = _load_image_b64(source_path)
    cand_b64, cand_mime = _load_image_b64(candidate_path)
    spec = _dna_to_spec(dna)
    try:
        response = client.chat.completions.create(
            model=GPT_JUDGE_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": JUDGE_PROMPT.format(spec=spec) + "\n\nIMAGE 1 = SOURCE, IMAGE 2 = GENERATED"},
                    {"type": "image_url", "image_url": {"url": f"data:{src_mime};base64,{src_b64}"}},
                    {"type": "image_url", "image_url": {"url": f"data:{cand_mime};base64,{cand_b64}"}},
                ],
            }],
            max_tokens=1000,
        )
        text = response.choices[0].message.content
        data = _parse_json(text)
        return _build_judgment_from_json("gpt-4o", data, text)
    except Exception as exc:
        log.error("GPT judge failed: %s", exc)
        return JudgmentScore("gpt-4o", 0, 0, 0, 0, 0, 0, 0, [f"judge error: {exc}"], [], "")


def judge_with_claude(client, source_path: Path, candidate_path: Path, dna: dict) -> JudgmentScore:
    src_b64, src_mime = _load_image_b64(source_path)
    cand_b64, cand_mime = _load_image_b64(candidate_path)
    spec = _dna_to_spec(dna)
    try:
        response = client.messages.create(
            model=CLAUDE_JUDGE_MODEL,
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "IMAGE 1 = SOURCE reference (ground truth):"},
                    {"type": "image", "source": {"type": "base64", "media_type": src_mime, "data": src_b64}},
                    {"type": "text", "text": "IMAGE 2 = GENERATED (evaluate against spec):"},
                    {"type": "image", "source": {"type": "base64", "media_type": cand_mime, "data": cand_b64}},
                    {"type": "text", "text": JUDGE_PROMPT.format(spec=spec)},
                ],
            }],
        )
        text = response.content[0].text
        data = _parse_json(text)
        return _build_judgment_from_json("claude-opus-4-6", data, text)
    except Exception as exc:
        log.error("Claude judge failed: %s", exc)
        return JudgmentScore("claude-opus-4-6", 0, 0, 0, 0, 0, 0, 0, [f"judge error: {exc}"], [], "")


def judge_with_gemini(client, source_path: Path, candidate_path: Path, dna: dict) -> JudgmentScore:
    from google.genai import types
    src_mime = _load_image_b64(source_path)[1]
    cand_mime = _load_image_b64(candidate_path)[1]
    spec = _dna_to_spec(dna)
    try:
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
                max_output_tokens=1000,
            ),
        )
        # Extract text from parts, skipping thought_signature and other non-text parts
        text_parts = []
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    text_parts.append(part.text)
        raw_text = "\n".join(text_parts) if text_parts else (response.text or "")
        data = _parse_json(raw_text)
        if not data:
            raise ValueError(f"Empty JSON parse from: {raw_text[:200]}")
        return _build_judgment_from_json("gemini-3-pro-preview", data, raw_text)
    except Exception as exc:
        log.error("Gemini judge failed: %s", exc)
        return JudgmentScore("gemini-3-pro-preview", 0, 0, 0, 0, 0, 0, 0, [f"judge error: {exc}"], [], "")


# -- Tournament orchestration -----------------------------------------------

def run_tournament(
    clients: dict,
    source_path: Path,
    candidate_path: Path,
    dna: dict,
    passing_threshold: float = 98.0,
) -> TournamentResult:
    """Run 3-judge tournament on a single candidate."""
    judges = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {}
        if clients.get("openai"):
            futures["gpt"] = pool.submit(judge_with_gpt, clients["openai"], source_path, candidate_path, dna)
        if clients.get("anthropic"):
            futures["claude"] = pool.submit(judge_with_claude, clients["anthropic"], source_path, candidate_path, dna)
        if clients.get("gemini"):
            futures["gemini"] = pool.submit(judge_with_gemini, clients["gemini"], source_path, candidate_path, dna)

        for name, fut in futures.items():
            try:
                judges.append(fut.result(timeout=90))
            except Exception as exc:
                log.error("Judge %s failed: %s", name, exc)

    # Aggregate scores
    if judges:
        aggregate = sum(j.overall for j in judges) / len(judges)
    else:
        aggregate = 0.0

    # Collect top issues (ones mentioned by 2+ judges)
    all_issues = []
    all_fixes = []
    for j in judges:
        all_issues.extend(j.issues)
        all_fixes.extend(j.suggested_fixes)

    # Deduplicate fixes by normalizing case
    seen_fixes = set()
    unique_fixes = []
    for f in all_fixes:
        norm = f.lower().strip()
        if norm and norm not in seen_fixes:
            seen_fixes.add(norm)
            unique_fixes.append(f)

    # Top issues: pick most critical (lowest individual score categories)
    critical_issues = []
    for j in judges:
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
        top_issues=list(dict.fromkeys(critical_issues))[:5],  # dedup preserving order
        all_fixes=unique_fixes[:10],
    )


def pick_winner(results: list[TournamentResult]) -> TournamentResult | None:
    """Pick the winning candidate from tournament results."""
    if not results:
        return None
    return max(results, key=lambda r: r.aggregate_score)

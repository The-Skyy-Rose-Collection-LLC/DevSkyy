"""Render Fidelity Evaluator — imagery domain adapter.

Reuses the proven render-QC machinery (scripts/oai_render/qc.py + references.py) and
swaps the OpenAI judge for a Claude VISION judge via forced tool-use with a leading
visual_analysis chain-of-thought field. Subject = PNG bytes; ref = RenderExpectation.
"""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.contracts import Verdict
from evaluation.judge import image_block

# Leading-underscore imports from qc.py are intentional reuse of stable internals
# (this is the only cross-package consumer). Migrate if qc.py grows a public API.
from scripts.oai_render import config as render_config
from scripts.oai_render.qc import (
    _GATE_TAGS,
    RenderExpectation,
    _b64_data_url,
    _judge_instructions,
    _ref_data_url,
    deterministic_checks,
)

_GATES = tuple(_GATE_TAGS.keys())  # canonical 6 gates, in qc.py order

IMAGERY_TOOL: dict = {
    "name": "render_qc_verdict",
    "description": "Report the QC verdict for the candidate render against its references.",
    "input_schema": {
        "type": "object",
        "properties": {
            "visual_analysis": {
                "type": "string",
                "description": "FIRST describe the candidate's garment hue, material, silhouette, "
                "and each logo/graphic panel, comparing to the reference images, BEFORE the gates.",
            },
            "is_single_photograph": {"type": "boolean"},
            "garment_matches_reference": {"type": "boolean"},
            "view_correct": {"type": "boolean"},
            "branding_legible_and_correct": {"type": "boolean"},
            "photorealistic_not_flat": {"type": "boolean"},
            "all_garments_present": {"type": "boolean"},
            "reason": {"type": "string"},
        },
        "required": ["visual_analysis", *(_GATES), "reason"],
        "additionalProperties": False,
    },
}


class ImageryAdapter:
    domain = "imagery"

    def __init__(self, review_state_path: Path | None = None) -> None:
        self._review_state = review_state_path or (
            render_config.OUTPUT_DIR / "_review" / "review-state.json"
        )

    def deterministic_checks(self, subject: bytes, ref: RenderExpectation) -> list[str]:
        # Excluded SKUs skip image QC entirely by policy; the corrupt-bytes case won't
        # reach qc.deterministic_checks so no PIL/numpy import is needed for them.
        if ref.sku in render_config.EXCLUDED_SKUS:
            return ["excluded_sku"]
        return deterministic_checks(subject)

    def build_judge_request(self, subject: bytes, ref: RenderExpectation) -> dict:
        content: list[dict] = [{"type": "text", "text": _judge_instructions(ref)}]
        content.append(image_block(_b64_data_url(subject).split(",", 1)[1], "image/png"))
        for path in ref.reference_paths[:3]:
            url = _ref_data_url(path)
            if url:
                head, b64 = url.split(",", 1)
                mime = head[len("data:") :].split(";", 1)[0]
                content.append(image_block(b64, mime))
        return {"messages": [{"role": "user", "content": content}], "tool": IMAGERY_TOOL}

    def parse_verdict(self, judge_output: dict, det_failures: list[str]) -> Verdict:
        # Fail-closed: a gate that is absent or False counts as a failure. Under forced
        # tool-use (required + additionalProperties:False) all gate keys are present, but
        # this guards a degraded/truncated tool response from yielding a false "pass".
        tags = tuple(tag for gate, tag in _GATE_TAGS.items() if judge_output.get(gate) is not True)
        passed = not tags and not det_failures
        gate_results = {g: judge_output.get(g) is True for g in _GATES}
        score = sum(1 for g in _GATES if judge_output.get(g) is True) / len(_GATES)
        return Verdict(
            domain="imagery",
            passed=passed,
            score=score,
            gate_results=gate_results,
            failure_tags=tuple(det_failures) + tags,
            reason=str(judge_output.get("reason", ""))[:300],
            detail={"visual_analysis": judge_output.get("visual_analysis", "")},
        )

    async def revise(self, ref, critique):  # pipeline owns re-render; not used in score() path
        raise NotImplementedError("imagery re-render is owned by scripts/oai_render pipeline")

    def load_ground_truth(self) -> list[dict]:
        if not self._review_state.exists():
            return []
        state = json.loads(self._review_state.read_text(encoding="utf-8"))
        out = []
        for subject_id, entry in state.items():
            label_pass = bool(entry.get("approved")) and not bool(entry.get("flagged"))
            out.append(
                {
                    "subject_id": subject_id,
                    "label_pass": label_pass,
                    "comment": entry.get("comment", ""),
                }
            )
        return out

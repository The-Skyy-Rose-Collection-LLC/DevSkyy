"""Reviewer agent — Claude judges a PR diff and returns APPROVE / REQUEST_CHANGES / DEFER_HUMAN."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("pr_automator.reviewer")

REVIEWER_SYSTEM_PROMPT = """\
You are a senior staff engineer reviewing a pull request on the DevSkyy codebase
(luxury-fashion AI-driven e-commerce platform — Python/FastAPI + Next.js + WordPress/WooCommerce).

You are the SECOND agent in a two-agent pipeline. Another agent already attempted
auto-fixes for lint/format. You read the FINAL diff blind to that work and give
ONE of three verdicts:

  APPROVE          — code is shippable. Scope coherent, no breaking risk you
                     can identify, conventions followed, gates green.
  REQUEST_CHANGES  — concrete issues a fixer should address before merge.
  DEFER_HUMAN      — you are not confident enough to approve. Use this when:
                       * scope is unclear or too broad for one PR
                       * touches a domain you can't fully reason about
                       * requires architectural / product judgment
                       * spec ambiguity makes "correct" ambiguous

DEFAULT TO DEFER_HUMAN WHEN UNSURE. Over-approval is the failure mode.

Project conventions (relevant to your verdict):
- Production-grade only: NO `TODO`, `FIXME`, `pass`, `raise NotImplementedError`,
  placeholder values, or "this would integrate with..." stubs.
- Files <800 lines, functions <50 lines.
- Immutability: `{...obj, key: v}` not `obj.key = v`.
- No hardcoded secrets — environment variables only.
- Generic errors to clients, detailed logs server-side only.
- Validate at system boundaries (Pydantic / Zod).
- Anti-Hallucination: the PR must not introduce code that references files,
  functions, or APIs that don't exist in this repo.

Output STRICT JSON matching this schema (no markdown fences, no prose around it):

{
  "verdict": "APPROVE" | "REQUEST_CHANGES" | "DEFER_HUMAN",
  "confidence": 0-100,
  "scope_assessment": "one paragraph - does this PR do one coherent thing?",
  "risk_assessment": "none | low | medium | high - what breaks if wrong",
  "findings": [
    {
      "severity": "blocker" | "major" | "minor" | "nit",
      "file": "path/to/file",
      "line": 42,
      "issue": "what's wrong",
      "suggested_fix": "concrete fix or 'human judgment needed'"
    }
  ],
  "defer_reasons": ["only when verdict=DEFER_HUMAN - why"],
  "human_attention_paths": ["files a human should look at specifically"]
}
"""


@dataclass
class Finding:
    severity: str
    file: str
    line: int | None
    issue: str
    suggested_fix: str


@dataclass
class ReviewVerdict:
    verdict: str  # APPROVE | REQUEST_CHANGES | DEFER_HUMAN
    confidence: int
    scope_assessment: str
    risk_assessment: str
    findings: list[Finding] = field(default_factory=list)
    defer_reasons: list[str] = field(default_factory=list)
    human_attention_paths: list[str] = field(default_factory=list)
    raw_json: str = ""

    @property
    def is_approve(self) -> bool:
        return self.verdict == "APPROVE"

    @property
    def is_defer(self) -> bool:
        return self.verdict == "DEFER_HUMAN"

    def to_yaml_body(self) -> str:
        """Render verdict as a GitHub review body (markdown + fenced YAML)."""
        lines = [
            f"## PR Automator Review — `{self.verdict}` (confidence {self.confidence}/100)",
            "",
            f"**Scope:** {self.scope_assessment}",
            "",
            f"**Risk:** {self.risk_assessment}",
            "",
        ]
        if self.findings:
            lines.append("**Findings:**")
            lines.append("")
            for f in self.findings:
                loc = f"`{f.file}:{f.line}`" if f.line else f"`{f.file}`"
                lines.append(
                    f"- **[{f.severity}]** {loc} — {f.issue}"
                    + (f"\n  - Fix: {f.suggested_fix}" if f.suggested_fix else "")
                )
            lines.append("")
        if self.defer_reasons:
            lines.append("**Why human review needed:**")
            for r in self.defer_reasons:
                lines.append(f"- {r}")
            lines.append("")
        if self.human_attention_paths:
            lines.append("**Files needing human eyes:**")
            for p in self.human_attention_paths:
                lines.append(f"- `{p}`")
            lines.append("")
        lines.append("---")
        lines.append(
            "_Posted by `pr_automator` reviewer agent. Configured via "
            "`scripts/pr_automator/RISK_PATHS.txt` and the 10-check merge "
            "predicate in `merge_gate.py`._"
        )
        return "\n".join(lines)


class ReviewerAgent:
    """Spawns `claude --print` (headless) with the reviewer system prompt.

    Using the CLI rather than the Python SDK keeps the automator deployable
    without an `ANTHROPIC_API_KEY` in the environment — `claude` already has
    the user's auth.
    """

    def __init__(self, claude_bin: str = "claude", model: str = "claude-sonnet-4-6"):
        self.claude_bin = claude_bin
        self.model = model

    def review(
        self, pr_number: int, diff_text: str, *, max_diff_chars: int = 60_000
    ) -> ReviewVerdict:
        truncated = diff_text[:max_diff_chars]
        truncated_note = ""
        if len(diff_text) > max_diff_chars:
            truncated_note = (
                f"\n\n[NOTE: diff truncated from {len(diff_text)} to {max_diff_chars} chars. "
                "If the diff is too large to safely review, return DEFER_HUMAN with a defer_reason.]"
            )

        user_prompt = (
            f"Review PR #{pr_number}.\n\nDIFF:\n```diff\n{truncated}\n```{truncated_note}\n\n"
            "Return STRICT JSON per the schema. No markdown fences."
        )

        cmd = [
            self.claude_bin,
            "--print",
            "--model",
            self.model,
            "--append-system-prompt",
            REVIEWER_SYSTEM_PROMPT,
        ]
        env = os.environ.copy()
        proc = subprocess.run(
            cmd,
            input=user_prompt,
            check=False,
            capture_output=True,
            text=True,
            env=env,
            timeout=600,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"reviewer claude exited {proc.returncode}: {proc.stderr[:500]}")

        raw = proc.stdout.strip()
        return self._parse(raw)

    @staticmethod
    def _parse(raw: str) -> ReviewVerdict:
        # Tolerate stray prose by extracting the first JSON object.
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"reviewer returned no JSON object: {raw[:300]}")
        payload = raw[start : end + 1]
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as e:
            raise ValueError(f"reviewer JSON parse error: {e}\n---\n{payload[:500]}") from e

        verdict = data.get("verdict", "DEFER_HUMAN")
        if verdict not in {"APPROVE", "REQUEST_CHANGES", "DEFER_HUMAN"}:
            verdict = "DEFER_HUMAN"

        findings_raw = data.get("findings") or []
        findings = [
            Finding(
                severity=str(f.get("severity", "minor")),
                file=str(f.get("file", "")),
                line=f.get("line") if isinstance(f.get("line"), int) else None,
                issue=str(f.get("issue", "")),
                suggested_fix=str(f.get("suggested_fix", "")),
            )
            for f in findings_raw
        ]

        return ReviewVerdict(
            verdict=verdict,
            confidence=int(data.get("confidence", 0) or 0),
            scope_assessment=str(data.get("scope_assessment", "")),
            risk_assessment=str(data.get("risk_assessment", "")),
            findings=findings,
            defer_reasons=[str(r) for r in (data.get("defer_reasons") or [])],
            human_attention_paths=[str(p) for p in (data.get("human_attention_paths") or [])],
            raw_json=payload,
        )


def fetch_diff(worktree: Path, pr_number: int, gh_bin: str = "gh") -> str:
    """Pull the full PR diff via gh — runs in the worktree so --repo is implicit."""
    proc = subprocess.run(
        [gh_bin, "pr", "diff", str(pr_number)],
        cwd=worktree,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh pr diff failed: {proc.stderr[:400]}")
    return proc.stdout

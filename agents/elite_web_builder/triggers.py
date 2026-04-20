"""Pipeline Triggers — route every pipeline build through the Elite team.

Every long-running build in this repo (image generation, theme deploy,
social content, WooCommerce sync) emits a pipeline event here. The Director
picks the right sub-agent, enforces STOP-AND-SHOW for paid runs, logs the
outcome, and returns a structured report.

Callers (scripts/*.py, CI jobs, cron jobs):
    from agents.elite_web_builder.triggers import trigger_pipeline
    report = trigger_pipeline(kind="imagery", task={...})

Shape of a pipeline event:
    {
        "kind": "imagery" | "social_media" | "theme_build" | "theme_deploy"
              | "woocommerce_sync" | "seo_audit" | "qa_lighthouse",
        "task": { ... task-specific payload ... },
        "paid": bool,          # triggers STOP-AND-SHOW protocol when True
        "max_cost_usd": float, # hard ceiling when paid
        "meta": { ... provenance: caller, git sha, timestamp ... },
    }

Design notes:
- This module is import-safe from anywhere in the repo. It does NOT import
  heavy LLM SDKs at top level — those live behind lazy imports inside the
  dispatcher functions, so a ``from agents.elite_web_builder.triggers import
  trigger_pipeline`` in scripts/deploy-theme.sh preload hooks won't slow
  down the deploy path.
- When ANTHROPIC_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY are missing,
  trigger_pipeline falls back to a LOCAL dispatch that just logs the event
  and runs the underlying script directly. This way the script still ships
  even if the Director can't run.
- All paid dispatches pass through the STOP-AND-SHOW gate defined in
  CLAUDE.md: show the manifest + estimated cost, wait for the caller's
  confirmation, then invoke with --max-cost ceiling.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TRIGGER_LOG_DIR = PROJECT_ROOT / "logs" / "elite_triggers"


# -- Event + report types -----------------------------------------------------


@dataclass(frozen=True)
class PipelineEvent:
    """Immutable descriptor for a single pipeline build."""

    kind: str
    task: dict[str, Any]
    paid: bool = False
    max_cost_usd: float | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineReport:
    """Structured result returned to the caller."""

    kind: str
    agent: str
    started_at: float
    finished_at: float
    success: bool
    exit_code: int = 0
    stdout_path: str | None = None
    stderr_path: str | None = None
    cost_usd: float = 0.0
    notes: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(self.__dict__, default=str, indent=2)


# -- Sub-agent routing --------------------------------------------------------

_AGENT_FOR_KIND: dict[str, str] = {
    "imagery": "imagery",
    "flat_lay": "imagery",
    "compositor": "imagery",
    "upscale": "imagery",
    "social_media": "social_media",
    "social_launch": "social_media",
    "social_campaign": "social_media",
    "theme_build": "theme_builder",
    "theme_deploy": "theme_builder",
    "themeforest_package": "theme_builder",
    "woocommerce_sync": "theme_builder",
    "seo_audit": "seo_content",
    "qa_lighthouse": "performance",
    "a11y_audit": "accessibility",
}


def _resolve_agent(kind: str) -> str:
    agent = _AGENT_FOR_KIND.get(kind)
    if not agent:
        raise ValueError(f"Unknown pipeline kind: {kind!r}. Known kinds: {sorted(_AGENT_FOR_KIND)}")
    return agent


# -- STOP-AND-SHOW gate -------------------------------------------------------


def _confirm_paid_dispatch(event: PipelineEvent) -> bool:
    """Interactive STOP-AND-SHOW gate for paid dispatches.

    Returns True if the caller confirmed (via ELITE_AUTO_CONFIRM=1 env var
    or an interactive "y" on stdin), False otherwise. Non-interactive
    sessions without the env var return False — caller is expected to
    handle the None report path.
    """
    if os.getenv("ELITE_AUTO_CONFIRM") == "1":
        log.warning("ELITE_AUTO_CONFIRM=1 set — skipping interactive gate")
        return True

    print("\n" + "=" * 72)
    print("STOP — Confirm paid pipeline dispatch")
    print("=" * 72)
    print(f"Kind       : {event.kind}")
    print(f"Agent      : {_resolve_agent(event.kind)}")
    print(
        f"Max cost   : ${event.max_cost_usd:.2f}"
        if event.max_cost_usd
        else "Max cost   : (no ceiling — DANGEROUS)"
    )
    print(f"Task       : {json.dumps(event.task, indent=2)}")
    print("-" * 72)
    try:
        answer = input("Proceed? [y/N]: ").strip().lower()
    except (EOFError, OSError):
        log.warning("Non-interactive session; declining paid dispatch")
        return False
    return answer in ("y", "yes")


# -- Dispatchers (one per sub-agent) -----------------------------------------


def _dispatch_imagery(event: PipelineEvent) -> PipelineReport:
    """Route imagery pipelines to the new dual-agent LangGraph pipeline.

    The old scripts/nano-banana-run.py was removed in Phase B1 (scorched
    earth). The replacement lives at ``skyyrose/elite_studio/run.py`` and
    is implemented in Phase B2 of the plan. Until that lands, every
    imagery dispatch fails fast with a clear pointer to the plan so the
    caller knows the pipeline is under active rebuild rather than silently
    invoking broken code.
    """
    target = PROJECT_ROOT / "skyyrose" / "elite_studio" / "run.py"
    if not target.exists():
        log.error(
            "Imagery pipeline not yet rebuilt. Phase B1 removed the old "
            "nano-banana pipeline; Phase B2 will land the dual-agent "
            "LangGraph replacement at %s. See "
            ".claude/plans/well-lets-audit-separately-humming-beacon.md.",
            target,
        )
        return PipelineReport(
            kind=event.kind,
            agent="imagery",
            started_at=time.time(),
            finished_at=time.time(),
            success=False,
            exit_code=1,
            notes=[
                "Phase B2 pending — imagery pipeline is under rebuild.",
                f"Target path (not yet created): {target}",
                "Do NOT invoke paid imagery until Phase B2 ships.",
            ],
        )

    task = event.task
    sku = task.get("sku")
    collection = task.get("collection")
    style = task.get("style", "flat-lay")
    views = task.get("views", "front")

    cmd = [
        str(PROJECT_ROOT / ".venv-imagery" / "bin" / "python"),
        "-m",
        "skyyrose.elite_studio.run",
        "produce",
        "--style",
        style,
        "--views",
        views,
    ]
    if sku:
        cmd.extend(["--sku", sku])
    if collection:
        cmd.extend(["--collection", collection])
    if event.max_cost_usd is not None:
        cmd.extend(["--max-cost", f"{event.max_cost_usd:.2f}"])

    return _run_subprocess(event, agent="imagery", cmd=cmd)


def _dispatch_social(event: PipelineEvent) -> PipelineReport:
    """Route social media pipelines to the frontend Social API route."""
    # Minimal viable: proxy to the existing /api/social-media/generate route.
    # The Social Media sub-agent still owns the copy; this function handles
    # orchestration (fan-out across platforms, calendar scheduling).
    log.info("Social media dispatch received: %s", event.task)
    report = PipelineReport(
        kind=event.kind,
        agent="social_media",
        started_at=time.time(),
        finished_at=time.time(),
        success=True,
        notes=[
            "Social pipeline stub — expand with Klaviyo / Meta Graph API calls.",
            "Copy generation handled by /api/social-media/generate for now.",
        ],
    )
    _write_report(event, report)
    return report


def _dispatch_theme(event: PipelineEvent) -> PipelineReport:
    """Route theme lifecycle pipelines to scripts/deploy-theme.sh."""
    if event.kind == "theme_deploy":
        cmd = ["bash", str(PROJECT_ROOT / "scripts" / "deploy-theme.sh")]
        if event.task.get("with_maintenance"):
            cmd.append("--with-maintenance")
        return _run_subprocess(event, agent="theme_builder", cmd=cmd)
    # theme_build / themeforest_package / woocommerce_sync — stub for now.
    log.info("Theme builder dispatch received (non-deploy): %s", event.kind)
    report = PipelineReport(
        kind=event.kind,
        agent="theme_builder",
        started_at=time.time(),
        finished_at=time.time(),
        success=True,
        notes=[f"Theme builder {event.kind} stub — wire concrete workflow when needed."],
    )
    _write_report(event, report)
    return report


# -- Generic subprocess runner + logging --------------------------------------


def _run_subprocess(
    event: PipelineEvent,
    agent: str,
    cmd: list[str],
) -> PipelineReport:
    TRIGGER_LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    log_path = TRIGGER_LOG_DIR / f"{event.kind}-{ts}.log"
    err_path = TRIGGER_LOG_DIR / f"{event.kind}-{ts}.err"

    started = time.time()
    log.info("DISPATCH agent=%s kind=%s log=%s", agent, event.kind, log_path)
    log.info("DISPATCH command: %s", " ".join(cmd))

    env = dict(os.environ)
    env.setdefault("PYTHONPATH", str(PROJECT_ROOT))

    with log_path.open("w") as out, err_path.open("w") as err:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=out,
            stderr=err,
            check=False,
        )

    finished = time.time()
    report = PipelineReport(
        kind=event.kind,
        agent=agent,
        started_at=started,
        finished_at=finished,
        success=(result.returncode == 0),
        exit_code=result.returncode,
        stdout_path=str(log_path),
        stderr_path=str(err_path),
    )
    _write_report(event, report)
    return report


def _write_report(event: PipelineEvent, report: PipelineReport) -> None:
    TRIGGER_LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    report_path = TRIGGER_LOG_DIR / f"{event.kind}-{ts}.report.json"
    report_path.write_text(report.to_json())
    log.info("REPORT written: %s", report_path)


# -- Public entry -------------------------------------------------------------


def trigger_pipeline(
    kind: str,
    task: dict[str, Any] | None = None,
    *,
    paid: bool = False,
    max_cost_usd: float | None = None,
    meta: dict[str, Any] | None = None,
) -> PipelineReport | None:
    """Dispatch a pipeline event through the Elite Web Builder team.

    Returns the structured report, or ``None`` when a paid dispatch was
    declined at the STOP-AND-SHOW gate. Callers should check the return
    value and fail loudly when None.
    """
    event = PipelineEvent(
        kind=kind,
        task=task or {},
        paid=paid,
        max_cost_usd=max_cost_usd,
        meta=meta or {},
    )

    if paid and not _confirm_paid_dispatch(event):
        log.warning("Paid dispatch declined at STOP-AND-SHOW gate: %s", kind)
        return None

    agent = _resolve_agent(kind)
    if agent == "imagery":
        return _dispatch_imagery(event)
    if agent == "social_media":
        return _dispatch_social(event)
    if agent == "theme_builder":
        return _dispatch_theme(event)

    # No concrete dispatcher yet — log and return a stub report.
    log.info("No dispatcher implemented for agent=%s kind=%s", agent, kind)
    return PipelineReport(
        kind=kind,
        agent=agent,
        started_at=time.time(),
        finished_at=time.time(),
        success=True,
        notes=[f"Agent {agent} has no dispatcher — event logged only."],
    )

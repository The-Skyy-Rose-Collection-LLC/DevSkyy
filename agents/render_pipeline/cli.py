"""External CLI driver for the RenderPipeline ADK agent.

This script is the production entry point. It implements the STOP-AND-SHOW
gate (CLAUDE.md mandate) externally so the agent itself stays purely
autonomous — clean ADK contract for programmatic callers (CI, dashboard,
cron) which can skip the gate entirely by setting STOP_CONFIRM=y or
calling root_agent directly via the Runner.

Pipeline:
  1. Parse args (--sku, --view, --max-usd)
  2. Preflight (free tools only): load_dossier + resolve_source +
     route_engine. Builds the cost-and-source manifest.
  3. STOP-AND-SHOW: print manifest + wait for explicit 'y' on stdin.
     Skipped when STOP_CONFIRM=y is set in the environment.
  4. Run the SequentialAgent via Runner.run_async() → emit RenderResult
  5. Pretty-print the result.

Usage:
    python -m agents.render_pipeline.cli --sku br-001 --view front
    STOP_CONFIRM=y python -m agents.render_pipeline.cli --sku br-001
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

# Same sys.path setup pattern as agent.py / tools/_paths.py
REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (REPO_ROOT, REPO_ROOT / "scripts"):
    _ps = str(_p)
    if _ps not in sys.path:
        sys.path.insert(0, _ps)

log = logging.getLogger("render_pipeline.cli")


def _load_env_files() -> list[str]:
    """Source .env files into os.environ. Returns missing required keys.

    Mirrors the pattern from `_validate_pipeline_multi_sku._load_env_files`.
    Required keys: OPENAI_API_KEY (vision + judge + image), ANTHROPIC_API_KEY
    (Sonnet L0 + Opus synthesis + Opus judge), GOOGLE_API_KEY (Gemini stack),
    FAL_KEY (FLUX + Kontext refinement).
    """
    for envf in (
        ".env.judge-gpt-vision",
        ".env.judge-gemini-vision",
        ".env.judge-opus-thinking",
        ".env.hf",
        ".env.secrets",
    ):
        path = REPO_ROOT / envf
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    needed = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "FAL_KEY"]
    return [k for k in needed if not os.environ.get(k)]


def _make_state_shim() -> SimpleNamespace:
    """Build a state-only ToolContext stand-in for preflight.

    Preflight calls the free tool functions DIRECTLY (no ADK Runner involved)
    to gather the cost+source manifest without paid API calls. The tools
    expect `tool_context.state` (dict-like) — we provide a SimpleNamespace
    wrapping a dict, which mirrors the real ToolContext shape.
    """
    return SimpleNamespace(state={})


def _preflight(sku: str, view: str) -> dict:
    """Run the 4 FREE tools synchronously to build the manifest.

    Tools called: load_dossier_fn, resolve_source_fn, route_engine_fn, build_prompt_fn.
    These are all file/CSV reads — no paid API calls. vision_consensus_fn
    and articulate_layer0_fn are NOT called here (those incur cost) — the
    agent will call them at runtime after the user confirms.
    """
    from agents.render_pipeline.tools.build_prompt import build_prompt_fn
    from agents.render_pipeline.tools.load_dossier import load_dossier_fn
    from agents.render_pipeline.tools.resolve_source import resolve_source_fn
    from agents.render_pipeline.tools.route_engine import route_engine_fn

    ctx = _make_state_shim()
    ctx.state["view"] = view  # build_prompt_fn reads view from state for some paths

    dossier_info = load_dossier_fn(sku, ctx)
    source_info = resolve_source_fn(sku, ctx)
    if source_info.get("error"):
        raise SystemExit(f"PREFLIGHT FAILED: {source_info['error']}")

    route_info = route_engine_fn(sku, view, ctx)
    if route_info.get("error"):
        raise SystemExit(f"PREFLIGHT FAILED: {route_info['error']}")

    # Build prompt is free (no API calls — composition only); skip Sonnet's L0
    # since articulate_layer0 isn't run in preflight. build_prompt falls back
    # to registry's canonical_mode_v1 when state['layer0_directives'] missing.
    prompt_info = build_prompt_fn(sku, view, ctx)

    return {
        "sku": sku,
        "view": view,
        "name": dossier_info.get("name", ""),
        "collection": dossier_info.get("collection", ""),
        "dossier_spec_chars": dossier_info.get("spec_chars", 0),
        "engine_override_pinned": dossier_info.get("engine_override"),
        "source_path": source_info.get("source_path"),
        "source_filename": source_info.get("filename"),
        "source_size_kb": source_info.get("size_kb"),
        "engine": route_info.get("engine"),
        "model_id": route_info.get("model_id"),
        "engine_reason": route_info.get("reason"),
        "estimated_cost_usd": route_info.get("estimated_cost_usd", 0.0),
        "override_applied": route_info.get("override_applied", False),
        "preview_template_id": prompt_info.get("template_id"),
        "preview_layer3_chars": prompt_info.get("layer3_chars"),
        "preview_layer2_chars": prompt_info.get("layer2_chars"),
    }


def _stop_and_show(manifest: dict, max_usd: float) -> bool:
    """Print the cost+source manifest and require explicit 'y' to proceed.

    STOP_CONFIRM=y in environment auto-confirms (CI usage, no human present).
    Estimated total = generation cost (route's estimate) + tournament cost
    (~$0.10 covering 3 judges) + Sonnet L0 cost (~$0.005) + dual vision
    cost (~$0.01 if not cached) + possible refinement (~$0.04).
    """
    gen_cost = manifest["estimated_cost_usd"]
    # Empirically-tuned overhead estimates:
    overhead = 0.10 + 0.005 + 0.01  # tournament + Sonnet L0 + dual vision
    refine_max = 0.04  # one Kontext refinement if needed
    est_total = gen_cost + overhead + refine_max

    print("\n" + "=" * 72)
    print("STOP — Confirm before proceeding (paid API calls):")
    print("=" * 72)
    print("  Action          : RenderPipeline ADK agent — full 9-step pipeline")
    print(f"  SKU             : {manifest['sku']} — {manifest['name']}")
    print(f"  Collection      : {manifest['collection']}")
    print(f"  View            : {manifest['view']}")
    print(
        f"  Source image    : {manifest['source_filename']} ({manifest['source_size_kb']:.0f} KB)"
    )
    print(f"                    {manifest['source_path']}")
    print(f"  Dossier spec    : {manifest['dossier_spec_chars']} chars (canonical)")
    print(f"  Engine          : {manifest['engine']} ({manifest['model_id']})")
    print(f"    Reason        : {manifest['engine_reason']}")
    print(
        f"    Override      : {manifest['override_applied']} "
        f"(catalog-pinned: {manifest['engine_override_pinned']!r})"
    )
    print(f"  Layer 3 chars   : {manifest['preview_layer3_chars']} (verbatim dossier positives)")
    print(f"  Layer 2 chars   : {manifest['preview_layer2_chars']} (verbatim dossier negatives)")
    print(
        f"  Cost estimate   : ~${est_total:.3f}  (gen={gen_cost:.3f}, overhead={overhead:.3f}, "
        f"max_refine={refine_max:.3f})"
    )
    print(f"  Hard cap        : ${max_usd:.2f}")
    print("=" * 72)

    if est_total > max_usd:
        print(f"  ⚠ Estimated cost exceeds --max-usd ${max_usd:.2f}. Aborting.\n")
        return False

    if os.environ.get("STOP_CONFIRM", "").lower() == "y":
        print("[STOP_CONFIRM=y in environment — auto-confirmed]\n")
        return True

    try:
        answer = input("Proceed? [y/N]: ").strip().lower()
    except EOFError:
        return False
    return answer in ("y", "yes")


async def _run_agent(sku: str, view: str) -> dict:
    """Invoke root_agent via the ADK Runner. Returns the final RenderResult dict."""
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types as genai_types

    from agents.render_pipeline.agent import root_agent

    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="render_pipeline",
        session_service=session_service,
    )

    user_id = "cli"
    session_id = f"render-{sku}-{view}-{int(time.time())}"
    await session_service.create_session(
        app_name="render_pipeline", user_id=user_id, session_id=session_id
    )

    user_input = json.dumps({"sku": sku, "view": view})
    new_message = genai_types.Content(role="user", parts=[genai_types.Part(text=user_input)])

    final_event = None
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=new_message
    ):
        if event.is_final_response():
            final_event = event

    # The synthesis_agent's RenderResult lands in state['render_result']
    session = await session_service.get_session(
        app_name="render_pipeline", user_id=user_id, session_id=session_id
    )
    render_result = session.state.get("render_result") if session else None

    return {
        "render_result": render_result,
        "session_state": dict(session.state) if session else {},
        "final_event_text": (
            final_event.content.parts[0].text
            if (final_event and final_event.content and final_event.content.parts)
            else None
        ),
    }


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--sku", required=True, help="Catalog SKU (e.g. br-001)")
    parser.add_argument("--view", default="front", choices=["front", "back", "branding"])
    parser.add_argument(
        "--max-usd",
        type=float,
        default=float(os.environ.get("MAX_USD", "0.50")),
        help="Hard cost cap. Aborts if estimated total exceeds this.",
    )
    args = parser.parse_args(argv)

    missing = _load_env_files()
    if missing:
        print(f"ERROR: missing required env keys: {missing}", file=sys.stderr)
        return 1

    log.info("Running preflight (free tools only)...")
    try:
        manifest = _preflight(args.sku, args.view)
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"PREFLIGHT FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    if not _stop_and_show(manifest, args.max_usd):
        print("Aborted.", file=sys.stderr)
        return 4

    log.info("Invoking RenderPipeline agent — paid API calls in flight...")
    t0 = time.monotonic()
    try:
        outcome = asyncio.run(_run_agent(args.sku, args.view))
    except Exception as exc:
        log.exception("Agent invocation failed")
        print(f"AGENT FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 5
    elapsed = time.monotonic() - t0

    print("\n" + "=" * 72)
    print(f"RESULT — {args.sku} {args.view} in {elapsed:.0f}s")
    print("=" * 72)
    rr = outcome.get("render_result")
    if rr:
        print(json.dumps(rr if isinstance(rr, dict) else rr.model_dump(), indent=2))
    else:
        print("(No structured RenderResult — see session_state below)")
        print(json.dumps(outcome.get("session_state", {}), indent=2, default=str))

    # Persist outcome for audit
    out_dir = REPO_ROOT / "tasks"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"render-pipeline-cli-{args.sku}-{args.view}-{int(time.time())}.json"
    out_path.write_text(json.dumps(outcome, indent=2, default=str))
    log.info("Outcome saved to %s", out_path.relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())

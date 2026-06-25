"""Live integration eval — gated by EVAL_LIVE=1 environment variable.

Cost: ~$0.15-0.25 per run (single br-001 SKU end-to-end). Runs the agent
through Runner against the real APIs:
  - Anthropic (Sonnet L0 + Opus synthesis + Opus judge)
  - OpenAI (GPT-4o vision describe + GPT-5.5-pro judge + optional GPT-image gen)
  - Google (Gemini-3-flash-preview describe + NB Pro image + Gemini-3.1-pro-preview judge)
  - fal.ai (FLUX-pro / Kontext refinement, conditional)

Skipped by default. CI nightly cron sets EVAL_LIVE=1 + STOP_CONFIRM=y so
the agent runs without interactive prompts (the agent itself is non-interactive;
only the CLI driver has the gate).

Mock-based unit tests live in agents/render_pipeline/tests/test_tools.py and
run on every PR — no API keys required.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Same sys.path setup as agent.py
_REPO = Path(__file__).resolve().parents[3]
for _p in (_REPO, _REPO / "scripts"):
    _ps = str(_p)
    if _ps not in sys.path:
        sys.path.insert(0, _ps)


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.environ.get("EVAL_LIVE") != "1",
    reason="Live eval gated by EVAL_LIVE=1 (incurs ~$0.20 cost). Run mock tests instead.",
)
async def test_render_pipeline_live_br001() -> None:
    """End-to-end live eval on br-001.

    Asserts the AgentEvaluator's tool trajectory + final-response criteria
    (defined in eval/test_config.json). Trajectory check: tools are called
    in order, with the expected sku/view args. Response match: final
    SynthesisAgent output mentions ship-readiness keywords.

    Run nightly via:
        EVAL_LIVE=1 STOP_CONFIRM=y \\
            pytest agents/render_pipeline/eval/test_render_pipeline.py -v
    """
    from google.adk.evaluation.agent_evaluator import AgentEvaluator

    eval_dir = Path(__file__).parent / "render_pipeline.evalset.json"

    await AgentEvaluator.evaluate(
        agent_module="agents.render_pipeline",
        eval_dataset_file_path_or_dir=str(eval_dir),
        num_runs=1,  # single run — eval is expensive; nightly cadence is enough
    )

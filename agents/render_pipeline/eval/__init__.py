"""ADK AgentEvaluator harness for the RenderPipeline agent.

Two eval modalities (Q4=both per user direction 2026-05-06):
  - tests/test_tools.py — mock-based unit tests (always runs, no paid calls)
  - eval/test_render_pipeline.py — live integration via AgentEvaluator
    (gated by EVAL_LIVE=1 environment variable, ~$0.20/run)
"""

"""Cross-service orchestration pipelines.

Each submodule packages a multi-stage workflow that composes services from
``services/``, ``agents/``, and ``llm/`` into a single end-to-end operation.

Currently shipped:
- :mod:`pipelines.clothing_3d` — image/text → preprocessed → TRELLIS →
  postprocessed GLB/USDZ → stored artifact, with QC gates and event emission.
"""

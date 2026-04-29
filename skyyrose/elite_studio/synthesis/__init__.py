"""FLUX synthesis pipeline — dossier-aware luxury product render.

Replaces the single-pass Gemini Pro Image Preview RAS stage in
``three_d_agent.py`` with a 5-stage diffusion pipeline:

    Stage 1  FLUX Kontext Pro    base garment, no decoration
    Stage 2  Gemini Flash vision derive decoration-zone mask
    Stage 3  FLUX Fill Pro       inpaint decoration in mask only
    Stage 4  IC-Light V2         relight (deferred to v2)
    Stage 5  VisionAuditAgent    audit + retry-with-feedback (existing)

The structural innovation is the binary mask in Stage 3 — it makes
decoration drift physically impossible, not just unlikely.

Architecture: ``docs/architecture/flux-synthesis.md``.
"""

from .flux_pipeline import RenderResult, render

__all__ = ["RenderResult", "render"]

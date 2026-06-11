"""Configuration for the OpenAI gpt-image-2 product render pipeline.

Loads API keys via the project env loader (root .env + gemini/.env with
override=True) and exposes the fixed, deterministic render parameters that
make every product render identical. No Gemini / nano-banana dependencies.
"""

from __future__ import annotations

import os
from pathlib import Path

# Load root .env + gemini/.env (override=True) so OPENAI_API_KEY is present.
# config/ is a repo-root package; fall back to a path walk if it is not yet
# importable (e.g. when the module is imported before sys.path is set up).
try:  # pragma: no cover - import wiring
    from config.load_env import load_project_env

    PROJECT_ROOT = load_project_env()
except Exception:  # pragma: no cover - defensive fallback
    PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ── Model + render parameters (the "identical procedure") ───────────────────
MODEL = "gpt-image-2"  # OpenAI "Image 2"; auto-high-fidelity on every input
QUALITY = "high"  # highest fidelity tier
SIZE = "1024x1536"  # portrait → feeds the 4:5 holo card crop
OUTPUT_FORMAT = "png"  # lossless
BACKGROUND = "auto"  # "transparent" | "opaque" | "auto"
N = 1
MAX_REFERENCE_IMAGES = 16  # gpt-image edit hard limit
# NOTE: input_fidelity is intentionally NOT sent. Context7 (OpenAI API docs):
# for gpt-image-2 the model auto-processes every input at high fidelity and
# the parameter cannot be set.

# ── Networking / resilience ─────────────────────────────────────────────────
REQUEST_TIMEOUT_S = 180.0
MAX_RETRIES = 5
RETRY_BACKOFF_BASE_S = 2.0  # exponential: base * 2**attempt (+ jitter)
RETRY_BACKOFF_MAX_S = 60.0

# ── Cost guardrails ─────────────────────────────────────────────────────────
# Estimate for the STOP-AND-SHOW manifest; real spend is whatever OpenAI bills.
# Verified 2026-06: gpt-image-2 high quality ≈ $0.21 at 1024x1024. Our 1024x1536
# portrait + multi-image edit (reference input tokens) ≈ $0.35–0.40/image. Edit-
# heavy / retried calls can run higher — treat this as a floor, not a ceiling.
EST_COST_PER_IMAGE_USD = 0.40
HARD_COST_CAP_USD = 50.0  # abort any run whose manifest estimate exceeds this

# ── QC gate (post-generation validation, pre-acceptance) ────────────────────
# Layered: free deterministic checks (decode / dimensions / collage panels),
# then a cheap VLM judge. The HARD_COST_CAP_USD above guards the manifest
# ESTIMATE; the SpendTracker in cost.py enforces the same cap against ACTUAL
# accumulated spend (renders + judged retries + judge calls) at runtime, which
# closes the retry-storm gap (worst case previously ~$189 vs the $50 cap).
QC_ENABLED = True
QC_JUDGE_MODEL = "gpt-4o-mini"  # vision judge; detail:"low" = 85 image tokens flat
QC_JUDGE_DETAIL = "low"  # NEVER "auto"/"high" — community-verified token inflation
QC_JUDGE_MAX_OUTPUT_TOKENS = 300
QC_MAX_RENDER_RETRIES = 2  # judged re-renders per plan before quarantine
EST_JUDGE_COST_USD = 0.0002  # generous ceiling per judge call (actual ≈ $0.000075)
EXPECTED_RENDER_SIZE = (1024, 1536)  # must match SIZE above

# ── Batch exclusions ────────────────────────────────────────────────────────
# SKUs auto-skipped from --all / --collection batches (known-bad source asset).
# Explicit --sku/--skus still renders them (founder override). Reason logged.
EXCLUDED_SKUS: dict[str, str] = {
    "sg-015": "only reference is a 4-panel composite techflat — needs a clean cropped front "
    "techflat before it can render as a single garment (would otherwise produce a multi-panel).",
    # sg-006 / sg-014 removed 2026-06-10: dossiers re-authored from the real mint
    # garments (bug-119 contamination cleared) — both SKUs render again.
}

# ── Paths (single authority: skyyrose/core/paths.py) ────────────────────────
from skyyrose.core import paths as _ap  # noqa: E402

THEME_ROOT = _ap.THEME_ROOT
CATALOG_CSV = _ap.CATALOG_CSV
DOSSIER_DIR = _ap.DOSSIERS_DIR
# Founder's verbatim render-review corrections, injected into prompts per SKU
# (generated from the 2026-06-09 review board; see the file's _meta block).
CORRECTIONS_JSON = THEME_ROOT / "data" / "render-corrections.json"
# Founder-approved surviving assets (tasks/mockup-render-inventory.md keep pass):
# each entry skips one (sku, style, view) plan in batches; explicit --sku overrides.
KEEPERS_JSON = THEME_ROOT / "data" / "render-keepers.json"
PRODUCT_REFERENCES_DIR = _ap.PRODUCT_REFERENCES
PRODUCTS_DIR = _ap.WP_PRODUCTS_DIR
SPLIT_DIR = _ap.PRODUCT_TECHFLATS / "split"
OVERLAYS_DIR = _ap.PRODUCT_TECHFLATS / "hero-overlays"
TECHFLATS_DIR = _ap.PRODUCT_TECHFLATS
OUTPUT_DIR = PROJECT_ROOT / "renders" / "oai"
REJECTED_DIR = OUTPUT_DIR / "_rejected"  # QC-failed renders quarantined for human review

API_KEY_ENV = "OPENAI_API_KEY"


def get_api_key() -> str:
    """Return the OpenAI API key from the environment, or raise a clear error.

    The key is loaded from gemini/.env (override=True) by config/load_env.py.
    It is never logged or printed.
    """
    key = os.environ.get(API_KEY_ENV, "").strip()
    if not key:
        raise RuntimeError(
            f"{API_KEY_ENV} not set. Add it to gemini/.env "
            "(loaded with override=True by config/load_env.py) and retry."
        )
    return key


def api_key_present() -> bool:
    """True if an API key is available, without raising (for dry-run / status)."""
    return bool(os.environ.get(API_KEY_ENV, "").strip())

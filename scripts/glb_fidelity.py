#!/usr/bin/env python3
"""
GLB Fidelity Gate — headless screenshot each product GLB and score against hub master.

Serves GLBs via a background HTTP server, renders them with <model-viewer> at a canonical
front angle, screenshots with Playwright, then runs the fidelity gate (color ΔE; CLIP when
open_clip_torch is installed).

NOTE: Color ΔE and CLIP thresholds are uncalibrated heuristics for render-vs-photo
comparison. Treats verdicts as a triage list — FAIL means "look at this one," not
definitively "wrong garment."

Usage:
    python scripts/glb_fidelity.py [--sku SKU] [--limit N] [--skip-existing]
    python scripts/glb_fidelity.py --sku sg-001
    python scripts/glb_fidelity.py --limit 3
    python scripts/glb_fidelity.py --skip-existing
"""

from __future__ import annotations

import argparse
import atexit
import hashlib
import http.server
import json
import os
import re
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# ── repo root ──────────────────────────────────────────────────────────────────
# This script lives in scripts/ inside a git worktree. GLBs and hub assets are
# gitignored, so they live only in the main repo checkout — not the worktree.
# We find the main repo via --git-common-dir (the shared .git directory).
_WORKTREE_ROOT = Path(__file__).resolve().parent.parent


def _main_repo_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "-C", str(_WORKTREE_ROOT), "rev-parse", "--git-common-dir"],
            capture_output=True,
            text=True,
            check=True,
        )
        git_common = Path(result.stdout.strip())
        if not git_common.is_absolute():
            git_common = _WORKTREE_ROOT / git_common
        return git_common.resolve().parent
    except subprocess.CalledProcessError:
        return _WORKTREE_ROOT  # fallback: running in the main repo directly


REPO_ROOT: Path = _main_repo_root()

# Ensure fidelity module is importable from the main repo.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# ── paths ──────────────────────────────────────────────────────────────────────
GLB_DIR: Path = REPO_ROOT / "renders" / "3d" / "web"
HUB_ROOT: Path = REPO_ROOT / "assets" / "hub" / "collections"
QC_DIR: Path = REPO_ROOT / "renders" / "3d" / "qc"
VENDOR_DIR: Path = QC_DIR / "_vendor"
HTML_CACHE: Path = QC_DIR / "_html_cache"

_MV_CDN = "https://unpkg.com/@google/model-viewer@4.0.0/dist/model-viewer.min.js"
# Pinned SHA-256 of the vendored module — a CDN compromise otherwise executes
# arbitrary JS inside the QC browser (which can reach the localhost server).
_MV_SHA256 = "774edda21e1be2a0934e460ca5943af1fe3f88da130a9f98bd6a9d611576cacf"
_MV_LOCAL = VENDOR_DIR / "model-viewer.min.js"

# Decoder URLs — absolute from HTTP server root (REPO_ROOT).
# Draco: gstatic CDN (meshopt/KTX2 decoders are local in renders/3d/_viewer/).
_DRACO_CDN = "https://www.gstatic.com/draco/versioned/decoders/1.5.6/"
_MESHOPT_REL = "/renders/3d/_viewer/meshopt_decoder.js"
_KTX2_REL = "/renders/3d/_viewer/basis/"

# ── collection mapping ─────────────────────────────────────────────────────────
_COLLECTION_MAP: dict[str, str] = {
    "br": "black-rose",
    "lh": "love-hurts",
    "sg": "signature",
    "kids": "kids-capsule",
}
_FRONT_EXTS: tuple[str, ...] = ("webp", "png", "jpg", "jpeg")

# Thresholds — uncalibrated heuristics (render vs product photo, not render vs render).
# CLIP is only available if open_clip_torch is installed.
_COLOR_DELTA_E_MAX = 20.0
_CLIP_SIM_MIN = 0.70
# A blank/failed canvas compresses far below this; real renders are 80KB+.
_MIN_SCREENSHOT_BYTES = 20_000
# Valid SKU stems (e.g. br-001, kids-002) — anything else in the GLB dir is skipped.
_SKU_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


# ── helpers ────────────────────────────────────────────────────────────────────


def _collection_slug(sku: str) -> str:
    prefix = sku.split("-")[0]
    slug = _COLLECTION_MAP.get(prefix)
    if slug is None:
        raise ValueError(f"Unknown SKU prefix {prefix!r} for SKU {sku!r}")
    return slug


def _hub_master(sku: str) -> Path | None:
    """Return the verified hub front image path for a SKU, or None if absent."""
    try:
        col = _collection_slug(sku)
    except ValueError:
        return None
    base = HUB_ROOT / col / "products" / sku
    for ext in _FRONT_EXTS:
        p = base / f"front.{ext}"
        if p.exists():
            return p
    return None


def _all_skus() -> list[str]:
    """Return all valid GLB SKUs sorted by stem; skip files with unexpected names."""
    skus: list[str] = []
    for p in GLB_DIR.glob("*.glb"):
        if _SKU_RE.fullmatch(p.stem):
            skus.append(p.stem)
        else:
            print(f"  ! skipping non-SKU glb name: {p.name}", flush=True)
    return sorted(skus)


# ── vendor: download model-viewer once ────────────────────────────────────────


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _ensure_model_viewer() -> None:
    """Ensure the vendored model-viewer module exists AND matches the pinned SHA-256."""
    if _MV_LOCAL.exists():
        got = _sha256(_MV_LOCAL)
        if got == _MV_SHA256:
            return
        sys.exit(
            f"vendored model-viewer hash mismatch (got {got[:16]}…, want {_MV_SHA256[:16]}…) — "
            f"delete {_MV_LOCAL} only if you trust a re-download, then re-run"
        )
    VENDOR_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {_MV_CDN} ...", flush=True)
    urllib.request.urlretrieve(_MV_CDN, _MV_LOCAL)
    got = _sha256(_MV_LOCAL)
    if got != _MV_SHA256:
        _MV_LOCAL.unlink(missing_ok=True)
        sys.exit(f"downloaded model-viewer failed integrity check ({got[:16]}…) — aborting")
    print(f"  -> {_MV_LOCAL} ({_MV_LOCAL.stat().st_size:,} B, sha256 verified)", flush=True)


# ── HTTP server ────────────────────────────────────────────────────────────────


class _ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def _start_http_server(serve_dir: Path) -> tuple[int, _ReusableTCPServer]:
    """Start a background HTTP server rooted at serve_dir. Returns (port, server)."""

    class _Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=str(serve_dir), **kwargs)

        def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A002
            pass  # suppress per-request noise

    server = _ReusableTCPServer(("127.0.0.1", 0), _Handler)
    port: int = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return port, server


# ── HTML template ──────────────────────────────────────────────────────────────


def _make_html(sku: str, port: int) -> str:
    """Return per-SKU page HTML with correct decoder config and load-event signalling."""
    glb_url = f"http://127.0.0.1:{port}/renders/3d/web/{sku}.glb"
    mv_url = f"http://127.0.0.1:{port}/renders/3d/qc/_vendor/model-viewer.min.js"
    meshopt_url = f"http://127.0.0.1:{port}{_MESHOPT_REL}"
    ktx2_url = f"http://127.0.0.1:{port}{_KTX2_REL}"

    # JS curly braces must be doubled inside an f-string: {{ -> {, }} -> }
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ margin:0; padding:0; box-sizing:border-box }}
body {{ background:#e8e8e8; width:800px; height:1000px; overflow:hidden }}
model-viewer {{
  width:800px; height:1000px;
  background-color:#e8e8e8;
  --progress-bar-color:transparent;
}}
</style>
<script>
/* Decoder config MUST run before the model-viewer ES module loads.
   Draco: gstatic CDN (verified). meshopt + KTX2: local vendored files. */
self.ModelViewerElement = self.ModelViewerElement || {{}};
self.ModelViewerElement.dracoDecoderLocation = '{_DRACO_CDN}';
self.ModelViewerElement.meshoptDecoderLocation = '{meshopt_url}';
self.ModelViewerElement.ktx2TranscoderLocation = '{ktx2_url}';
</script>
<script type="module" src="{mv_url}"></script>
</head>
<body>
<model-viewer
  id="mv"
  src="{glb_url}"
  camera-orbit="0deg 90deg auto"
  auto-rotate="false"
  camera-controls="false"
  shadow-intensity="1"
  exposure="1"
  loading="eager"
  reveal="auto">
</model-viewer>
<script>
window._mvLoaded = false;
window._mvError  = false;
window._mvErrMsg = '';
document.getElementById('mv').addEventListener('load', () => {{
  window._mvLoaded = true;
}});
document.getElementById('mv').addEventListener('error', (e) => {{
  window._mvError  = true;
  window._mvErrMsg = (e.detail && e.detail.type) ? e.detail.type : 'unknown';
}});
</script>
</body>
</html>"""


# ── screenshot via Playwright ──────────────────────────────────────────────────


def _screenshot_glb(
    sku: str,
    port: int,
    out_path: Path,
    *,
    timeout_ms: int = 30_000,
    settle_ms: int = 800,
) -> tuple[bool, str, bool, bool]:
    """
    Render the GLB and save a PNG screenshot.

    Returns:
        (screenshot_ok, message, mv_loaded, mv_errored)
        screenshot_ok = True if file >20KB (non-blank canvas)
    """
    from playwright.sync_api import TimeoutError as PWTimeout  # noqa: PLC0415
    from playwright.sync_api import sync_playwright

    # Write HTML to cache dir (same HTTP server root = no CORS issues).
    HTML_CACHE.mkdir(parents=True, exist_ok=True)
    (HTML_CACHE / f"{sku}.html").write_text(_make_html(sku, port), encoding="utf-8")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    page_url = f"http://127.0.0.1:{port}/renders/3d/qc/_html_cache/{sku}.html"

    mv_loaded = False
    mv_errored = False
    timed_out = False

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        ctx = browser.new_context(viewport={"width": 800, "height": 1000})
        page = ctx.new_page()
        page.goto(page_url, wait_until="domcontentloaded")

        try:
            page.wait_for_function(
                "() => window._mvLoaded === true || window._mvError === true",
                timeout=timeout_ms,
            )
        except PWTimeout:
            timed_out = True

        # Extra GPU compositing settle time.
        time.sleep(settle_ms / 1000)
        page.screenshot(path=str(out_path), full_page=False)

        # Read JS flags before closing.
        try:
            mv_loaded = bool(page.evaluate("() => window._mvLoaded"))
            mv_errored = bool(page.evaluate("() => window._mvError"))
        except Exception:  # noqa: BLE001
            pass

        browser.close()

    size = out_path.stat().st_size if out_path.exists() else 0
    ok = size > _MIN_SCREENSHOT_BYTES

    parts = []
    if mv_loaded:
        parts.append("loaded")
    elif mv_errored:
        parts.append("mv_error")
    elif timed_out:
        parts.append("timeout")
    parts.append(f"{size:,}B")
    msg = " ".join(parts) if parts else "unknown"
    return ok, msg, mv_loaded, mv_errored


# ── color spec from hub master ─────────────────────────────────────────────────


def _color_spec_from_image(image_path: Path, top_n: int = 4) -> dict[str, Any]:
    """
    Extract the top dominant colors from a master image as a fidelity color_spec.

    Returns {"primary": "#hex", "accents": ["#hex", ...]} or {} if extraction fails.
    """
    try:
        from PIL import Image  # noqa: PLC0415
    except ImportError:
        return {}

    try:
        with Image.open(image_path) as img:
            img_rgb = img.convert("RGB").resize((128, 128))
            palette = img_rgb.quantize(
                colors=max(top_n * 2, 16),
                method=Image.Quantize.FASTOCTREE,
            )
            counts = palette.getcolors() or []
            pal = palette.getpalette() or []

        hexes: list[str] = []
        for _count, idx in sorted(counts, key=lambda p: -p[0])[:top_n]:
            base = idx * 3
            if base + 2 < len(pal):
                r, g, b = pal[base], pal[base + 1], pal[base + 2]
                hexes.append(f"#{r:02x}{g:02x}{b:02x}")

        if not hexes:
            return {}
        return {"primary": hexes[0], "accents": hexes[1:]}
    except Exception:  # noqa: BLE001
        return {}


# ── fidelity scoring ───────────────────────────────────────────────────────────


def _run_fidelity(screenshot: Path, master: Path | None) -> dict[str, Any]:
    """
    Run color ΔE and CLIP checks against the hub master.

    Returns a flat dict with color_delta_e, color_pass, clip_score, clip_pass, verdict.
    Verdict is one of: pass | fail | no_master | no_checks | no_screenshot.
    """
    if master is None:
        return {
            "color_delta_e": None,
            "color_pass": None,
            "clip_score": None,
            "clip_pass": None,
            "verdict": "no_master",
        }
    if not screenshot.exists():
        return {
            "color_delta_e": None,
            "color_pass": None,
            "clip_score": None,
            "clip_pass": None,
            "verdict": "no_screenshot",
        }

    from skyyrose.elite_studio.fidelity import check_clip_similarity, check_color  # noqa: PLC0415

    # Color: extract dominant palette from master → compare against screenshot.
    color_spec = _color_spec_from_image(master)
    color_r = (
        check_color(screenshot, color_spec, delta_e_max=_COLOR_DELTA_E_MAX) if color_spec else None
    )

    # CLIP: optional (open_clip_torch). Degrades gracefully to available=False.
    clip_r = check_clip_similarity(screenshot, master, min_similarity=_CLIP_SIM_MIN)

    color_de = color_r.score if (color_r and color_r.available) else None
    color_pass = color_r.passed if (color_r and color_r.available) else None
    clip_score = clip_r.score if clip_r.available else None
    clip_pass = clip_r.passed if clip_r.available else None

    available_checks = [
        c for c in [color_r, clip_r] if c is not None and c.available and c.passed is not None
    ]

    if not available_checks:
        verdict = "no_checks"
    elif all(c.passed for c in available_checks):
        verdict = "pass"
    else:
        verdict = "fail"

    return {
        "color_delta_e": color_de,
        "color_pass": color_pass,
        "clip_score": clip_score,
        "clip_pass": clip_pass,
        "verdict": verdict,
    }


# ── result dataclass ───────────────────────────────────────────────────────────


@dataclass
class SKUResult:
    sku: str
    glb: str
    master: str | None
    screenshot: str | None
    screenshot_ok: bool
    mv_loaded: bool
    mv_errored: bool
    color_delta_e: float | None
    color_pass: bool | None
    clip_score: float | None
    clip_pass: bool | None
    verdict: str
    error: str | None = None


def _fmt_row(r: SKUResult) -> str:
    de = f"{r.color_delta_e:5.1f}" if r.color_delta_e is not None else "  n/a"
    clip = f"{r.clip_score:.3f}" if r.clip_score is not None else " n/a"
    shot = "ok  " if r.screenshot_ok else "FAIL"
    mv = "L" if r.mv_loaded else ("E" if r.mv_errored else "T")
    return f"  {r.sku:<12}  shot={shot}  mv={mv}  dE={de}  clip={clip}  {r.verdict.upper()}"


# ── main ───────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Headless GLB fidelity gate — screenshot + hub-master comparison"
    )
    parser.add_argument("--sku", help="Run for a single SKU only")
    parser.add_argument("--limit", type=int, help="Process only the first N SKUs")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip SKUs that already have a >20KB screenshot",
    )
    args = parser.parse_args()

    # ── resolve SKU list ─────────────────────────────────────────────────────
    skus = _all_skus()
    if not skus:
        sys.exit(f"No GLBs found in {GLB_DIR}")

    if args.sku:
        if args.sku not in skus:
            sys.exit(f"SKU {args.sku!r} has no GLB in {GLB_DIR}")
        skus = [args.sku]
    if args.limit:
        skus = skus[: args.limit]

    print(
        f"GLB fidelity gate — {len(skus)} SKU(s) | REPO_ROOT={REPO_ROOT}",
        flush=True,
    )
    print(
        "Thresholds: color ΔE ≤ 20.0 (heuristic), "
        "CLIP ≥ 0.70 (heuristic, available only with open_clip_torch)",
        flush=True,
    )

    # ── vendor ───────────────────────────────────────────────────────────────
    _ensure_model_viewer()

    # ── HTTP server — serve a temp root exposing ONLY the four asset trees the
    # viewer needs. Rooting at REPO_ROOT would expose .env* and every other
    # repo file to any JS running in the QC browser.
    serve_root = Path(tempfile.mkdtemp(prefix="glbqc-"))
    # atexit (not try/finally) so the symlink tree is reclaimed on EVERY exit
    # path — unhandled exceptions included. rmtree removes links, never targets.
    atexit.register(shutil.rmtree, serve_root, ignore_errors=True)
    (serve_root / "renders" / "3d").mkdir(parents=True)
    (serve_root / "renders" / "3d" / "qc").mkdir(parents=True)
    HTML_CACHE.mkdir(parents=True, exist_ok=True)
    VENDOR_DIR.mkdir(parents=True, exist_ok=True)
    os.symlink(GLB_DIR, serve_root / "renders" / "3d" / "web")
    os.symlink(REPO_ROOT / "renders" / "3d" / "_viewer", serve_root / "renders" / "3d" / "_viewer")
    os.symlink(VENDOR_DIR, serve_root / "renders" / "3d" / "qc" / "_vendor")
    os.symlink(HTML_CACHE, serve_root / "renders" / "3d" / "qc" / "_html_cache")
    http_port, http_server = _start_http_server(serve_root)
    print(f"HTTP server port={http_port} root={serve_root} (symlink-only)", flush=True)

    results: list[SKUResult] = []
    t_start = time.monotonic()

    for sku in skus:
        glb_path = GLB_DIR / f"{sku}.glb"
        master = _hub_master(sku)
        qc_png = QC_DIR / f"{sku}_front.png"

        t_sku = time.monotonic()
        print(f"\n[{sku}]", end="  ", flush=True)

        shot_ok = False
        mv_loaded = False
        mv_errored = False
        error: str | None = None

        # ── screenshot ───────────────────────────────────────────────────────
        if args.skip_existing and qc_png.exists() and qc_png.stat().st_size > _MIN_SCREENSHOT_BYTES:
            shot_ok = True
            mv_loaded = True  # assume loaded if we already have a good screenshot
            print("screenshot=cached", end="  ", flush=True)
        else:
            try:
                shot_ok, msg, mv_loaded, mv_errored = _screenshot_glb(sku, http_port, qc_png)
                print(f"screenshot={msg}", end="  ", flush=True)
            except Exception as exc:  # noqa: BLE001
                error = f"screenshot_err:{exc}"
                print(f"screenshot=ERROR({exc})", end="  ", flush=True)

        # ── fidelity scoring ─────────────────────────────────────────────────
        scores: dict[str, Any]
        if shot_ok and qc_png.exists():
            try:
                scores = _run_fidelity(qc_png, master)
            except Exception as exc:  # noqa: BLE001
                scores = {
                    "color_delta_e": None,
                    "color_pass": None,
                    "clip_score": None,
                    "clip_pass": None,
                    "verdict": "error",
                }
                error = (error or "") + f" fidelity_err:{exc}"
        else:
            scores = {
                "color_delta_e": None,
                "color_pass": None,
                "clip_score": None,
                "clip_pass": None,
                "verdict": "no_screenshot",
            }

        elapsed = time.monotonic() - t_sku
        r = SKUResult(
            sku=sku,
            glb=str(glb_path),
            master=str(master) if master else None,
            screenshot=str(qc_png) if qc_png.exists() else None,
            screenshot_ok=shot_ok,
            mv_loaded=mv_loaded,
            mv_errored=mv_errored,
            error=error,
            **scores,
        )
        results.append(r)
        print(f"verdict={r.verdict}  ({elapsed:.1f}s)", flush=True)

    # ── stop HTTP server ─────────────────────────────────────────────────────
    http_server.shutdown()

    total_elapsed = time.monotonic() - t_start

    # ── print results table ──────────────────────────────────────────────────
    print("\n── GLB Fidelity Results ──────────────────────────────────────────────────")
    print("  SKU           shot  mv  dE       clip    verdict\n  (mv: L=loaded E=error T=timeout)")
    for r in results:
        print(_fmt_row(r))

    verdicts = [r.verdict for r in results]
    n_pass = verdicts.count("pass")
    n_fail = verdicts.count("fail")
    n_no_master = verdicts.count("no_master")
    n_no_checks = verdicts.count("no_checks")
    n_other = sum(1 for v in verdicts if v not in ("pass", "fail", "no_master", "no_checks"))
    print(
        f"\n  PASS={n_pass}  FAIL={n_fail}  NO_MASTER={n_no_master}  "
        f"NO_CHECKS={n_no_checks}  OTHER={n_other}  TOTAL={len(results)}"
    )
    print(f"  Total time: {total_elapsed:.1f}s  ({total_elapsed / len(results):.1f}s/SKU)")

    # ── write JSON report ─────────────────────────────────────────────────────
    QC_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": (
            "Color ΔE threshold=20.0 and CLIP threshold=0.70 are uncalibrated "
            "heuristics for render-vs-photo comparison. Use FAIL as 'triage flag', "
            "not as ground-truth wrong-garment detection."
        ),
        "skus": [asdict(r) for r in results],
        "summary": {
            "pass": n_pass,
            "fail": n_fail,
            "no_master": n_no_master,
            "no_checks": n_no_checks,
            "other": n_other,
            "total": len(results),
            "elapsed_s": round(total_elapsed, 1),
        },
    }
    report_path = QC_DIR / "fidelity_report.json"
    tmp_path = report_path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    os.replace(tmp_path, report_path)  # atomic — a crash never leaves a half-written report
    print(f"\n  Report -> {report_path}", flush=True)


if __name__ == "__main__":
    main()

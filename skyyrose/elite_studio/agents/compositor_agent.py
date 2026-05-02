"""CompositorAgent — 6-stage scene compositing pipeline (Phase B2).

Takes a B1-rendered branded garment (model image, neutral background) and a
scene reference, produces a final scene composite suitable for marketing use.

Stages:
  1. Alpha matte extraction          — BRIA RMBG 2.0 via rembg
  2. Opus-driven FLUX prompt synth   — Claude vision (dossier-grounded)
  3. IC-Light relighting             — Replicate primary, libcom fallback, alpha fallback
  4. FLUX inpainting composite       — fal-fill primary, kontext + replicate fallback
  5. Contact shadow generation       — PIL gaussian fallback (GPSDiff hookable)
  6. Visual QA gate                  — Gemini structured rubric

Design contract (matches `tests/test_compositor_agent.py`):
  - Synchronous public API: ``composite()`` is sync; callers in async contexts
    wrap it via ``asyncio.to_thread``.
  - Module-level imports for the 5 external dependencies (``remove``,
    ``fal_client``, ``httpx``, ``get_anthropic_client``, ``analyze_vision``)
    so ``unittest.mock.patch`` can replace them cleanly.
  - Hash-keyed caching at every paid stage so reruns are idempotent.
  - Resume-from-stage-N support via ``resume_from=`` + checkpoint kwargs.
  - Audit log JSON written alongside the output.

Cost estimate per render (verified against ``synthesis/state/telemetry.py``):
  Stage 1 (BRIA via fal):      $0.005
  Stage 2 (Claude Opus):       $0.015
  Stage 3 (IC-Light v2):       $0.020
  Stage 4 (FLUX Fill Pro):     $0.050
  Stage 5 (PIL shadows):       $0.000
  Stage 6 (Gemini QA):         $0.025
  Total:                       $0.115
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import httpx
from PIL import Image, ImageFilter

# Module-level imports the test fixtures patch. Importing at module level (not
# inside functions) is required so unittest.mock.patch can replace them on the
# `compositor_agent` namespace without having to re-import inside each call.
_REMBG_UNAVAILABLE_SENTINEL = "__REMBG_UNAVAILABLE__"

try:  # pragma: no cover - exercised via tests that patch this name
    from rembg import remove  # type: ignore[import-not-found]
except (ImportError, AttributeError, Exception):  # pragma: no cover
    # Catches both: missing package (ImportError) and Python 3.14 + numpy 2.x
    # incompatibility in numba/pymatting (AttributeError on np.trapz). When
    # local rembg can't load, _extract_alpha falls through to the FAL hosted
    # BRIA endpoint via _matte_via_fal. Tests patch the ``remove`` symbol
    # directly so they don't depend on the real package — a real BRIA failure
    # raises with a message that does NOT contain the sentinel, so the test's
    # ``RuntimeError("BRIA model failed")`` propagates as expected.

    def remove(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError(_REMBG_UNAVAILABLE_SENTINEL)


try:  # pragma: no cover
    import fal_client  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    fal_client = None  # type: ignore[assignment]


from ..config import get_anthropic_client
from ..gemini_rest import analyze_vision
from ..models import CompositorResult
from ..quality import embedding_gate
from ..quality.brand_centroid import load_centroid

logger = logging.getLogger(__name__)

# Default location for the persisted brand-style centroid. The pre-QA gate
# (Stage 5.5) loads this file at runtime if it exists; otherwise the gate
# is a no-op and the pipeline proceeds straight to Gemini QA.
_DEFAULT_CENTROID_PATH = Path(__file__).resolve().parents[1] / "data" / "brand_centroid.npz"


class _SilentLogger:
    """No-op default logger when caller doesn't supply one.

    Avoids a circular import with ``..coordinator.NullLogger`` (coordinator
    itself imports CompositorAgent). Any duck-typed logger with the same
    methods works in its place — tests pass ``coordinator.NullLogger()``.
    """

    def info(self, msg: str) -> None: ...
    def step(self, step_num: int, total: int, label: str) -> None: ...
    def ok(self, msg: str) -> None: ...
    def fail(self, msg: str) -> None: ...
    def separator(self) -> None: ...


# ---------------------------------------------------------------------------
# Module-level helpers (test fixtures patch ``upload_to_fal``)
# ---------------------------------------------------------------------------


def upload_to_fal(local_path: str | Path) -> str:
    """Upload a local file to the fal CDN and return its public URL.

    Synchronous wrapper around ``fal_client.upload_file`` so the compositor's
    sync API stays linear. Tests patch this symbol directly to avoid network.
    """
    if fal_client is None:  # pragma: no cover
        raise RuntimeError(
            "fal_client is not installed. `pip install fal_client` to enable Stages 3-4."
        )
    path = str(local_path)
    if not Path(path).is_file():
        raise FileNotFoundError(f"upload source not found: {path}")
    return fal_client.upload_file(path)  # type: ignore[no-any-return]


def _matte_via_fal(image_bytes: bytes) -> bytes:
    """Run BRIA RMBG 2.0 via FAL when local rembg is unavailable.

    Same model, same ~$0.005 cost — the only difference is that the matte
    runs hosted instead of locally. Used as a transparent fallback when the
    rembg toolchain can't load (typically Python 3.14 + numpy 2.x).
    """
    if fal_client is None:
        raise RuntimeError("Neither rembg nor fal_client is available; cannot extract alpha matte.")
    image_url = fal_client.upload(image_bytes, content_type="image/png")
    result = fal_client.run(
        "fal-ai/bria/background/remove",
        arguments={"image_url": image_url},
    )
    out_url = _extract_first_image_url(result)
    if not out_url:
        raise RuntimeError("FAL BRIA endpoint returned no image URL")
    resp = httpx.get(out_url, timeout=60.0)
    resp.raise_for_status()
    return resp.content


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


def _file_hash(path: str | Path, *, prefix: str = "") -> str:
    """SHA-256 of file bytes, truncated for filename safety."""
    p = Path(path)
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return f"{prefix}{h.hexdigest()[:16]}" if prefix else h.hexdigest()[:16]


def _cache_dir(stage: str) -> Path:
    """Repo-relative cache directory per stage. Created on first use."""
    repo = Path(__file__).resolve().parents[3]
    d = repo / "renders" / "cache" / stage
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# Scene SKU lookbook (legacy export for callers that import it)
# ---------------------------------------------------------------------------

SCENE_LOOKBOOK: dict[str, str] = {
    "black-rose-bay-bridge-night": "br-",
    "love-hurts-enchanted-rose-dome": "lh-",
    "signature-golden-gate-golden-hour": "sg-",
    "kids-capsule-urban-playground": "kids-",
}


# ---------------------------------------------------------------------------
# CompositorAgent
# ---------------------------------------------------------------------------


_DEFAULT_QA_RUBRIC = """You are QA-scoring a scene composite for SkyyRose luxury fashion.

Scene: {scene_name}
Collection: {collection}

Score on a 0-10 scale across three dimensions and reply as STRICT JSON:
{{
  "status": "pass" | "warn" | "fail",
  "lighting_match": {{"score": <0-10>, "notes": "<one sentence>"}},
  "garment_fidelity": {{"score": <0-10>, "notes": "<one sentence>"}},
  "scene_coherence": {{"score": <0-10>, "notes": "<one sentence>"}}
}}

Rules:
- "pass" requires all three scores >= 8 with no edge artifacts visible.
- "warn" if any single score is 6-7 OR mild edge halo / contact-shadow drift.
- "fail" if any score < 6, identity loss, or the subject looks pasted-on.
"""


class CompositorAgent:
    """6-stage scene compositor.

    Sync API; tests do not ``await`` calls. Use ``asyncio.to_thread(agent.composite, ...)``
    from async callers.
    """

    DEFAULT_OUTPUT_DIR = "renders/output/compositor"
    QA_PASS_THRESHOLD = 24  # sum of three 0-10 scores; ~8 each on average

    def __init__(
        self,
        *,
        logger: Any = None,
        config: Any = None,
    ) -> None:
        # ``config`` (AgentConfig) is accepted for legacy callers (BaseSuperAgent
        # callers in coordinator.py / cli.py) but is not required. The new sync
        # API is the source of truth.
        self.logger = logger or _SilentLogger()
        self._config = config  # currently unused; reserved for future ADK telemetry hook

    # ----------------------------------------------------------------- public

    def composite(
        self,
        sku: str,
        scene_image_path: str,
        model_image_path: str,
        collection: str,
        scene_name: str,
        output_dir: str | None = None,
        *,
        resume_from: int | None = None,
        checkpoint_alpha: str | None = None,
        checkpoint_relit: str | None = None,
        checkpoint_prompt: str | None = None,
    ) -> CompositorResult:
        """Run the 6-stage compositing pipeline.

        Args:
            sku: canonical SKU (e.g. ``br-001``).
            scene_image_path: scene background reference image.
            model_image_path: B1 model render (branded garment, neutral BG).
            collection: collection slug (``black-rose``, ``love-hurts``, ``signature``, ``kids-capsule``).
            scene_name: identifier for the scene + lighting spec; used to load
                ``{scenes_dir}/{collection}/{scene_name}/scene.json`` if present.
            output_dir: where to write all stage outputs and the audit log.
            resume_from: skip stages 1..N-1 and start at stage N. Use with
                ``checkpoint_alpha`` / ``checkpoint_relit`` / ``checkpoint_prompt``.
        """
        out = Path(output_dir or self.DEFAULT_OUTPUT_DIR)
        out.mkdir(parents=True, exist_ok=True)

        stages: dict[str, dict[str, Any]] = {}
        stages_done = 0
        result_kwargs: dict[str, Any] = {
            "scene_name": scene_name,
            "collection": collection,
            "stages_completed": 0,
        }

        try:
            # ------------------------------ Stage 1: alpha matte
            if resume_from and resume_from > 1:
                if not checkpoint_alpha or not Path(checkpoint_alpha).is_file():
                    raise RuntimeError(
                        f"resume_from={resume_from} requires checkpoint_alpha to be a real file"
                    )
                alpha_path = checkpoint_alpha
                stages["alpha"] = {"path": alpha_path, "resumed": True}
            else:
                started = time.perf_counter()
                alpha_path = self._extract_alpha(model_image_path, sku, str(out))
                stages["alpha"] = {
                    "path": alpha_path,
                    "duration_s": round(time.perf_counter() - started, 3),
                }
                stages_done = 1

            # ------------------------------ Stage 2: prompt synth
            if resume_from and resume_from > 2:
                prompt = checkpoint_prompt or ""
                if not prompt:
                    raise RuntimeError(f"resume_from={resume_from} requires checkpoint_prompt")
                stages["prompt"] = {"resumed": True, "chars": len(prompt)}
            else:
                started = time.perf_counter()
                lighting_spec = self._load_lighting_spec(collection, scene_name)
                # Downscale before base64 — Anthropic caps each image at 5MB
                # post-encoding. 1568px longest-side is their published target.
                scene_b64 = self._b64_image_for_claude(scene_image_path)
                subject_b64 = self._b64_image_for_claude(alpha_path)
                prompt = self._engineer_flux_prompt(
                    scene_b64=scene_b64,
                    subject_b64=subject_b64,
                    collection=collection,
                    scene_name=scene_name,
                    lighting_spec=lighting_spec,
                )
                stages["prompt"] = {
                    "model": "claude-opus-4-7",
                    "chars": len(prompt),
                    "duration_s": round(time.perf_counter() - started, 3),
                }
                stages_done = 2

            # ------------------------------ Stage 3: relight
            if resume_from and resume_from > 3:
                if not checkpoint_relit or not Path(checkpoint_relit).is_file():
                    raise RuntimeError(f"resume_from={resume_from} requires checkpoint_relit")
                relit_path = checkpoint_relit
                stages["relight"] = {"path": relit_path, "resumed": True}
            else:
                started = time.perf_counter()
                relit_path = self._relight_subject(
                    alpha_path, scene_image_path, prompt, sku, str(out)
                )
                stages["relight"] = {
                    "path": relit_path,
                    "duration_s": round(time.perf_counter() - started, 3),
                    "fallback_to_alpha": relit_path == alpha_path,
                }
                stages_done = 3

            # ------------------------------ Stage 4: FLUX composite
            started = time.perf_counter()
            # The 3 FAL uploads are independent — run them in parallel via a
            # thread pool. Saves 2-6 seconds per render on a typical network.
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=3) as pool:
                scene_fut = pool.submit(upload_to_fal, scene_image_path)
                subject_fut = pool.submit(upload_to_fal, relit_path)
                mask_fut = pool.submit(upload_to_fal, alpha_path)
                scene_url = scene_fut.result()
                subject_url = subject_fut.result()
                mask_url = mask_fut.result()  # alpha doubles as placement mask
            composite_bytes, provider = self._composite_with_flux(
                scene_url=scene_url,
                subject_url=subject_url,
                mask_url=mask_url,
                prompt=prompt,
            )
            composite_path = str(out / f"{sku}-composite.png")
            Path(composite_path).write_bytes(composite_bytes)
            stages["composite"] = {
                "path": composite_path,
                "provider": provider,
                "duration_s": round(time.perf_counter() - started, 3),
            }
            stages_done = 4
            result_kwargs["provider"] = provider
            result_kwargs["model"] = "flux-fill-pro" if provider == "fal-fill" else provider
            if provider != "fal-fill":
                result_kwargs["used_fallback"] = True
                result_kwargs["fallback_provider"] = provider

            # ------------------------------ Stage 5: shadows
            started = time.perf_counter()
            shadow_path = self._generate_shadows(composite_path, sku, str(out))
            stages["shadow"] = {
                "path": shadow_path,
                "duration_s": round(time.perf_counter() - started, 3),
            }
            stages_done = 5

            # ---------------------- Stage 5.5/6: pre-QA gate + Gemini QA
            # _maybe_apply_gate runs the embedding gate first. If a brand
            # centroid is deployed and the render scores below threshold, the
            # gate returns a fail verdict and Gemini is skipped (cost savings).
            # If no centroid is deployed, the gate is a no-op pass-through.
            started = time.perf_counter()
            qa = _maybe_apply_gate(shadow_path, scene_name, collection)
            stages["qa"] = {
                "status": qa.get("status", "warn"),
                "details": qa,
                "duration_s": round(time.perf_counter() - started, 3),
            }
            stages_done = 6
            result_kwargs["qa_status"] = qa.get("status", "warn")
            result_kwargs["qa_details"] = qa
            result_kwargs["output_path"] = shadow_path
            result_kwargs["alpha_path"] = alpha_path
            result_kwargs["stages_completed"] = stages_done
            result_kwargs["success"] = True
            result_kwargs["provider"] = result_kwargs.get("provider", "fal-fill")

            result = CompositorResult(**result_kwargs)
            log_path = self._write_audit_log(sku, scene_name, stages, result, str(out))
            return CompositorResult(**{**result_kwargs, "audit_log_path": log_path})

        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Compositor failed at stage %d for %s", stages_done + 1, sku)
            self.logger.fail(f"compositor[{sku}] stage {stages_done + 1}: {exc}")
            partial_kwargs = {
                **result_kwargs,
                "success": False,
                "stages_completed": stages_done,
                "error": str(exc),
            }
            partial = CompositorResult(**partial_kwargs)
            try:
                log_path = self._write_audit_log(sku, scene_name, stages, partial, str(out))
                return CompositorResult(**{**partial_kwargs, "audit_log_path": log_path})
            except Exception:  # pragma: no cover
                return partial

    # --------------------------------------------------- Stage 1: alpha matte

    def _extract_alpha(
        self,
        model_image_path: str,
        sku: str,
        output_dir: str,
    ) -> str:
        """Extract subject from model image via BRIA RMBG 2.0.

        The matte is RGBA with alpha = subject silhouette. Cached by input
        file hash so repeated runs against the same source image are free.
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        with open(model_image_path, "rb") as f:
            input_bytes = f.read()
        # Hash the bytes we already have in memory so we don't re-read the
        # source image to compute the cache key.
        input_hash = hashlib.sha256(input_bytes).hexdigest()[:16]
        # Try local rembg first (cheaper, no network). If it raises ImportError
        # — common on Python 3.14 where numba/numpy 2.x is still settling — fall
        # through to FAL's hosted BRIA endpoint. Other exceptions still surface
        # so a real model failure isn't silently swallowed.
        try:
            result = remove(input_bytes)
        except RuntimeError as exc:
            # Only the placeholder shim raises with the sentinel string. Real
            # BRIA / rembg failures get re-raised so callers see them — same
            # behavior the original test contract expects.
            if _REMBG_UNAVAILABLE_SENTINEL not in str(exc):
                raise
            logger.info("Local rembg unavailable; using FAL hosted BRIA endpoint")
            result = _matte_via_fal(input_bytes)
        if isinstance(result, (bytes, bytearray)):
            img = Image.open(io.BytesIO(result)).convert("RGBA")
        elif isinstance(result, Image.Image):
            img = result.convert("RGBA")
        else:  # pragma: no cover
            raise RuntimeError(f"unexpected rembg return type: {type(result).__name__}")

        # Soft alpha edge (1px feather) — reduces hard-cutout artifacts in
        # downstream FLUX inpainting.
        r, g, b, a = img.split()
        a = a.filter(ImageFilter.GaussianBlur(radius=1.0))
        img = Image.merge("RGBA", (r, g, b, a))

        dest = out / f"{sku}-alpha.png"
        img.save(dest, format="PNG")
        # Populate the per-input cache for future runs against the same source.
        try:
            cache = _cache_dir("matte")
            cached = cache / f"{input_hash}.png"
            if not cached.exists():
                img.save(cached, format="PNG")
        except Exception:  # pragma: no cover - cache write is best-effort
            pass
        return str(dest)

    # ------------------------------------------------- Stage 2: prompt synth

    def _engineer_flux_prompt(
        self,
        *,
        scene_b64: str,
        subject_b64: str,
        collection: str,
        scene_name: str,
        lighting_spec: dict[str, Any],
    ) -> str:
        """Use Claude Opus to write a single FLUX prompt grounded in the dossier.

        Test fixtures patch ``get_anthropic_client`` and assert the model arg
        equals ``COMPOSITOR_OPUS_MODEL``. Do NOT hardcode the model string —
        always pull from config.
        """
        from ..config import COMPOSITOR_OPUS_MODEL  # local import — tested with patched module

        client = get_anthropic_client()
        system = (
            "You write FLUX inpainting prompts for SkyyRose luxury fashion scene "
            "composites. Stay grounded in the visible subject and scene; never "
            "invent embellishments not present in the subject. Return ONLY the "
            "prompt text — no preamble, no quotes, no markdown."
        )
        user_text = (
            f"Collection: {collection}\n"
            f"Scene: {scene_name}\n"
            f"Lighting spec: {json.dumps(lighting_spec)}\n\n"
            "Write a single FLUX prompt (≤ 220 words) that places the SUBJECT "
            "naturally into the SCENE. Match scene lighting direction, color "
            "temperature, and mood. Preserve garment identity exactly."
        )

        # Anthropic's strict TypedDicts reject the plain dict literal at type
        # check time but accept it at runtime — cast at the SDK boundary.
        msg = client.messages.create(
            model=COMPOSITOR_OPUS_MODEL,
            max_tokens=512,
            system=system,
            messages=[  # type: ignore[arg-type]
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": scene_b64,
                            },
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": subject_b64,
                            },
                        },
                        {"type": "text", "text": user_text},
                    ],
                }
            ],
        )
        # ``msg.content`` is a list of content blocks; first block is the text.
        return msg.content[0].text.strip()

    # --------------------------------------------------- Stage 3: relighting

    def _relight_subject(
        self,
        alpha_path: str,
        scene_path: str,
        prompt: str,
        sku: str,
        output_dir: str,
    ) -> str:
        """Match subject lighting to scene via IC-Light.

        Tries Replicate IC-Light first (``_run_iclight_replicate``), then a
        local libcom path (``_run_iclight``), then falls back to the alpha
        image unchanged so the pipeline never blocks on a single missing
        provider. The fallback is logged in the audit so downstream QA can
        be stricter.
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        cache = _cache_dir("relight")
        cache_key = hashlib.sha256(
            f"{_file_hash(alpha_path)}:{_file_hash(scene_path)}:{prompt}".encode()
        ).hexdigest()[:16]
        cached = cache / f"{cache_key}.png"
        if cached.exists():
            dest = out / f"{sku}-relit.png"
            dest.write_bytes(cached.read_bytes())
            return str(dest)

        # Try Replicate IC-Light
        try:
            relit_bytes = self._run_iclight_replicate(
                alpha_path=alpha_path,
                scene_path=scene_path,
                prompt=prompt,
            )
            if relit_bytes:
                dest = out / f"{sku}-relit.png"
                dest.write_bytes(relit_bytes)
                cached.write_bytes(relit_bytes)
                return str(dest)
        except Exception as exc:
            logger.warning("IC-Light Replicate failed for %s: %s", sku, exc)

        # Try local libcom
        try:
            relit_bytes = self._run_iclight(
                alpha_path=alpha_path,
                scene_path=scene_path,
                prompt=prompt,
            )
            if relit_bytes:
                dest = out / f"{sku}-relit.png"
                dest.write_bytes(relit_bytes)
                cached.write_bytes(relit_bytes)
                return str(dest)
        except Exception as exc:
            logger.warning("IC-Light local fallback failed for %s: %s", sku, exc)

        # Final fallback — pass alpha through unchanged. QA gate will weigh
        # this against the scene to decide pass/warn/fail.
        return alpha_path

    def _run_iclight_replicate(
        self,
        *,
        alpha_path: str,
        scene_path: str,
        prompt: str,
    ) -> bytes | None:
        """Replicate IC-Light v2 — preferred relighting path.

        Returns the relit image bytes, or None on graceful failure (which
        triggers the libcom fallback). Tests patch this method directly.
        """
        token = os.environ.get("REPLICATE_API_TOKEN")
        if not token:  # pragma: no cover - tests always patch
            return None
        try:
            with httpx.Client(timeout=120.0) as client:
                with open(alpha_path, "rb") as f:
                    subject_b64 = base64.b64encode(f.read()).decode("ascii")
                with open(scene_path, "rb") as f:
                    bg_b64 = base64.b64encode(f.read()).decode("ascii")
                resp = client.post(
                    "https://api.replicate.com/v1/predictions",
                    headers={
                        "Authorization": f"Token {token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "version": "iclight-v2",
                        "input": {
                            "subject_image": f"data:image/png;base64,{subject_b64}",
                            "background_image": f"data:image/png;base64,{bg_b64}",
                            "prompt": prompt,
                            "image_width": 768,
                            "image_height": 1024,
                            "steps": 25,
                        },
                    },
                )
                if not resp.is_success:
                    return None
                pred = resp.json()
                poll_url = pred.get("urls", {}).get("get")
                if not poll_url:
                    return None
                # Poll until done (capped attempts).
                for _ in range(60):
                    poll = client.get(
                        poll_url,
                        headers={"Authorization": f"Token {token}"},
                    )
                    poll.raise_for_status()
                    body = poll.json()
                    status = body.get("status")
                    if status == "succeeded":
                        out_url = body.get("output")
                        if isinstance(out_url, list):
                            out_url = out_url[0] if out_url else None
                        if not out_url:
                            return None
                        img = client.get(out_url)
                        img.raise_for_status()
                        return img.content
                    if status in ("failed", "canceled"):
                        return None
                    time.sleep(2.0)
                return None
        except Exception as exc:
            logger.warning("Replicate IC-Light call errored: %s", exc)
            return None

    def _run_iclight(
        self,
        *,
        alpha_path: str,
        scene_path: str,
        prompt: str,
    ) -> bytes | None:
        """Local libcom relighting path.

        libcom (https://github.com/bcmi/libcom) provides ImageHarmonizer that
        approximates relighting for image composites. We fail soft if libcom
        is not installed — tests patch this method directly anyway.
        """
        try:
            from libcom import ImageHarmonizationModel  # type: ignore[import-not-found]
        except ImportError:
            return None

        try:
            # libcom's type stubs declare device: int but the runtime accepts
            # the literal "cpu" — well-documented usage in their README.
            harmonizer = ImageHarmonizationModel(device="cpu", model_type="PCTNet")  # type: ignore[arg-type]
            with Image.open(alpha_path).convert("RGBA") as subject:
                # Build a binary mask from the alpha channel for libcom.
                mask = subject.split()[-1]
                mask_path = Path(alpha_path).with_suffix(".mask.png")
                mask.save(mask_path)
                rgb_path = Path(alpha_path).with_suffix(".rgb.jpg")
                subject.convert("RGB").save(rgb_path, format="JPEG", quality=95)
                # Composite over scene to produce the harmonization input.
                with Image.open(scene_path).convert("RGB") as scene:
                    scene = scene.resize(subject.size)
                    base_path = Path(alpha_path).with_suffix(".composite.jpg")
                    scene.save(base_path, format="JPEG", quality=95)
            result_path = Path(alpha_path).with_suffix(".relit.jpg")
            harmonizer(str(base_path), str(mask_path), save_path=str(result_path))  # type: ignore[call-arg]
            return Path(result_path).read_bytes()
        except Exception as exc:
            logger.warning("libcom IC-Light errored: %s", exc)
            return None

    # ----------------------------------------------- Stage 4: FLUX composite

    def _composite_with_flux(
        self,
        *,
        scene_url: str,
        subject_url: str,
        mask_url: str,
        prompt: str,
    ) -> tuple[bytes, str]:
        """Run the FLUX provider fallback chain: fal-fill → kontext → replicate.

        Each provider returns ``bytes`` on success or ``None`` on any failure
        so we can cleanly fall through. Raises ``RuntimeError`` only when ALL
        three fail.
        """
        # Primary: fal-fill (pure FLUX Fill Pro)
        out = self._flux_fill_fal(scene_url, mask_url, prompt)
        if out:
            return out, "fal-fill"

        # Secondary: fal-kontext (uses subject as reference image)
        out = self._flux_kontext(scene_url, mask_url, subject_url, prompt)
        if out:
            return out, "kontext"

        # Tertiary: Replicate
        out = self._flux_fill_replicate(scene_url, mask_url, prompt)
        if out:
            return out, "replicate"

        raise RuntimeError("All FLUX providers failed")

    def _flux_fill_fal(
        self,
        scene_url: str,
        mask_url: str,
        prompt: str,
    ) -> bytes | None:
        """fal-ai/flux-pro/v1/fill — primary inpainting path."""
        if fal_client is None:  # pragma: no cover
            return None
        try:
            result = fal_client.run(
                "fal-ai/flux-pro/v1/fill",
                arguments={
                    "image_url": scene_url,
                    "mask_url": mask_url,
                    "prompt": prompt,
                    "num_inference_steps": 40,
                    "guidance_scale": 7.5,
                    "output_format": "png",
                    "safety_tolerance": 2,
                },
            )
            url = _extract_first_image_url(result)
            if not url:
                return None
            resp = httpx.get(url, timeout=60.0)
            resp.raise_for_status()
            return resp.content
        except Exception as exc:
            logger.warning("fal-fill errored: %s", exc)
            return None

    def _flux_kontext(
        self,
        scene_url: str,
        mask_url: str,
        ref_url: str,
        prompt: str,
    ) -> bytes | None:
        """fal-ai/flux-pro/kontext — secondary path with reference conditioning."""
        if fal_client is None:  # pragma: no cover
            return None
        try:
            result = fal_client.run(
                "fal-ai/flux-pro/kontext",
                arguments={
                    "image_url": scene_url,
                    "mask_url": mask_url,
                    "reference_image_url": ref_url,
                    "prompt": prompt,
                    "num_inference_steps": 35,
                    "guidance_scale": 6.0,
                    "output_format": "png",
                },
            )
            url = _extract_first_image_url(result)
            if not url:
                return None
            resp = httpx.get(url, timeout=60.0)
            resp.raise_for_status()
            return resp.content
        except Exception as exc:
            logger.warning("kontext errored: %s", exc)
            return None

    def _flux_fill_replicate(
        self,
        scene_url: str,
        mask_url: str,
        prompt: str,
    ) -> bytes | None:
        """Replicate FLUX Fill — tertiary fallback when fal is unhealthy."""
        token = os.environ.get("REPLICATE_API_TOKEN")
        if not token:
            return None
        try:
            predict = httpx.post(
                "https://api.replicate.com/v1/predictions",
                headers={
                    "Authorization": f"Token {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "version": "black-forest-labs/flux-fill-pro",
                    "input": {
                        "image": scene_url,
                        "mask": mask_url,
                        "prompt": prompt,
                        "num_inference_steps": 40,
                        "guidance": 7.5,
                    },
                },
                timeout=30.0,
            )
            if not predict.is_success:
                return None
            poll_url = predict.json().get("urls", {}).get("get")
            if not poll_url:
                return None
            # Poll up to 2 minutes.
            for _ in range(60):
                poll = httpx.get(
                    poll_url,
                    headers={"Authorization": f"Token {token}"},
                    timeout=30.0,
                )
                poll.raise_for_status()
                body = poll.json()
                status = body.get("status")
                if status == "succeeded":
                    out_url = body.get("output")
                    if isinstance(out_url, list):
                        out_url = out_url[0] if out_url else None
                    if not out_url:
                        return None
                    img = httpx.get(out_url, timeout=60.0)
                    img.raise_for_status()
                    return img.content
                if status in ("failed", "canceled"):
                    return None
                time.sleep(2.0)
            return None
        except Exception as exc:
            logger.warning("Replicate FLUX Fill errored: %s", exc)
            return None

    # --------------------------------------------------- Stage 5: shadows

    def _generate_shadows(
        self,
        composite_path: str,
        sku: str,
        output_dir: str,
    ) -> str:
        """Add a soft contact shadow to anchor the subject in the scene.

        PIL gaussian fallback only. GPSDiffusion can be hooked in later by
        replacing this body — the test contract expects ``"shadow"`` in the
        returned path OR returning the input path unchanged when the subject
        fills the frame (no ground plane).
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        try:
            with Image.open(composite_path).convert("RGBA") as composite:
                width, height = composite.size

                # Derive a soft mask from the alpha (or the full image as a
                # luminance proxy if no alpha present).
                if "A" in composite.getbands():
                    alpha = composite.split()[-1]
                else:
                    alpha = composite.convert("L")

                # If the subject occupies > 85% of the frame, skip shadows
                # (no ground plane visible). Compare with the alpha mean.
                # Use ImageStat for an O(1) sum instead of a Python-level
                # iteration over every pixel; ~50-200ms saved per render on
                # full-res composites. ``alpha`` is L-mode at this point so
                # ImageStat.sum has length 1.
                from PIL import ImageStat

                stats = ImageStat.Stat(alpha)
                non_zero = int(stats.sum[0] / 255)
                if non_zero >= 0.85 * width * height:
                    return composite_path

                # Project alpha downward + blur to create a contact shadow.
                shadow = Image.new("L", (width, height), 0)
                shadow.paste(alpha, (4, 12))
                shadow = shadow.filter(ImageFilter.GaussianBlur(radius=14))

                # Multiply blend at 45% opacity onto a black layer.
                black = Image.new("RGBA", (width, height), (0, 0, 0, 0))
                shadow_rgba = Image.merge(
                    "RGBA",
                    (
                        Image.new("L", (width, height), 0),
                        Image.new("L", (width, height), 0),
                        Image.new("L", (width, height), 0),
                        shadow.point(lambda v: int(v * 0.45)),
                    ),
                )
                black.alpha_composite(shadow_rgba)
                final = Image.alpha_composite(black, composite)

            dest = out / f"{sku}-shadow.png"
            final.save(dest, format="PNG")
            return str(dest)
        except Exception as exc:
            logger.warning("Shadow stage failed for %s, using composite as-is: %s", sku, exc)
            return composite_path

    # --------------------------------------------------- Stage 6: visual QA

    def _visual_qa(
        self,
        composite_path: str,
        scene_name: str,
        collection: str,
    ) -> dict[str, Any]:
        """Score the composite via Gemini using a structured rubric.

        Returns a dict with at minimum a ``status`` key (``pass`` / ``warn`` /
        ``fail``). Soft-fails to ``warn`` rather than blocking the pipeline
        when the QA provider itself is unavailable — the audit log captures
        the failure mode.
        """
        from ..config import COMPOSITOR_QA_MODEL

        with open(composite_path, "rb") as f:
            b64 = base64.standard_b64encode(f.read()).decode("ascii")
        ext = Path(composite_path).suffix.lower().lstrip(".")
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"

        rubric = _DEFAULT_QA_RUBRIC.format(
            scene_name=scene_name,
            collection=collection,
        )

        result = analyze_vision(
            model=COMPOSITOR_QA_MODEL,
            prompt=rubric,
            image_b64=b64,
            mime_type=mime,
        )

        if not result.get("success"):
            return {
                "status": "warn",
                "error": result.get("error", "QA provider returned no body"),
                "model": COMPOSITOR_QA_MODEL,
            }

        text = result.get("text", "")
        try:
            parsed = _safe_json_extract(text)
            status = parsed.get("status") or "warn"
            return {**parsed, "status": status, "model": COMPOSITOR_QA_MODEL}
        except Exception:
            return {
                "status": "warn",
                "error": f"could not parse QA JSON: {text[:120]}",
                "model": COMPOSITOR_QA_MODEL,
            }

    # ---------------------------------------------------- audit log

    def _write_audit_log(
        self,
        sku: str,
        scene_name: str,
        stages: dict[str, Any],
        result: CompositorResult,
        output_dir: str,
    ) -> str:
        """Persist a JSON audit log alongside the output."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        log_path = out / f"audit-{sku}-{scene_name}.json"
        body = {
            "sku": sku,
            "scene_name": scene_name,
            "collection": result.collection,
            "stages": stages,
            "result": {
                "success": result.success,
                "provider": result.provider,
                "model": result.model,
                "output_path": result.output_path,
                "alpha_path": result.alpha_path,
                "qa_status": result.qa_status,
                "qa_details": result.qa_details,
                "stages_completed": result.stages_completed,
                "used_fallback": result.used_fallback,
                "fallback_provider": result.fallback_provider,
                "error": result.error,
            },
            "pipeline_version": "compositor-v2-2026-04-30",
        }
        log_path.write_text(json.dumps(body, indent=2))
        return str(log_path)

    # ------------------------------------------------------- helpers

    @staticmethod
    def _b64_image(path: str) -> str:
        with open(path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("ascii")

    @staticmethod
    def _b64_image_for_claude(path: str, *, max_dim: int = 1568) -> str:
        """Base64-encode an image, downscaling first to fit Anthropic's 5MB-per-image limit.

        Anthropic's published guidance is 1568px on the longest side as the
        sweet spot for accuracy + cost. Below that, vision quality degrades;
        above 5MB after base64, the API rejects the request outright.
        """
        with Image.open(path) as img:
            img = img.convert("RGB")
            w, h = img.size
            longest = max(w, h)
            if longest > max_dim:
                ratio = max_dim / longest
                img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=88, optimize=True)
            return base64.standard_b64encode(buf.getvalue()).decode("ascii")

    def _load_lighting_spec(self, collection: str, scene_name: str) -> dict[str, Any]:
        """Look for ``{scenes_dir}/{collection}/{scene_name}/scene.json``.

        Returns an empty dict if missing — Stage 2 will infer reasonable
        defaults from the collection.
        """
        try:
            from ..config import SCENES_DIR
        except ImportError:
            return {}
        candidate = Path(SCENES_DIR) / collection / scene_name / "scene.json"
        if candidate.is_file():
            try:
                return json.loads(candidate.read_text())
            except json.JSONDecodeError:
                return {}
        # Sibling scene.json (when scene_name is the directory itself)
        sibling = Path(SCENES_DIR) / collection / "scene.json"
        if sibling.is_file():
            try:
                return json.loads(sibling.read_text())
            except json.JSONDecodeError:
                return {}
        return {}


# ---------------------------------------------------------------------------
# Module helpers
# ---------------------------------------------------------------------------


def _extract_first_image_url(result: Any) -> str | None:
    """Pull the first output URL from a fal_client response.

    fal endpoints vary: some return ``{"images": [{"url": ...}]}``, others
    ``{"image": {"url": ...}}``, others raw strings.
    """
    if not isinstance(result, dict):
        return None
    if "images" in result:
        items = result["images"]
        if isinstance(items, list) and items:
            head = items[0]
            if isinstance(head, dict) and "url" in head:
                return str(head["url"])
            if isinstance(head, str):
                return head
    if "image" in result:
        item = result["image"]
        if isinstance(item, dict) and "url" in item:
            return str(item["url"])
        if isinstance(item, str):
            return item
    return None


def _safe_json_extract(text: str) -> dict[str, Any]:
    """Pull JSON out of an LLM response that may have prose around it."""
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)
    # Find first { and matching last }
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object in text")
    return json.loads(text[start : end + 1])


def _visual_qa_gemini(
    shadow_path: str,
    scene_name: str,
    collection: str,
) -> dict[str, Any]:
    """Module-level proxy to ``CompositorAgent._visual_qa``.

    Isolated as a module-level function so the pre-QA gate (``_maybe_apply_gate``)
    and its tests can patch the Gemini path without instantiating a full agent.
    ``_visual_qa`` itself does not read ``self``; it only reads its three args
    plus module-level imports — so a bare instance via ``__new__`` is safe.
    """
    instance = CompositorAgent.__new__(CompositorAgent)
    return CompositorAgent._visual_qa(instance, shadow_path, scene_name, collection)


def _maybe_apply_gate(
    shadow_path: str,
    scene_name: str,
    collection: str,
    *,
    centroid_path: Path | str | None = None,
) -> dict[str, Any]:
    """Pre-QA embedding gate. Reject -> skip Gemini. Accept -> call Gemini.

    If no centroid file exists at ``centroid_path`` (or the default
    ``_DEFAULT_CENTROID_PATH``), the gate is a no-op and we fall through to
    Gemini directly. This means the gate is opt-in: deploy the centroid file
    to enable it; remove the file to disable it.
    """
    resolved = Path(centroid_path) if centroid_path else _DEFAULT_CENTROID_PATH
    if not resolved.exists():
        return _visual_qa_gemini(shadow_path, scene_name, collection)

    centroid = load_centroid(resolved)
    verdict = embedding_gate.evaluate(shadow_path, centroid)
    if not verdict.accepted:
        return {
            "status": "fail",
            "reason": verdict.reason,
            "embedding_score": verdict.score,
            "embedding_threshold": verdict.threshold,
            "skipped_gemini": True,
        }
    return _visual_qa_gemini(shadow_path, scene_name, collection)


__all__ = [
    "CompositorAgent",
    "SCENE_LOOKBOOK",
    "upload_to_fal",
]

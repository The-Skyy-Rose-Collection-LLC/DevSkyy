"""CompositorAgent orchestrator — thin coordinator for the 6-stage pipeline.

## Architecture note (for next reader)

This file was split from a 1241-line monolith (agents/compositor_agent.py)
in H-03 of the elite_studio audit (2026-05-24). Each stage now lives in its
own module under agents/compositor/:

  infra.py           — shared helpers, budget gate, optional imports
  stage_a_matte.py   — BRIA alpha extraction
  stage_b_prompt.py  — Claude Opus FLUX prompt engineering
  stage_c_relight.py — IC-Light relighting (Replicate → libcom → alpha fallback)
  stage_d_flux.py    — FLUX inpainting (fal-fill → kontext → replicate) + budget gates
  stage_e_cleanup.py — GIMP pixel cleanup
  stage_f_shadows.py — PIL contact shadow
  stage_g_visual_qa.py — embedding pre-gate + Gemini visual QA
  audit.py           — JSON audit log writer
  lighting.py        — SCENE_LOOKBOOK + scene.json spec loader

Public API (CompositorAgent, SCENE_LOOKBOOK, upload_to_fal) is re-exported
from agents/compositor_agent.py, which is now a thin shim.
External callers (coordinator.py, cli.py, graph/nodes.py) require no changes.

## Mock/patch compatibility

Tests patch module-level names on the ``compositor_agent`` shim namespace:
  remove, get_anthropic_client, fal_client, httpx, analyze_vision

Methods that use those names perform a lazy ``import ...compositor_agent as _mod``
at call time and read ``_mod.<name>`` so that ``unittest.mock.patch`` intercepts
the lookup. Methods where the test patches the *class method itself* (e.g.
``CompositorAgent._flux_fill_fal``) use ``self._method()`` so the patch applies.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import httpx as _httpx
from PIL import Image, ImageFilter

from ...models import CompositorResult
from .audit import write_audit_log
from .flux_methods import FluxProviderMixin
from .infra import (
    _REMBG_UNAVAILABLE_SENTINEL,
    _b64_image_for_claude,
    _cache_dir,
    _file_hash,
    _safe_json_extract,
    _SilentLogger,
    upload_to_fal,
)
from .lighting import SCENE_LOOKBOOK, load_lighting_spec
from .stage_e_cleanup import gimp_pixel_cleanup
from .stage_f_shadows import generate_shadows

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# QA rubric (kept here so _DEFAULT_QA_RUBRIC is accessible at module level
# for the shim re-export)
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


class CompositorAgent(FluxProviderMixin):
    """6-stage scene compositor.

    Sync API; tests do not ``await`` calls. Use ``asyncio.to_thread(agent.composite, ...)``
    from async callers.

    Patch compatibility note: methods that read module-level names patched by
    tests (remove, fal_client, httpx, get_anthropic_client, analyze_vision)
    do a lazy ``import ...compositor_agent as _mod`` and read from ``_mod``
    so unittest.mock.patch intercepts the lookup correctly.
    """

    DEFAULT_OUTPUT_DIR = "renders/output/compositor"
    QA_PASS_THRESHOLD = 24  # sum of three 0-10 scores; ~8 each on average

    def __init__(
        self,
        *,
        logger: Any = None,
        config: Any = None,
    ) -> None:
        self.logger = logger or _SilentLogger()
        self._config = config  # reserved for future ADK telemetry hook

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
        budget: Any = None,
    ) -> CompositorResult:
        """Run the 6-stage compositing pipeline."""
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

            # Rasterize mode does NOT use Stage 2's FLUX prompt or Stage 3's
            # IC-Light relit subject — Stage D rasterize composites the
            # verified mockup directly onto the scene. Skip them in rasterize
            # mode to avoid the wasted paid calls (Anthropic + Replicate) and
            # to drop the auth requirements on those services for the
            # deterministic path.
            _rasterize_mode = os.environ.get("ELITE_STUDIO_STAGE_D_MODE", "kontext") == "rasterize"

            # ------------------------------ Stage 2: prompt synth
            if _rasterize_mode:
                prompt = ""
                stages["prompt"] = {"skipped": True, "reason": "rasterize-mode"}
            elif resume_from and resume_from > 2:
                prompt = checkpoint_prompt or ""
                if not prompt:
                    raise RuntimeError(f"resume_from={resume_from} requires checkpoint_prompt")
                stages["prompt"] = {"resumed": True, "chars": len(prompt)}
            else:
                started = time.perf_counter()
                lighting_spec = self._load_lighting_spec(collection, scene_name)
                scene_b64 = _b64_image_for_claude(scene_image_path)
                subject_b64 = _b64_image_for_claude(alpha_path)
                prompt = self._engineer_flux_prompt(
                    scene_b64=scene_b64,
                    subject_b64=subject_b64,
                    collection=collection,
                    scene_name=scene_name,
                    lighting_spec=lighting_spec,
                )
                stages["prompt"] = {
                    "chars": len(prompt),
                    "duration_s": round(time.perf_counter() - started, 3),
                }
                stages_done = 2

            # ------------------------------ Stage 3: relight
            if _rasterize_mode:
                # Rasterize composites the mockup directly; no relit subject
                # is consumed downstream. Set relit_path = alpha_path so any
                # downstream reference remains well-typed.
                relit_path = alpha_path
                stages["relight"] = {"skipped": True, "reason": "rasterize-mode"}
            elif resume_from and resume_from > 3:
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

            # ------------------------------ Stage 4: composite
            # Branch on ELITE_STUDIO_STAGE_D_MODE:
            #   "kontext"   (default) — FLUX inpainting via fal/replicate
            #   "rasterize"           — deterministic PIL alpha-composite
            # Rasterize uses model_image_path directly as the verified mockup
            # (per-SKU golden photo). No paid API. See
            # docs/superpowers/specs/2026-05-27-mockup-stage-d-and-cost-ceiling-design.md
            started = time.perf_counter()
            stage_d_mode = os.environ.get("ELITE_STUDIO_STAGE_D_MODE", "kontext")

            if stage_d_mode == "rasterize":
                from .stage_d_rasterize import align_mask_to_scene, rasterize_composite

                # BRIA matte is cutout-sized; scene is scene-sized. Resize the
                # mask onto the scene canvas first so rasterize's size-equality
                # check passes (see stage_d_rasterize:86-90).
                aligned_mask_path = align_mask_to_scene(
                    alpha_path=alpha_path,
                    scene_image_path=scene_image_path,
                    sku=sku,
                    output_dir=str(out),
                )
                composite_path = rasterize_composite(
                    mockup_path=model_image_path,
                    scene_image_path=scene_image_path,
                    aligned_mask_path=aligned_mask_path,
                    sku=sku,
                    output_dir=str(out),
                )
                provider = "rasterize-pil"
                stages["composite"] = {
                    "path": composite_path,
                    "provider": provider,
                    "mode": "rasterize",
                    "aligned_mask_path": aligned_mask_path,
                    "duration_s": round(time.perf_counter() - started, 3),
                }
                stages_done = 4
                result_kwargs["provider"] = provider
                result_kwargs["model"] = "deterministic-pil-rasterize"
            else:
                with ThreadPoolExecutor(max_workers=3) as pool:
                    scene_fut = pool.submit(upload_to_fal, scene_image_path)
                    subject_fut = pool.submit(upload_to_fal, relit_path)
                    mask_fut = pool.submit(upload_to_fal, alpha_path)
                    scene_url = scene_fut.result()
                    subject_url = subject_fut.result()
                    mask_url = mask_fut.result()
                composite_bytes, provider = self._composite_with_flux(
                    scene_url=scene_url,
                    subject_url=subject_url,
                    mask_url=mask_url,
                    prompt=prompt,
                    budget=budget,
                )
                composite_path = str(out / f"{sku}-composite.png")
                Path(composite_path).write_bytes(composite_bytes)
                stages["composite"] = {
                    "path": composite_path,
                    "provider": provider,
                    "mode": "kontext",
                    "duration_s": round(time.perf_counter() - started, 3),
                }
                stages_done = 4
                result_kwargs["provider"] = provider
                result_kwargs["model"] = "flux-fill-pro" if provider == "fal-fill" else provider
                if provider != "fal-fill":
                    result_kwargs["used_fallback"] = True
                    result_kwargs["fallback_provider"] = provider

            # ------------------------------ Stage 4.5: GIMP pixel cleanup
            started = time.perf_counter()
            composite_path = self._gimp_pixel_cleanup(composite_path, sku, str(out))
            stages["gimp_cleanup"] = {
                "path": composite_path,
                "duration_s": round(time.perf_counter() - started, 3),
            }

            # ------------------------------ Stage 5: shadows
            started = time.perf_counter()
            shadow_path = self._generate_shadows(composite_path, sku, str(out))
            stages["shadow"] = {
                "path": shadow_path,
                "duration_s": round(time.perf_counter() - started, 3),
            }
            stages_done = 5

            # ---------------------- Stage 5.5/6: pre-QA gate + Gemini QA
            started = time.perf_counter()
            qa = self._maybe_apply_gate(shadow_path, scene_name, collection)
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

        Reads ``remove`` and ``_matte_via_fal`` from the compositor_agent shim
        namespace so tests can patch them at that location.
        """
        import skyyrose.elite_studio.agents.compositor_agent as _mod

        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        with open(model_image_path, "rb") as f:
            input_bytes = f.read()
        input_hash = hashlib.sha256(input_bytes).hexdigest()[:16]

        try:
            result: Any = _mod.remove(input_bytes)
        except RuntimeError as exc:
            if _REMBG_UNAVAILABLE_SENTINEL not in str(exc):
                raise
            logger.info("Local rembg unavailable; using FAL hosted BRIA endpoint")
            result = _mod._matte_via_fal(input_bytes)

        if isinstance(result, (bytes, bytearray)):
            img = Image.open(io.BytesIO(result)).convert("RGBA")
        elif isinstance(result, Image.Image):
            img = result.convert("RGBA")
        else:  # pragma: no cover
            raise RuntimeError(f"unexpected rembg return type: {type(result).__name__}")

        r, g, b, a = img.split()
        a = a.filter(ImageFilter.GaussianBlur(radius=1.0))
        img = Image.merge("RGBA", (r, g, b, a))

        dest = out / f"{sku}-alpha.png"
        img.save(dest, format="PNG")
        try:
            cache = _cache_dir("matte")
            cached = cache / f"{input_hash}.png"
            if not cached.exists():
                img.save(cached, format="PNG")
        except Exception:  # pragma: no cover
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
        """Use Claude Opus to write a FLUX prompt.

        Reads ``get_anthropic_client`` from the compositor_agent shim namespace
        so tests can patch it at that location.
        """
        import skyyrose.elite_studio.agents.compositor_agent as _mod

        from ...config import COMPOSITOR_OPUS_MODEL

        client = _mod.get_anthropic_client()
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
        """Match subject lighting to scene via IC-Light."""
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

        return alpha_path

    def _run_iclight_replicate(
        self,
        *,
        alpha_path: str,
        scene_path: str,
        prompt: str,
    ) -> bytes | None:
        """Replicate IC-Light v2 — preferred relighting path."""
        token = os.environ.get("REPLICATE_API_TOKEN")
        if not token:  # pragma: no cover
            return None
        try:
            with _httpx.Client(timeout=120.0) as client:
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
        """Local libcom relighting path."""
        try:
            from libcom import ImageHarmonizationModel  # type: ignore[import-not-found]
        except ImportError:
            return None
        try:
            harmonizer = ImageHarmonizationModel(device="cpu", model_type="PCTNet")  # type: ignore[arg-type]
            with Image.open(alpha_path).convert("RGBA") as subject:
                mask = subject.split()[-1]
                mask_path = Path(alpha_path).with_suffix(".mask.png")
                mask.save(mask_path)
                rgb_path = Path(alpha_path).with_suffix(".rgb.jpg")
                subject.convert("RGB").save(rgb_path, format="JPEG", quality=95)
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

    # ------------------------------------------------- Stage 4.5: GIMP cleanup

    def _gimp_pixel_cleanup(self, composite_path: str, sku: str, output_dir: str) -> str:
        return gimp_pixel_cleanup(composite_path, sku, output_dir)

    # --------------------------------------------------- Stage 5: shadows

    def _generate_shadows(self, composite_path: str, sku: str, output_dir: str) -> str:
        return generate_shadows(composite_path, sku, output_dir)

    # --------------------------------------------------- Stage 6: visual QA

    def _visual_qa(
        self,
        composite_path: str,
        scene_name: str,
        collection: str,
    ) -> dict[str, Any]:
        """Score the composite via Gemini.

        Reads ``analyze_vision`` from the compositor_agent shim namespace so
        tests can patch it at that location.
        """
        import skyyrose.elite_studio.agents.compositor_agent as _mod

        from ...config import COMPOSITOR_QA_MODEL

        with open(composite_path, "rb") as f:
            b64 = base64.standard_b64encode(f.read()).decode("ascii")
        ext = Path(composite_path).suffix.lower().lstrip(".")
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"

        rubric = _DEFAULT_QA_RUBRIC.format(
            scene_name=scene_name,
            collection=collection,
        )
        result = _mod.analyze_vision(
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

    def _maybe_apply_gate(
        self,
        shadow_path: str,
        scene_name: str,
        collection: str,
        *,
        centroid_path: Path | str | None = None,
    ) -> dict[str, Any]:
        """Pre-QA embedding gate; falls through to Gemini QA if no centroid."""
        from ...quality import embedding_gate
        from ...quality.brand_centroid import load_centroid

        default_centroid = Path(__file__).resolve().parents[2] / "data" / "brand_centroid.npz"
        resolved = Path(centroid_path) if centroid_path else default_centroid
        if not resolved.exists():
            return self._visual_qa_gemini(shadow_path, scene_name, collection)

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
        return self._visual_qa_gemini(shadow_path, scene_name, collection)

    def _visual_qa_gemini(
        self,
        shadow_path: str,
        scene_name: str,
        collection: str,
    ) -> dict[str, Any]:
        """Proxy to _visual_qa for the pre-QA gate."""
        return self._visual_qa(shadow_path, scene_name, collection)

    # ---------------------------------------------------- audit log

    def _write_audit_log(
        self,
        sku: str,
        scene_name: str,
        stages: dict[str, Any],
        result: CompositorResult,
        output_dir: str,
    ) -> str:
        return write_audit_log(sku, scene_name, stages, result, output_dir)

    # ------------------------------------------------------- helpers

    @staticmethod
    def _b64_image(path: str) -> str:
        from .infra import _b64_image

        return _b64_image(path)

    @staticmethod
    def _b64_image_for_claude(path: str, *, max_dim: int = 1568) -> str:
        return _b64_image_for_claude(path, max_dim=max_dim)

    def _load_lighting_spec(self, collection: str, scene_name: str) -> dict[str, Any]:
        return load_lighting_spec(collection, scene_name)


# ---------------------------------------------------------------------------
# Module-level proxies (preserved for callers that import them directly)
# ---------------------------------------------------------------------------


def _visual_qa_gemini_proxy(
    shadow_path: str,
    scene_name: str,
    collection: str,
) -> dict[str, Any]:
    """Module-level proxy to CompositorAgent._visual_qa.

    Isolated so the pre-QA gate and its tests can patch the Gemini path
    without instantiating a full agent.
    """
    instance = CompositorAgent.__new__(CompositorAgent)
    return CompositorAgent._visual_qa(instance, shadow_path, scene_name, collection)


def _maybe_apply_gate_proxy(
    shadow_path: str,
    scene_name: str,
    collection: str,
    *,
    centroid_path: Path | str | None = None,
) -> dict[str, Any]:
    """Module-level proxy to CompositorAgent._maybe_apply_gate."""
    instance = CompositorAgent.__new__(CompositorAgent)
    return CompositorAgent._maybe_apply_gate(
        instance,
        shadow_path,
        scene_name,
        collection,
        centroid_path=centroid_path,
    )


__all__ = [
    "CompositorAgent",
    "SCENE_LOOKBOOK",
    "upload_to_fal",
]

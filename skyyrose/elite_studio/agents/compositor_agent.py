"""
Compositor Agent — Immersive Scene Compositing (Step 4)

Places generated fashion models INTO immersive collection scenes.
Uses Opus as brain (prompt engineering) and FLUX/BRIA as hands (image gen).

6-Stage Pipeline:
    1. BRIA RMBG 2.0   -> alpha matte extraction
    2. Claude Opus      -> FLUX prompt engineering
    3. IC-Light         -> background-conditioned relighting
    4. FLUX Fill/Kontext -> inpaints subject into scene (fallback chain)
    5. GPSDiffusion     -> contact shadows (fallback: PIL gaussian)
    6. Gemini Pro       -> visual QA (pass/warn/fail)
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Protocol

import httpx

from ..config import (
    COMPOSITOR_OPUS_MODEL,
    COMPOSITOR_QA_MODEL,
    COMPOSITOR_STAGE_DELAY,
    get_anthropic_client,
)
from ..gemini_rest import analyze_vision
from ..models import CompositorResult
from ..utils import image_to_base64, upload_to_fal

try:
    import fal_client
except ImportError:
    fal_client = None  # type: ignore[assignment]

try:
    from rembg import remove
except ImportError:
    remove = None  # type: ignore[assignment]

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Product-to-Scene Mapping
# ---------------------------------------------------------------------------

SCENE_LOOKBOOK: dict[str, dict[str, str]] = {
    "black-rose-rooftop-garden": {
        "br-001": "br-001-render-branding.webp",
        "br-002": "br-002-front-model.webp",
        "br-004": "br-004-render-branding.webp",
        "br-006": "lookbook",
    },
    "love-hurts-cathedral-rose-chamber": {
        "lh-001": "lh-001-model-m.webp",
        "lh-003": "lookbook",
        "lh-005": "lh-005-composite-front.webp",
    },
    "signature-golden-gate-showroom": {
        "sg-005": "lookbook",
        "sg-007": "sg-007-front-model.webp",
        "sg-011": "lookbook",
        "sg-012": "sg-012-composite-front.webp",
    },
}


class Logger(Protocol):
    def info(self, msg: str) -> None: ...
    def step(self, step_num: int, total: int, label: str) -> None: ...
    def ok(self, msg: str) -> None: ...
    def fail(self, msg: str) -> None: ...
    def separator(self) -> None: ...


class CompositorAgent:
    """Scene compositor using Opus brain + FLUX hands.

    Opus engineers prompts, FLUX executes compositing,
    Gemini verifies quality.
    """

    def __init__(self, logger: Logger | None = None):
        from ..coordinator import PrintLogger

        self.log = logger or PrintLogger()

    # -----------------------------------------------------------------------
    # Main entry point
    # -----------------------------------------------------------------------

    def composite(
        self,
        sku: str,
        scene_image_path: str,
        model_image_path: str,
        collection: str,
        scene_name: str,
        output_dir: str = "",
        resume_from: int = 0,
        checkpoint_alpha: str = "",
        checkpoint_relit: str = "",
        checkpoint_prompt: str = "",
    ) -> CompositorResult:
        """Run 6-stage compositing pipeline.

        Args:
            sku: Product SKU (e.g., "br-001")
            scene_image_path: Path to scene background image
            model_image_path: Path to model/product image
            collection: Collection name (e.g., "black-rose")
            scene_name: Scene identifier (e.g., "black-rose-rooftop-garden")
            output_dir: Output directory (auto-created)
            resume_from: Resume from this stage number (1-6, 0=start fresh)
            checkpoint_alpha: Pre-computed alpha matte path (for resume)
            checkpoint_relit: Pre-computed relit image path (for resume)
            checkpoint_prompt: Pre-computed FLUX prompt (for resume)

        Returns:
            CompositorResult with success/failure and output path.
        """
        self.log.separator()
        self.log.info(f"COMPOSITOR — {sku.upper()} | {scene_name}")
        self.log.separator()

        out = Path(output_dir or f"editorial-staging/{collection}")
        out.mkdir(parents=True, exist_ok=True)
        work = out / f".work-{sku}-{scene_name}"
        work.mkdir(parents=True, exist_ok=True)

        stages: dict[str, Any] = {}
        alpha_path = checkpoint_alpha
        relit_path = checkpoint_relit
        flux_prompt = checkpoint_prompt
        stages_completed = 0
        used_fallback = False
        fallback_provider = ""
        provider = ""

        try:
            # ── Stage 1: Alpha Matte ──────────────────────────────────
            if resume_from < 2:
                self.log.step(1, 6, "Alpha Matte Extraction (BRIA RMBG 2.0)")
                t0 = time.time()
                alpha_path = self._extract_alpha(model_image_path, sku, str(work))
                stages["alpha"] = {
                    "path": alpha_path,
                    "duration_s": round(time.time() - t0, 2),
                }
                stages_completed = 1
                self.log.ok(f"Alpha: {alpha_path}")
                time.sleep(COMPOSITOR_STAGE_DELAY)

            # ── Stage 2: Opus Prompt Engineering ──────────────────────
            if resume_from < 3:
                self.log.step(2, 6, "Opus Prompt Engineering")
                t0 = time.time()
                scene_b64 = image_to_base64(scene_image_path)
                subject_b64 = image_to_base64(alpha_path)
                lighting_spec = self._load_scene_spec(scene_image_path)

                flux_prompt = self._engineer_flux_prompt(
                    scene_b64, subject_b64, collection, scene_name, lighting_spec
                )
                stages["prompt"] = {
                    "model": COMPOSITOR_OPUS_MODEL,
                    "prompt_length": len(flux_prompt),
                    "duration_s": round(time.time() - t0, 2),
                }
                stages_completed = 2
                self.log.ok(f"Prompt: {len(flux_prompt)} chars")
                time.sleep(COMPOSITOR_STAGE_DELAY)

            # ── Stage 3: IC-Light Relighting ──────────────────────────
            if resume_from < 4:
                self.log.step(3, 6, "IC-Light Relighting")
                t0 = time.time()
                relit_path = self._relight_subject(
                    alpha_path, scene_image_path, flux_prompt, sku, str(work)
                )
                stages["relight"] = {
                    "path": relit_path,
                    "duration_s": round(time.time() - t0, 2),
                }
                stages_completed = 3
                self.log.ok(f"Relit: {relit_path}")
                time.sleep(COMPOSITOR_STAGE_DELAY)

            # ── Stage 4: FLUX Compositing ─────────────────────────────
            self.log.step(4, 6, "FLUX Compositing")
            t0 = time.time()

            # Upload assets to CDN (try fal, fall back to data URIs for Replicate)
            try:
                scene_url = upload_to_fal(Path(scene_image_path).read_bytes(), f"{sku}-scene.png")
                subject_url = upload_to_fal(Path(relit_path).read_bytes(), f"{sku}-relit.png")
                mask_url = upload_to_fal(
                    self._create_scene_mask(alpha_path, scene_image_path),
                    f"{sku}-mask.png",
                )
            except Exception as exc:
                import base64 as b64

                def _to_data_uri(data: bytes) -> str:
                    return "data:image/png;base64," + b64.b64encode(data).decode()

                log.info("fal CDN unavailable, using data URIs: %s", exc)
                scene_url = _to_data_uri(Path(scene_image_path).read_bytes())
                subject_url = _to_data_uri(Path(relit_path).read_bytes())
                mask_url = _to_data_uri(self._create_scene_mask(alpha_path, scene_image_path))

            composite_bytes, provider = self._composite_with_flux(
                scene_url, subject_url, mask_url, flux_prompt
            )

            # Save composite
            composite_path = str(work / f"{sku}-composite-{scene_name}.png")
            Path(composite_path).write_bytes(composite_bytes)

            if provider != "fal-fill":
                used_fallback = True
                fallback_provider = provider

            stages["flux"] = {
                "provider": provider,
                "used_fallback": used_fallback,
                "duration_s": round(time.time() - t0, 2),
            }
            stages_completed = 4
            self.log.ok(f"Composite: {provider}")
            time.sleep(COMPOSITOR_STAGE_DELAY)

            # ── Stage 5: Shadow Generation ────────────────────────────
            self.log.step(5, 6, "Shadow Generation")
            t0 = time.time()
            final_path = self._generate_shadows(composite_path, sku, str(work))
            stages["shadows"] = {
                "path": final_path,
                "duration_s": round(time.time() - t0, 2),
            }
            stages_completed = 5
            self.log.ok(f"Shadows: {final_path}")
            time.sleep(COMPOSITOR_STAGE_DELAY)

            # ── Stage 6: Visual QA ────────────────────────────────────
            self.log.step(6, 6, "Visual QA (Gemini)")
            t0 = time.time()
            qa = self._visual_qa(final_path, scene_name, collection)
            stages["qa"] = {
                "status": qa.get("status", "unknown"),
                "duration_s": round(time.time() - t0, 2),
                **qa,
            }
            stages_completed = 6
            self.log.ok(f"QA: {qa.get('status', 'unknown')}")

            # ── Save final output ─────────────────────────────────────
            output_path = str(out / f"{sku}-final-{scene_name}.jpg")
            self._save_final(final_path, output_path)

            # ── Audit log ─────────────────────────────────────────────
            result = CompositorResult(
                success=True,
                provider=provider,
                model="flux-fill-pro" if provider == "fal-fill" else provider,
                scene_name=scene_name,
                collection=collection,
                output_path=output_path,
                alpha_path=alpha_path,
                qa_status=qa.get("status", "unknown"),
                qa_details=qa,
                stages_completed=stages_completed,
                used_fallback=used_fallback,
                fallback_provider=fallback_provider,
            )

            audit_path = self._write_audit_log(sku, scene_name, stages, result, str(out))

            self.log.separator()
            self.log.info(f"COMPLETE: {sku.upper()} → {output_path}")
            self.log.separator()

            return CompositorResult(
                success=True,
                provider=provider,
                model="flux-fill-pro" if provider == "fal-fill" else provider,
                scene_name=scene_name,
                collection=collection,
                output_path=output_path,
                alpha_path=alpha_path,
                qa_status=qa.get("status", "unknown"),
                qa_details=qa,
                stages_completed=stages_completed,
                audit_log_path=audit_path,
                used_fallback=used_fallback,
                fallback_provider=fallback_provider,
            )

        except Exception as exc:
            self.log.fail(f"Stage {stages_completed + 1} failed: {exc}")
            return CompositorResult(
                success=False,
                error=str(exc),
                scene_name=scene_name,
                collection=collection,
                stages_completed=stages_completed,
                used_fallback=used_fallback,
                fallback_provider=fallback_provider,
            )

    # -----------------------------------------------------------------------
    # Stage 1: Alpha Matte Extraction
    # -----------------------------------------------------------------------

    def _extract_alpha(self, model_image_path: str, sku: str, work_dir: str) -> str:
        """BRIA RMBG 2.0 via rembg — extract alpha matte from subject."""
        from PIL import Image

        if remove is None:
            raise RuntimeError("rembg not installed — run: pip install rembg")

        img = Image.open(model_image_path)
        result = remove(img)

        alpha_path = str(Path(work_dir) / f"{sku}-alpha.png")
        result.save(alpha_path, format="PNG")
        return alpha_path

    # -----------------------------------------------------------------------
    # Stage 2: Opus Prompt Engineering
    # -----------------------------------------------------------------------

    def _engineer_flux_prompt(
        self,
        scene_b64: str,
        subject_b64: str,
        collection: str,
        scene_name: str,
        lighting_spec: dict,
    ) -> str:
        """Opus analyzes scene + subject and crafts a FLUX compositing prompt."""
        client = get_anthropic_client()

        spec_text = json.dumps(lighting_spec) if lighting_spec else "No spec available"

        response = client.messages.create(
            model=COMPOSITOR_OPUS_MODEL,
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": scene_b64,
                            },
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": subject_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                f"You are a scene compositor for luxury fashion brand SkyyRose.\n\n"
                                f"SCENE: {scene_name} (collection: {collection})\n"
                                f"LIGHTING SPEC: {spec_text}\n\n"
                                f"Image 1 is the SCENE BACKGROUND.\n"
                                f"Image 2 is the SUBJECT (fashion model with alpha matte).\n\n"
                                f"Write a FLUX inpainting prompt that composites the subject "
                                f"INTO the scene. The prompt must:\n"
                                f"1. Match the scene's lighting direction, color temperature, and mood\n"
                                f"2. Place the subject naturally (correct scale, perspective, grounding)\n"
                                f"3. Preserve all garment details, logos, and branding\n"
                                f"4. Describe realistic shadow and reflection interactions\n\n"
                                f"Return ONLY the prompt text, no explanations."
                            ),
                        },
                    ],
                }
            ],
        )

        return response.content[0].text.strip()

    # -----------------------------------------------------------------------
    # Stage 3: IC-Light Relighting
    # -----------------------------------------------------------------------

    def _relight_subject(
        self,
        alpha_path: str,
        scene_path: str,
        prompt: str,
        sku: str,
        work_dir: str,
    ) -> str:
        """IC-Light background-conditioned relighting.

        Falls back to using the alpha-matted image directly if IC-Light
        is unavailable or fails.
        """
        # Try cloud IC-Light (Replicate) first, then local, then fallback
        for method_name, method in [
            ("replicate", self._run_iclight_replicate),
            ("local", self._run_iclight),
        ]:
            try:
                relit_bytes = method(alpha_path, scene_path, prompt)
                relit_path = str(Path(work_dir) / f"{sku}-relit.png")
                Path(relit_path).write_bytes(relit_bytes)
                return relit_path
            except Exception as exc:
                log.warning("IC-Light %s failed: %s", method_name, exc)

        log.warning("All IC-Light methods failed — using alpha directly")
        return alpha_path

    def _run_iclight_replicate(self, alpha_path: str, scene_path: str, prompt: str) -> bytes:
        """IC-Light via Replicate cloud API (A100 GPU)."""
        import replicate

        fg_data = Path(alpha_path).read_bytes()
        bg_data = Path(scene_path).read_bytes()

        output = replicate.run(
            "zsxkib/ic-light",
            input={
                "prompt": prompt,
                "light_source": "None",
                "foreground_image": fg_data,
                "background_image": bg_data,
                "num_inference_steps": 25,
                "guidance_scale": 2.0,
            },
        )
        # output is a URL or list of URLs
        url = output[0] if isinstance(output, list) else output
        resp = httpx.get(str(url), timeout=60)
        resp.raise_for_status()
        return resp.content

    def _run_iclight(self, alpha_path: str, scene_path: str, prompt: str) -> bytes:
        """Run IC-Light FBC pipeline (lllyasviel/IC-Light).

        Background-conditioned relighting: takes foreground (alpha-matted subject)
        + background (scene) and relights the foreground to match.

        Uses SD1.5 UNet with conv_in expanded to 12 channels:
          4 (noised latent) + 4 (foreground latent) + 4 (background latent)

        Returns PNG bytes of the relit image.
        """
        import io

        import numpy as np
        import safetensors.torch as sf
        import torch
        from diffusers import (
            AutoencoderKL,
            EulerAncestralDiscreteScheduler,
            StableDiffusionPipeline,
            UNet2DConditionModel,
        )
        from diffusers.models.attention_processor import AttnProcessor2_0
        from PIL import Image
        from transformers import CLIPTextModel, CLIPTokenizer

        from ..config import (
            ICLIGHT_BASE_MODEL,
            ICLIGHT_CFG,
            ICLIGHT_RESOLUTION,
            ICLIGHT_STEPS,
            ICLIGHT_WEIGHTS_PATH,
        )

        if not ICLIGHT_WEIGHTS_PATH.exists():
            raise FileNotFoundError(
                f"IC-Light weights not found: {ICLIGHT_WEIGHTS_PATH}\n"
                "Download from: huggingface.co/lllyasviel/ic-light"
            )

        # Determine device
        if torch.backends.mps.is_available():
            device = torch.device("mps")
            dtype = torch.float16
        elif torch.cuda.is_available():
            device = torch.device("cuda")
            dtype = torch.float16
        else:
            device = torch.device("cpu")
            dtype = torch.float32

        res = ICLIGHT_RESOLUTION

        # Load base SD1.5 components
        tokenizer = CLIPTokenizer.from_pretrained(ICLIGHT_BASE_MODEL, subfolder="tokenizer")
        text_encoder = CLIPTextModel.from_pretrained(ICLIGHT_BASE_MODEL, subfolder="text_encoder")
        vae = AutoencoderKL.from_pretrained(ICLIGHT_BASE_MODEL, subfolder="vae")
        unet = UNet2DConditionModel.from_pretrained(ICLIGHT_BASE_MODEL, subfolder="unet")
        scheduler = EulerAncestralDiscreteScheduler.from_pretrained(
            ICLIGHT_BASE_MODEL, subfolder="scheduler"
        )

        # Expand conv_in from 4 to 12 channels for FBC conditioning
        with torch.no_grad():
            new_conv_in = torch.nn.Conv2d(
                12,
                unet.conv_in.out_channels,
                unet.conv_in.kernel_size,
                unet.conv_in.stride,
                unet.conv_in.padding,
            )
            new_conv_in.weight.zero_()
            new_conv_in.weight[:, :4, :, :].copy_(unet.conv_in.weight)
            new_conv_in.bias = unet.conv_in.bias
            unet.conv_in = new_conv_in

        # Load IC-Light FBC weights
        sd_offset = sf.load_file(str(ICLIGHT_WEIGHTS_PATH))
        unet.load_state_dict(sd_offset, strict=False)
        unet.set_attn_processor(AttnProcessor2_0())

        # Move to device
        text_encoder.to(device=device, dtype=dtype)
        vae.to(device=device, dtype=dtype)
        unet.to(device=device, dtype=dtype)

        # Hook UNet forward to inject fg+bg conditioning
        unet_original_forward = unet.forward

        def hooked_unet_forward(sample, timestep, encoder_hidden_states, **kwargs):
            c_concat = kwargs["cross_attention_kwargs"]["concat_conds"].to(sample)
            c_concat = torch.cat([c_concat] * (sample.shape[0] // c_concat.shape[0]), dim=0)
            new_sample = torch.cat([sample, c_concat], dim=1)
            kwargs["cross_attention_kwargs"] = {}
            return unet_original_forward(new_sample, timestep, encoder_hidden_states, **kwargs)

        unet.forward = hooked_unet_forward

        # Build pipeline
        pipe = StableDiffusionPipeline(
            vae=vae,
            text_encoder=text_encoder,
            tokenizer=tokenizer,
            unet=unet,
            scheduler=scheduler,
            safety_checker=None,
            requires_safety_checker=False,
            feature_extractor=None,
            image_encoder=None,
        )

        # Prepare images
        def _load_and_resize(path: str, size: int) -> np.ndarray:
            img = Image.open(path).convert("RGB")
            img = img.resize((size, size), Image.Resampling.LANCZOS)
            return np.array(img)

        fg = _load_and_resize(alpha_path, res)
        bg = _load_and_resize(scene_path, res)

        # Encode fg and bg through VAE
        imgs_np = np.stack([fg, bg], axis=0).astype(np.float32) / 127.5 - 1.0
        imgs_t = torch.from_numpy(imgs_np).permute(0, 3, 1, 2).to(device=device, dtype=dtype)
        concat_conds = vae.encode(imgs_t).latent_dist.mode() * vae.config.scaling_factor
        concat_conds = concat_conds.unsqueeze(0).reshape(1, -1, *concat_conds.shape[2:])

        # Encode prompt
        text_input = tokenizer(
            prompt, padding="max_length", max_length=77, truncation=True, return_tensors="pt"
        )
        conds = text_encoder(text_input.input_ids.to(device))[0]
        uncond_input = tokenizer("", padding="max_length", max_length=77, return_tensors="pt")
        unconds = text_encoder(uncond_input.input_ids.to(device))[0]

        # Generate
        rng = torch.Generator(device="cpu").manual_seed(42)
        latents = pipe(
            prompt_embeds=conds,
            negative_prompt_embeds=unconds,
            width=res,
            height=res,
            num_inference_steps=ICLIGHT_STEPS,
            num_images_per_prompt=1,
            generator=rng,
            output_type="latent",
            guidance_scale=ICLIGHT_CFG,
            cross_attention_kwargs={"concat_conds": concat_conds},
        ).images

        # Decode
        pixels = vae.decode(latents / vae.config.scaling_factor).sample
        pixels = (pixels.clamp(-1, 1) + 1) / 2 * 255
        pixels = pixels[0].permute(1, 2, 0).cpu().numpy().astype(np.uint8)

        result_img = Image.fromarray(pixels)
        buf = io.BytesIO()
        result_img.save(buf, format="PNG")
        return buf.getvalue()

    # -----------------------------------------------------------------------
    # Stage 4: FLUX Compositing (smart routing with fallback)
    # -----------------------------------------------------------------------

    def _composite_with_flux(
        self,
        scene_url: str,
        subject_url: str,
        mask_url: str,
        prompt: str,
    ) -> tuple[bytes, str]:
        """Try FLUX providers in order: fal Fill -> Kontext -> Replicate.

        Returns (image_bytes, provider_name).
        Raises RuntimeError if all providers fail.
        """
        # Try fal FLUX Fill Pro
        result = self._flux_fill_fal(scene_url, mask_url, prompt)
        if result:
            return result, "fal-fill"

        # Try fal FLUX Kontext (reference-guided)
        result = self._flux_kontext(scene_url, mask_url, subject_url, prompt)
        if result:
            return result, "kontext"

        # Try Replicate FLUX Fill Pro
        result = self._flux_fill_replicate(scene_url, mask_url, prompt)
        if result:
            return result, "replicate"

        raise RuntimeError("All FLUX providers failed for compositing")

    def _flux_fill_fal(self, scene_url: str, mask_url: str, prompt: str) -> bytes | None:
        """fal FLUX Fill Pro — primary compositing provider."""
        if fal_client is None:
            return None

        try:
            result = fal_client.run(
                "fal-ai/flux-pro/v1/fill",
                arguments={
                    "image_url": scene_url,
                    "mask_url": mask_url,
                    "prompt": prompt,
                    "output_format": "png",
                    "num_images": 1,
                },
            )
            if result and "images" in result and result["images"]:
                img_url = result["images"][0]["url"]
                resp = httpx.get(img_url, timeout=30)
                resp.raise_for_status()
                return resp.content
        except Exception as exc:
            log.warning("fal Fill failed: %s", exc)
        return None

    def _flux_kontext(
        self, scene_url: str, mask_url: str, ref_url: str, prompt: str
    ) -> bytes | None:
        """fal FLUX Kontext — reference-guided inpainting fallback."""
        if fal_client is None:
            return None

        try:
            result = fal_client.run(
                "fal-ai/flux-kontext-lora/inpaint",
                arguments={
                    "image_url": scene_url,
                    "mask_url": mask_url,
                    "reference_image_url": ref_url,
                    "prompt": prompt,
                    "num_inference_steps": 35,
                    "guidance_scale": 3.0,
                    "strength": 0.85,
                    "output_format": "png",
                    "num_images": 1,
                },
            )
            if result and "images" in result and result["images"]:
                img_url = result["images"][0]["url"]
                resp = httpx.get(img_url, timeout=30)
                resp.raise_for_status()
                return resp.content
        except Exception as exc:
            log.warning("Kontext failed: %s", exc)
        return None

    def _flux_fill_replicate(self, scene_url: str, mask_url: str, prompt: str) -> bytes | None:
        """Replicate FLUX Fill Pro via HTTP API — final fallback."""
        token = os.environ.get("REPLICATE_API_TOKEN", "")
        if not token:
            log.warning("Replicate skipped: no REPLICATE_API_TOKEN")
            return None

        try:
            resp = httpx.post(
                "https://api.replicate.com/v1/models/black-forest-labs/flux-fill-pro/predictions",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Prefer": "wait",
                },
                json={
                    "input": {
                        "image": scene_url,
                        "mask": mask_url,
                        "prompt": prompt,
                    },
                },
                timeout=120,
            )
            if not resp.is_success:
                log.warning("Replicate failed (%d): %s", resp.status_code, resp.text[:300])
                return None

            prediction = resp.json()
            poll_url = prediction.get("urls", {}).get("get", "")
            if not poll_url:
                return None

            for _ in range(60):
                time.sleep(5)
                poll_resp = httpx.get(
                    poll_url,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=15,
                )
                poll_resp.raise_for_status()
                status = poll_resp.json()

                if status["status"] == "succeeded":
                    output = status.get("output")
                    if isinstance(output, list) and output:
                        output = output[0]
                    if isinstance(output, str) and output.startswith("http"):
                        img_resp = httpx.get(output, timeout=30)
                        img_resp.raise_for_status()
                        return img_resp.content
                    return None
                elif status["status"] == "failed":
                    log.warning("Replicate failed: %s", status.get("error", "unknown"))
                    return None

            log.warning("Replicate timed out")
        except Exception as exc:
            log.warning("Replicate failed: %s", exc)
        return None

    # -----------------------------------------------------------------------
    # Stage 5: Shadow Generation
    # -----------------------------------------------------------------------

    def _generate_shadows(self, composite_path: str, sku: str, work_dir: str) -> str:
        """Generate contact shadows.

        Tries GPSDiffusion (libcom) first, falls back to PIL gaussian shadow.
        """
        try:
            return self._gpsdiffusion_shadows(composite_path, sku, work_dir)
        except Exception:
            return self._pil_soft_shadow(composite_path, sku, work_dir)

    def _gpsdiffusion_shadows(self, composite_path: str, sku: str, work_dir: str) -> str:
        """GPSDiffusion from libcom — CVPR 2025 contact shadow generation.

        Requires: pip install libcom (Linux + CUDA only).
        """
        import cv2
        import numpy as np
        from libcom.shadow_generation import ShadowGenerationModel
        from PIL import Image

        net = ShadowGenerationModel(device=0)
        img = Image.open(composite_path)
        if img.mode != "RGBA":
            raise ValueError("Need RGBA image for shadow generation")

        alpha = np.array(img.split()[-1])
        mask = (alpha > 128).astype(np.uint8) * 255
        mask_path = str(Path(work_dir) / f"{sku}-shadow-mask.png")
        cv2.imwrite(mask_path, mask)

        results = net(composite_path, mask_path, number=3)
        if results:
            shadow_path = str(Path(work_dir) / f"{sku}-shadow.png")
            cv2.imwrite(shadow_path, results[0])
            return shadow_path
        raise RuntimeError("GPSDiffusion returned no results")

    def _pil_soft_shadow(self, composite_path: str, sku: str, work_dir: str) -> str:
        """Perspective-aware contact shadow using PIL.

        Creates a ground-plane shadow darker/sharper near the subject's feet
        and lighter/more diffuse further away.
        """
        import numpy as np
        from PIL import Image, ImageFilter

        img = Image.open(composite_path)

        if img.mode == "RGBA":
            alpha = img.split()[-1]
            alpha_np = np.array(alpha)
            w, h = img.size

            rows = np.any(alpha_np > 128, axis=1)
            cols = np.any(alpha_np > 128, axis=0)
            if not rows.any() or not cols.any():
                shadow_path = str(Path(work_dir) / f"{sku}-shadow.png")
                img.save(shadow_path, format="PNG")
                return shadow_path

            y_max = int(np.where(rows)[0][-1])
            x_min = int(np.where(cols)[0][0])
            x_max = int(np.where(cols)[0][-1])

            # Contact shadow from bottom of subject alpha
            subject_w = x_max - x_min
            shadow_height = max(10, int((y_max - int(np.where(rows)[0][0])) * 0.15))
            foot_region = alpha.crop((x_min, y_max - shadow_height, x_max, y_max))
            foot_region = foot_region.resize((subject_w, shadow_height), Image.Resampling.LANCZOS)

            # Gradient: opaque at contact, fading away
            grad_np = np.zeros((shadow_height, subject_w), dtype=np.float32)
            for row in range(shadow_height):
                grad_np[row, :] = 180 * (1 - row / shadow_height) ** 1.5
            foot_np = np.array(foot_region).astype(np.float32)
            combined = np.clip(foot_np * grad_np / 255.0, 0, 255).astype(np.uint8)
            shadow_mask = Image.fromarray(combined).filter(ImageFilter.GaussianBlur(radius=8))

            # Place shadow below subject feet
            shadow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            shadow_color = Image.new("RGBA", shadow_mask.size, (0, 0, 0, 255))
            paste_y = min(y_max + 5, h - shadow_mask.height)
            paste_x = x_min

            # Clip to bounds
            if paste_y + shadow_mask.height > h:
                crop_h = h - paste_y
                shadow_mask = shadow_mask.crop((0, 0, shadow_mask.width, crop_h))
                shadow_color = shadow_color.crop((0, 0, shadow_color.width, crop_h))
            if paste_x + shadow_mask.width > w:
                crop_w = w - paste_x
                shadow_mask = shadow_mask.crop((0, 0, crop_w, shadow_mask.height))
                shadow_color = shadow_color.crop((0, 0, crop_w, shadow_color.height))

            shadow_layer.paste(shadow_color, (paste_x, paste_y), mask=shadow_mask)
            result = Image.alpha_composite(
                Image.alpha_composite(Image.new("RGBA", img.size, (0, 0, 0, 0)), shadow_layer),
                img,
            )
        else:
            result = img

        shadow_path = str(Path(work_dir) / f"{sku}-shadow.png")
        result.save(shadow_path, format="PNG")
        return shadow_path

    # -----------------------------------------------------------------------
    # Stage 6: Visual QA
    # -----------------------------------------------------------------------

    def _visual_qa(self, composite_path: str, scene_name: str, collection: str) -> dict:
        """Gemini visual QA on final composite."""
        composite_b64 = image_to_base64(composite_path)

        prompt = (
            f"Analyze this composited fashion image for quality.\n\n"
            f"SCENE: {scene_name} (collection: {collection})\n\n"
            f"Rate each criterion 1-10 and return JSON:\n"
            f"{{\n"
            f'  "status": "pass|warn|fail",\n'
            f'  "lighting_match": {{"score": N, "notes": "..."}},\n'
            f'  "garment_fidelity": {{"score": N, "notes": "..."}},\n'
            f'  "scene_coherence": {{"score": N, "notes": "..."}}\n'
            f"}}\n\n"
            f"pass = all scores >= 7, warn = any score 5-6, fail = any score < 5.\n"
            f"Return ONLY valid JSON."
        )

        result = analyze_vision(
            model=COMPOSITOR_QA_MODEL,
            prompt=prompt,
            image_b64=composite_b64,
        )

        if not result.get("success"):
            return {
                "status": "warn",
                "error": result.get("error", "QA unavailable"),
            }

        try:
            text = result["text"]
            if "```json" in text:
                text = text[text.find("```json") + 7 : text.find("```", text.find("```json") + 7)]
            elif "```" in text:
                text = text[text.find("```") + 3 : text.find("```", text.find("```") + 3)]
            return json.loads(text.strip())
        except (json.JSONDecodeError, KeyError):
            return {
                "status": "warn",
                "raw_text": result.get("text", ""),
                "parse_error": True,
            }

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _load_scene_spec(self, scene_image_path: str) -> dict:
        """Load scene.json from the same directory as the scene image."""
        scene_dir = Path(scene_image_path).parent
        spec_path = scene_dir / "scene.json"
        if spec_path.exists():
            with open(spec_path) as f:
                return json.load(f)
        return {}

    def _create_scene_mask(self, alpha_path: str, scene_path: str) -> bytes:
        """Create inpainting mask from alpha matte sized to scene dimensions."""
        import io

        from PIL import Image

        scene = Image.open(scene_path)
        alpha_img = Image.open(alpha_path)

        # Resize alpha to fit scene (centered, lower third for standing model)
        alpha_resized = alpha_img.copy()
        scale = min(scene.width * 0.4 / alpha_img.width, scene.height * 0.8 / alpha_img.height)
        new_w = int(alpha_img.width * scale)
        new_h = int(alpha_img.height * scale)
        alpha_resized = alpha_resized.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Create mask: white where subject should be placed
        mask = Image.new("L", scene.size, 0)
        x = (scene.width - new_w) // 2
        y = scene.height - new_h - int(scene.height * 0.05)

        if alpha_resized.mode == "RGBA":
            alpha_channel = alpha_resized.split()[-1]
            mask.paste(alpha_channel, (x, y))
        else:
            mask.paste(Image.new("L", (new_w, new_h), 255), (x, y))

        buf = io.BytesIO()
        mask.save(buf, format="PNG")
        return buf.getvalue()

    def _save_final(self, source_path: str, output_path: str) -> None:
        """Save final composite as high-quality JPEG."""
        from PIL import Image

        img = Image.open(source_path)
        if img.mode == "RGBA":
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1])
            img = bg

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, format="JPEG", quality=95, optimize=True)

    def _write_audit_log(
        self,
        sku: str,
        scene_name: str,
        stages: dict,
        result: CompositorResult,
        output_dir: str,
    ) -> str:
        """Write JSON audit log for the compositing run."""
        log_data = {
            "sku": sku,
            "scene_name": scene_name,
            "success": result.success,
            "provider": result.provider,
            "qa_status": result.qa_status,
            "stages_completed": result.stages_completed,
            "used_fallback": result.used_fallback,
            "fallback_provider": result.fallback_provider,
            "stages": stages,
        }

        log_dir = Path(output_dir) / "audit"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = str(log_dir / f"{sku}-{scene_name}-audit.json")
        Path(log_path).write_text(json.dumps(log_data, indent=2))
        return log_path

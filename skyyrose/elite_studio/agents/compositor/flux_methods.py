"""FluxProviderMixin — FLUX inpainting provider methods extracted from orchestrator.

Extracted in H-03 of the elite_studio audit (2026-05-24) to keep orchestrator.py
below the 800L ceiling.  CompositorAgent inherits this mixin; all patch paths
(``patch.object(CompositorAgent, "_flux_fill_fal")`` etc.) resolve via MRO with
no test changes needed.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from .infra import (
    _FLUX_FILL_FAL_COST_USD,
    _FLUX_FILL_REPLICATE_COST_USD,
    _FLUX_KONTEXT_FALLBACK_COST_USD,
    _extract_first_image_url,
    _gate_budget,
)

logger = logging.getLogger(__name__)


class FluxProviderMixin:
    """Mixin providing the three FLUX provider methods + fallback chain.

    Designed for single-use by ``CompositorAgent``.  All methods use a lazy
    ``import ...compositor_agent as _mod`` at call time so that
    ``unittest.mock.patch("...compositor_agent.<name>")`` intercepts correctly.
    """

    # ----------------------------------------------- Stage 4: FLUX composite

    def _composite_with_flux(
        self,
        *,
        scene_url: str,
        subject_url: str,
        mask_url: str,
        prompt: str,
        budget: Any = None,
    ) -> tuple[bytes, str]:
        """Run FLUX provider fallback chain via self methods (patchable by tests)."""
        out = self._flux_fill_fal(scene_url, mask_url, prompt)
        if out:
            return out, "fal-fill"

        out = self._flux_kontext(scene_url, mask_url, subject_url, prompt)
        if out:
            return out, "kontext"

        out = self._flux_fill_replicate(scene_url, mask_url, prompt)
        if out:
            return out, "replicate"

        raise RuntimeError("All FLUX providers failed")

    def _flux_fill_fal(
        self,
        scene_url: str,
        mask_url: str,
        prompt: str,
        budget: Any = None,
    ) -> bytes | None:
        """fal-ai/flux-pro/v1/fill — primary inpainting path.

        Reads ``fal_client`` and ``httpx`` from the compositor_agent shim
        namespace so tests can patch them at that location.
        """
        import skyyrose.elite_studio.agents.compositor_agent as _mod

        _gate_budget(budget, _FLUX_FILL_FAL_COST_USD, "flux_fill_fal")

        if _mod.fal_client is None:  # pragma: no cover
            return None
        try:
            result = _mod.fal_client.run(
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
            resp = _mod.httpx.get(url, timeout=60.0)
            resp.raise_for_status()
            image_bytes = resp.content
            if budget is not None:
                budget.spend(_FLUX_FILL_FAL_COST_USD)
            return image_bytes
        except Exception as exc:
            logger.warning("fal-fill errored: %s", exc)
            return None

    def _flux_kontext(
        self,
        scene_url: str,
        mask_url: str,
        ref_url: str,
        prompt: str,
        budget: Any = None,
    ) -> bytes | None:
        """fal-ai/flux-pro/kontext — secondary path.

        Reads ``fal_client`` and ``httpx`` from the compositor_agent shim namespace.
        """
        import skyyrose.elite_studio.agents.compositor_agent as _mod

        _gate_budget(budget, _FLUX_KONTEXT_FALLBACK_COST_USD, "flux_kontext")

        if _mod.fal_client is None:  # pragma: no cover
            return None
        try:
            result = _mod.fal_client.run(
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
            resp = _mod.httpx.get(url, timeout=60.0)
            resp.raise_for_status()
            image_bytes = resp.content
            if budget is not None:
                budget.spend(_FLUX_KONTEXT_FALLBACK_COST_USD)
            return image_bytes
        except Exception as exc:
            logger.warning("kontext errored: %s", exc)
            return None

    def _flux_fill_replicate(
        self,
        scene_url: str,
        mask_url: str,
        prompt: str,
        budget: Any = None,
    ) -> bytes | None:
        """Replicate FLUX Fill — tertiary fallback.

        Reads ``httpx`` from the compositor_agent shim namespace.
        """
        import skyyrose.elite_studio.agents.compositor_agent as _mod

        _gate_budget(budget, _FLUX_FILL_REPLICATE_COST_USD, "flux_fill_replicate")

        token = os.environ.get("REPLICATE_API_TOKEN")
        if not token:
            return None
        try:
            predict = _mod.httpx.post(
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
            for _ in range(60):
                poll = _mod.httpx.get(
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
                    img = _mod.httpx.get(out_url, timeout=60.0)
                    img.raise_for_status()
                    image_bytes = img.content
                    if budget is not None:
                        budget.spend(_FLUX_FILL_REPLICATE_COST_USD)
                    return image_bytes
                if status in ("failed", "canceled"):
                    return None
                time.sleep(2.0)
            return None
        except Exception as exc:
            logger.warning("Replicate FLUX Fill errored: %s", exc)
            return None

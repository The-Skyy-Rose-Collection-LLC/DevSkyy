"""
TryOnAgent — Phase 16 Legendary Try-On Architect.

Promoted to ADK SuperAgent for comprehensive "Back Data" (telemetry) and
high-fidelity virtual try-on.

Inherits from BaseSuperAgent to leverage standardized enterprise tools
and observability via Google ADK.

REAL FASHN integration as of D7 (2026-05-22) — the prior pass-through stub at
line 53 has been removed. Callers must pass public HTTPS image URLs; local
file paths raise FashnError. Upload local renders to Cloudflare R2 (or any
public host) before passing them here.
"""

from __future__ import annotations

import ipaddress
import logging
from pathlib import Path
from urllib.parse import urlparse

from adk.base import ADKProvider, AgentConfig
from adk.super_agents import BaseSuperAgent
from llm.model_ids import GEMINI_FLASH_2_MODEL
from skyyrose.integrations.fashn_client import FashnClient, FashnError

from ..models import TryOnResult

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Hostnames that must never be reachable from a FASHN-side fetch. FASHN
# fetches the URL we hand it server-side, so any private/link-local/loopback
# host = SSRF surface (e.g., 169.254.169.254 = AWS IMDS).
_BLOCKED_HOSTS: frozenset[str] = frozenset({"localhost", "0.0.0.0"})  # nosec B104 — 0.0.0.0 required in containerized/cloud deployment; network isolation at infra layer


def _validate_public_url(label: str, url: str) -> None:
    """Raise FashnError when `url` is not a safe, public https?:// URL.

    Rejects:
      * non-http(s) schemes (file://, gopher://, ftp://)
      * empty/missing hostname
      * private, loopback, link-local, or reserved IPs (RFC 1918 / 6890)
      * literal localhost / 0.0.0.0

    The check is intentionally strict — silently passing a local path to FASHN
    burns a paid API call and exposes the project's internal filesystem.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise FashnError(
            f"{label} URL must use http(s):// scheme — got {parsed.scheme or 'none'!r} in {url!r}"
        )
    host = (parsed.hostname or "").lower()
    if not host:
        raise FashnError(f"{label} URL has no hostname: {url!r}")
    if host in _BLOCKED_HOSTS:
        raise FashnError(f"{label} URL targets blocked host {host!r}")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        # Hostname is a DNS name, not an IP literal — accept.
        return
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
        raise FashnError(
            f"{label} URL targets non-public IP {host!r} ({ip.version}) — refusing to dispatch"
        )


class TryOnAgent(BaseSuperAgent):
    """Virtual try-on specialist promoted to ADK SuperAgent."""

    def __init__(self, config: AgentConfig | None = None) -> None:
        if config is None:
            config = AgentConfig(
                name="legendary_tryon_architect",
                provider=ADKProvider.GOOGLE,
                model=GEMINI_FLASH_2_MODEL,
                system_prompt="You are the Legendary Try-On Architect for SkyyRose. You create seamless digital wear experiences.",
            )
        super().__init__(config)

    async def execute_tryon(
        self,
        garment_image_path: str,
        model_image_path: str,
        category: str = "upper_body",
        garment_sku: str = "unknown",
        num_samples: int = 1,
    ) -> TryOnResult:
        """Execute a real FASHN try-on (no more silent stub).

        Args:
            garment_image_path: PUBLIC https:// URL of the garment cutout.
                Local file:// paths raise FashnError — upload to R2 first.
            model_image_path: PUBLIC https:// URL of the model photo.
            category: upper_body | lower_body | full_body | auto
            garment_sku: SKU label propagated into the result for traceability.
            num_samples: how many output variations (1-16, default 1).

        Returns:
            TryOnResult with `success=True` and `output_path=first FASHN URL`
            on completion. Raises FashnError on any failure — NEVER returns
            input image as a fake-success result.
        """
        # Reject local paths AND private/link-local URLs loudly. The prior stub
        # silently passed local paths through; downstream treated them as tryon
        # results. The SSRF prefix check defends against FASHN's servers being
        # used to scan internal hosts (e.g., AWS IMDS at 169.254.169.254).
        _validate_public_url("garment", garment_image_path)
        _validate_public_url("model", model_image_path)

        # ADK observability — same as before
        adk_prompt = (
            f"TRY-ON TASK: GARMENT={garment_image_path}, MODEL={model_image_path}, CAT={category}"
        )
        logger.info("Running FASHN try-on for %s via ADK", garment_sku)
        adk_result = await self.execute(adk_prompt)
        adk_metadata = adk_result.to_dict() if hasattr(adk_result, "to_dict") else {}

        # Real FASHN dispatch
        try:
            async with FashnClient.from_env() as client:
                fashn_result = await client.run_tryon(
                    model_image_url=model_image_path,
                    garment_image_url=garment_image_path,
                    category=category,  # type: ignore[arg-type]
                    num_samples=num_samples,
                )
        except FashnError:
            raise
        except Exception as exc:
            # Wrap anything unexpected so callers always see FashnError on failure.
            raise FashnError(f"unexpected FASHN failure: {exc}") from exc

        logger.info(
            "FASHN try-on complete for %s in %.1fs (cost $%.2f)",
            garment_sku,
            fashn_result.latency_s,
            fashn_result.cost_usd,
        )

        return TryOnResult(
            success=True,
            output_path=fashn_result.output_urls[0],
            garment_sku=garment_sku,
            model_image_path=model_image_path,
            provider="fashn",
            latency_s=fashn_result.latency_s,
            error="",
            metadata=adk_metadata,
        )


# Aliases for backwards compatibility
TryonAgent = TryOnAgent


def _find_garment_image(sku: str) -> str:
    """Return the path to the garment (flat-lay) image for ``sku``, or empty string.

    Resolves against the project root rather than the process CWD so the answer
    is stable regardless of how the pipeline is invoked. Returns empty string
    when the file does not exist so the caller can skip FASHN dispatch rather
    than sending a phantom path to the provider.
    """
    candidate = _PROJECT_ROOT / "renders" / "output" / sku / f"{sku}-model-front-gemini.jpg"
    return str(candidate) if candidate.is_file() else ""

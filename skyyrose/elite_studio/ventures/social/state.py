"""Pipeline state for the Social Media venture."""

from __future__ import annotations

from typing import TypedDict

from skyyrose.elite_studio.ventures._base import VentureState


class SocialState(VentureState, total=False):
    """Social-venture-specific keys layered onto the shared envelope.

    Cost gates: `generate_graphics` and `run_strategy` default to False.
    The graphics node (CreativeAgent) and strategy node (MarketingAgent)
    only invoke their paid / LLM-backed agents when the matching flag is
    True. The default path — including every smoke run and test — exercises
    only the free, template-based `SocialMediaAgent` publisher.
    """

    skus: list[str]
    platforms: list[str]
    content_type: str
    collection: str | None
    posts: list[dict[str, object]]
    graphics: list[dict[str, object]]
    strategy: dict[str, object]
    generate_graphics: bool
    run_strategy: bool

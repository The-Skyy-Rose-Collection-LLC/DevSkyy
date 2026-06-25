"""Tests for the immersive 3D agent routes.

Verifies:
    - `/api/v1/agents/scene-builder` invokes SDKSceneBuilderAgent and
      returns its result.
    - `/api/v1/agents/avatar-stylist` enforces the FASHN cost gate:
      returns 402 with the cost estimate when `confirm_fashn_cost` is
      False, and proceeds to invoke the agent when True.
    - The cost estimator distinguishes lookbook vs single-outfit tasks.
"""

from __future__ import annotations

import pytest

from api.agents import (
    _FASHN_DEFAULT_IMAGES,
    _FASHN_LOOKBOOK_IMAGES,
    _FASHN_USD_PER_IMAGE,
    _estimate_fashn_cost,
)


class TestEstimateFashnCost:
    """Sync tests for the cost estimator helper (no asyncio mark)."""

    def test_single_outfit(self):
        cost = _estimate_fashn_cost("try on this outfit")
        assert cost["estimated_images"] == _FASHN_DEFAULT_IMAGES
        assert cost["usd_per_image"] == _FASHN_USD_PER_IMAGE
        assert cost["estimated_cost_usd"] == round(_FASHN_DEFAULT_IMAGES * _FASHN_USD_PER_IMAGE, 2)
        assert cost["is_lookbook"] is False

    def test_lookbook_task(self):
        cost = _estimate_fashn_cost("generate full lookbook for the BR collection")
        assert cost["estimated_images"] == _FASHN_LOOKBOOK_IMAGES
        assert cost["is_lookbook"] is True
        # Lookbook should cost meaningfully more than single outfit
        assert cost["estimated_cost_usd"] > _FASHN_DEFAULT_IMAGES * _FASHN_USD_PER_IMAGE

    def test_all_outfits_phrasing(self):
        cost = _estimate_fashn_cost("render all outfits on avatar")
        assert cost["is_lookbook"] is True


@pytest.mark.asyncio
class TestAvatarStylistRoute:
    """The crown-jewel test: cost gate must block paid calls without confirmation."""

    async def test_avatar_stylist_402_without_confirmation(self, client, auth_headers):
        response = await client.post(
            "/api/v1/agents/avatar-stylist",
            json={
                "task": "try on this outfit",
                "sku": "br-001",
            },
            headers=auth_headers,
        )
        assert response.status_code == 402
        body = response.json()
        # The DevSkyy global exception handler wraps HTTPException.detail
        # under "message" rather than the FastAPI default "detail" key.
        cost_detail = body["message"]
        assert cost_detail["error"] == "FASHN cost confirmation required"
        assert cost_detail["paid_api"] == "FASHN"
        assert cost_detail["estimated_cost_usd"] > 0
        assert "confirm_fashn_cost=true" in cost_detail["message"]

    async def test_avatar_stylist_402_for_lookbook(self, client, auth_headers):
        """Lookbook tasks should surface the higher cost estimate."""
        response = await client.post(
            "/api/v1/agents/avatar-stylist",
            json={
                "task": "generate full lookbook for all SKUs",
                "confirm_fashn_cost": False,
            },
            headers=auth_headers,
        )
        assert response.status_code == 402
        cost_detail = response.json()["message"]
        assert cost_detail["is_lookbook"] is True
        assert cost_detail["estimated_images"] == _FASHN_LOOKBOOK_IMAGES

    async def test_avatar_stylist_proceeds_when_confirmed(
        self,
        client,
        auth_headers,
        monkeypatch,
    ):
        """With confirm_fashn_cost=True, agent is invoked and result returned."""
        from agents.claude_sdk.domain_agents import immersive

        # Patch the agent so we don't actually dispatch to Claude SDK
        class FakeAgent:
            def __init__(self, *args, **kwargs):
                pass

            async def execute(self, task, **kwargs):
                return {
                    "success": True,
                    "agent": "sdk_avatar_stylist",
                    "task": task,
                    "kwargs": kwargs,
                }

        monkeypatch.setattr(immersive, "SDKAvatarStylistAgent", FakeAgent)

        response = await client.post(
            "/api/v1/agents/avatar-stylist",
            json={
                "task": "try on this outfit",
                "sku": "br-001",
                "pose": "wave",
                "confirm_fashn_cost": True,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["agent"] == "sdk_avatar_stylist"
        assert body["result"]["success"] is True
        # Cost estimate should be echoed back so callers can record it
        assert body["estimated_cost"]["estimated_cost_usd"] > 0

    async def test_avatar_stylist_requires_auth(self, client):
        response = await client.post(
            "/api/v1/agents/avatar-stylist",
            json={"task": "try on outfit", "confirm_fashn_cost": True},
        )
        assert response.status_code in (401, 403)


@pytest.mark.asyncio
class TestSceneBuilderRoute:
    """Scene builder doesn't touch paid APIs — no cost gate required."""

    async def test_scene_builder_no_cost_gate(self, client, auth_headers, monkeypatch):
        from agents.claude_sdk.domain_agents import immersive

        class FakeAgent:
            def __init__(self, *args, **kwargs):
                pass

            async def execute(self, task, **kwargs):
                return {
                    "success": True,
                    "agent": "sdk_scene_builder",
                    "task": task,
                    "collection": kwargs.get("collection"),
                }

        monkeypatch.setattr(immersive, "SDKSceneBuilderAgent", FakeAgent)

        response = await client.post(
            "/api/v1/agents/scene-builder",
            json={
                "task": "build the Black Rose immersive scene",
                "collection": "black_rose",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["agent"] == "sdk_scene_builder"
        assert body["result"]["collection"] == "black_rose"

    async def test_scene_builder_requires_auth(self, client):
        response = await client.post(
            "/api/v1/agents/scene-builder",
            json={"task": "build a scene"},
        )
        assert response.status_code in (401, 403)

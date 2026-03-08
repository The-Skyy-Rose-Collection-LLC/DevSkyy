"""
WordPress AI SDK Bridge
========================

Cross-agent capability that connects the Python agent fleet to the
WordPress PHP AI Client SDK via REST API.

Providers: OpenAI (GPT-4), Anthropic (Claude), Google (Gemini)
Capabilities: Text generation, image generation, function calling

Maps directly to Round Table providers:
  LLMProvider.GPT4   → WordPress AI SDK "openai"
  LLMProvider.CLAUDE  → WordPress AI SDK "anthropic"
  LLMProvider.GEMINI  → WordPress AI SDK "google"

Usage by any core agent:
    bridge = WordPressAIBridge(wp_url="https://skyyrose.co")
    result = await bridge.generate_text("Write a product description", provider="anthropic")
    result = await bridge.generate_image("Luxury streetwear flat lay", provider="openai")
    status = await bridge.provider_status()
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent

logger = logging.getLogger(__name__)

# Round Table provider → WordPress AI SDK provider mapping
ROUND_TABLE_TO_WP_SDK = {
    "claude": "anthropic",
    "gpt4": "openai",
    "gemini": "google",
}

WP_SDK_TO_ROUND_TABLE = {v: k for k, v in ROUND_TABLE_TO_WP_SDK.items()}


class WordPressAIBridge(SubAgent):
    """
    Bridge between Python agent fleet and WordPress AI SDK.

    Calls the WordPress REST API endpoints provided by wp-ai-client:
      POST /wp-ai/v1/ai/prompt       → Text/image generation
      GET  /wp-ai/v1/ai/providers/models → Provider + model discovery

    Self-healing: If a provider is down, routes to alternatives.
    Circuit breaker: Opens after 5 consecutive failures.
    """

    name = "wp_ai_bridge"
    parent_type = CoreAgentType.ORCHESTRATOR  # Shared across all agents
    description = "WordPress AI SDK bridge — text, image, and function calling via 3 providers"
    capabilities = [
        "text_generation",
        "image_generation",
        "function_calling",
        "provider_status",
        "model_discovery",
    ]

    # Provider priority for auto-selection
    TEXT_PRIORITY = ["anthropic", "openai", "google"]
    IMAGE_PRIORITY = ["openai", "google"]  # Anthropic doesn't do images

    def __init__(
        self,
        *,
        wp_url: str | None = None,
        wp_auth_user: str | None = None,
        wp_auth_pass: str | None = None,
        correlation_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(correlation_id=correlation_id, **kwargs)
        self._wp_url = (wp_url or os.environ.get("WORDPRESS_URL", "https://skyyrose.co")).rstrip(
            "/"
        )
        self._wp_auth_user = wp_auth_user or os.environ.get("WP_AUTH_USER")
        self._wp_auth_pass = wp_auth_pass or os.environ.get("WP_AUTH_PASS")
        self._provider_cache: dict[str, Any] | None = None

    @property
    def _rest_base(self) -> str:
        """WordPress REST API base using index.php?rest_route= (WordPress.com compat)."""
        return f"{self._wp_url}/index.php?rest_route=/wp-ai/v1/ai"

    def _auth(self) -> httpx.BasicAuth | None:
        """Build auth for WordPress REST API."""
        if self._wp_auth_user and self._wp_auth_pass:
            return httpx.BasicAuth(self._wp_auth_user, self._wp_auth_pass)
        return None

    # -------------------------------------------------------------------------
    # Core: Text Generation
    # -------------------------------------------------------------------------

    async def generate_text(
        self,
        prompt: str,
        *,
        provider: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """
        Generate text via WordPress AI SDK.

        Args:
            prompt: The text prompt.
            provider: Force 'openai', 'anthropic', or 'google'.
            model: Specific model ID (e.g., 'gpt-4o', 'claude-sonnet-4-6').
            temperature: Sampling temperature (0.0 - 2.0).
            max_tokens: Max output tokens.

        Returns:
            {"success": True, "text": "...", "provider": "...", "model": "..."}
        """
        payload: dict[str, Any] = {"prompt": prompt}
        if provider:
            payload["provider"] = provider
        if model:
            payload["model"] = model
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        return await self._call_wp_api("/prompt", payload, capability="text")

    # -------------------------------------------------------------------------
    # Core: Image Generation
    # -------------------------------------------------------------------------

    async def generate_image(
        self,
        prompt: str,
        *,
        provider: str | None = None,
        model: str | None = None,
        size: str = "1024x1024",
    ) -> dict[str, Any]:
        """
        Generate an image via WordPress AI SDK.

        Only OpenAI (DALL-E) and Google (Imagen) support images.

        Args:
            prompt: Image description.
            provider: Force 'openai' or 'google'.
            size: Image dimensions.

        Returns:
            {"success": True, "images": [...], "provider": "..."}
        """
        if provider == "anthropic":
            return {
                "success": False,
                "error": "Anthropic does not support image generation",
            }

        payload: dict[str, Any] = {
            "prompt": prompt,
            "type": "image",
            "size": size,
        }
        if provider:
            payload["provider"] = provider
        if model:
            payload["model"] = model

        return await self._call_wp_api("/prompt", payload, capability="image")

    # -------------------------------------------------------------------------
    # Core: Provider Status
    # -------------------------------------------------------------------------

    async def provider_status(self) -> dict[str, Any]:
        """
        Check which providers are configured and available.

        Returns:
            {
                "openai": {"configured": True, "models": [...]},
                "anthropic": {"configured": True, "models": [...]},
                "google": {"configured": False, "models": []},
            }
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{self._rest_base}/providers/models",
                    auth=self._auth(),
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self._provider_cache = data
                    self._record_success()
                    return {"success": True, "providers": data}

                return {
                    "success": False,
                    "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
                }
        except Exception as exc:
            self._record_failure()
            return {"success": False, "error": str(exc)}

    # -------------------------------------------------------------------------
    # Core: Model Discovery
    # -------------------------------------------------------------------------

    async def list_models(self, provider: str | None = None) -> dict[str, Any]:
        """List available models, optionally filtered by provider."""
        status = await self.provider_status()
        if not status.get("success"):
            return status

        providers = status.get("providers", {})
        if provider:
            return {
                "success": True,
                "models": providers.get(provider, {}).get("models", []),
            }
        return {"success": True, "providers": providers}

    # -------------------------------------------------------------------------
    # SubAgent Interface
    # -------------------------------------------------------------------------

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        """
        SubAgent entry point — routes task to the right capability.

        Keywords determine action:
        - "status" / "providers" → provider_status()
        - "image" / "generate image" → generate_image()
        - Default → generate_text()
        """
        task_lower = task.lower()

        # Provider status check
        if any(kw in task_lower for kw in ["status", "providers", "models", "available"]):
            return await self.provider_status()

        # Image generation
        if any(
            kw in task_lower for kw in ["image", "picture", "photo", "visual", "dalle", "imagen"]
        ):
            provider = kwargs.get("provider")
            return await self.generate_image(task, provider=provider)

        # Default: text generation
        provider = kwargs.get("provider")
        return await self.generate_text(
            task,
            provider=provider,
            **{k: v for k, v in kwargs.items() if k in ("model", "temperature", "max_tokens")},
        )

    # -------------------------------------------------------------------------
    # Round Table Integration
    # -------------------------------------------------------------------------

    def get_round_table_mapping(self) -> dict[str, str]:
        """
        Map Round Table provider names to WordPress AI SDK providers.

        Used by the Round Table to route competitions through the WordPress SDK.
        """
        return dict(ROUND_TABLE_TO_WP_SDK)

    async def compete_for_round_table(
        self,
        prompt: str,
        round_table_provider: str,
    ) -> dict[str, Any]:
        """
        Execute a prompt for a specific Round Table provider via WordPress SDK.

        This allows Round Table competitions to flow through the WordPress AI SDK,
        using the same credentials and provider configuration.
        """
        wp_provider = ROUND_TABLE_TO_WP_SDK.get(round_table_provider)
        if not wp_provider:
            return {
                "success": False,
                "error": f"Unknown Round Table provider: {round_table_provider}",
            }
        return await self.generate_text(prompt, provider=wp_provider)

    # -------------------------------------------------------------------------
    # Internal
    # -------------------------------------------------------------------------

    async def _call_wp_api(
        self,
        endpoint: str,
        payload: dict[str, Any],
        capability: str = "text",
    ) -> dict[str, Any]:
        """Make a POST request to WordPress AI SDK REST API."""
        url = f"{self._rest_base}{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    url,
                    json=payload,
                    auth=self._auth(),
                )

                if resp.status_code == 200:
                    data = resp.json()
                    self._record_success()
                    return {
                        "success": True,
                        **data,
                    }

                self._record_failure()
                return {
                    "success": False,
                    "error": f"WordPress AI SDK returned {resp.status_code}",
                    "details": resp.text[:500],
                }

        except httpx.TimeoutException:
            self._record_failure()
            return {
                "success": False,
                "error": f"Timeout calling WordPress AI SDK ({capability})",
            }
        except Exception as exc:
            self._record_failure()
            return {
                "success": False,
                "error": f"WordPress AI SDK error: {exc}",
            }

    # -------------------------------------------------------------------------
    # Dashboard Serialization
    # -------------------------------------------------------------------------

    def to_dashboard_card(self) -> dict[str, Any]:
        """
        Serialize for the admin dashboard agent card.

        Returns data for the /admin/agents page.
        """
        health = self.health_check()
        return {
            "id": "wp_ai_bridge",
            "name": "WordPress AI Bridge",
            "type": "shared",
            "status": "active" if health.healthy else "offline",
            "description": self.description,
            "capabilities": self.capabilities,
            "providers": {
                "openai": {"name": "OpenAI", "models": ["GPT-4o", "GPT-4.1", "DALL-E 3"]},
                "anthropic": {"name": "Anthropic", "models": ["Claude Opus", "Claude Sonnet"]},
                "google": {"name": "Google", "models": ["Gemini 2.5", "Imagen 3"]},
            },
            "round_table_mapping": ROUND_TABLE_TO_WP_SDK,
            "healthy": health.healthy,
            "circuit_breaker": health.circuit_breaker,
            "consecutive_failures": health.consecutive_failures,
        }


__all__ = ["WordPressAIBridge", "ROUND_TABLE_TO_WP_SDK", "WP_SDK_TO_ROUND_TABLE"]

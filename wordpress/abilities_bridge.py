"""
WordPress Abilities API Bridge
=============================

Python client for WordPress Abilities API integration.
Enables DevSkyy agents to register and execute abilities via WordPress REST API.

The WordPress Abilities API provides:
- Discoverability: Every ability can be listed, queried, and inspected
- Interoperability: Uniform schema lets components compose workflows
- Security-first: Explicit permissions determine who may invoke an ability
- MCP/A2A compatibility: Designed for AI assistant protocols

REST Endpoints:
- GET  /wp-json/wp-abilities/v1/abilities - List all abilities
- GET  /wp-json/wp-abilities/v1/abilities/{name} - Get ability details
- POST /wp-json/wp-abilities/v1/abilities/{name}/run - Execute ability
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class AbilityAnnotations:
    """Ability behavior annotations."""

    readonly: bool | None = None  # If true, ability does not modify environment
    destructive: bool | None = None  # If true, may perform destructive updates
    idempotent: bool | None = None  # If true, repeated calls have no additional effect


@dataclass
class Ability:
    """Represents a WordPress Ability."""

    name: str  # Namespaced name, e.g., "devskyy/generate-product-image"
    label: str  # Human-readable label
    description: str  # Detailed description
    category: str  # Ability category slug
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    annotations: AbilityAnnotations = field(default_factory=AbilityAnnotations)
    show_in_rest: bool = True


class WordPressAbilitiesClient:
    """
    Client for WordPress Abilities API.

    Enables DevSkyy to register abilities in WordPress and execute them via REST API.
    """

    def __init__(
        self,
        wordpress_url: str,
        username: str | None = None,
        app_password: str | None = None,
    ):
        """
        Initialize WordPress Abilities client.

        Args:
            wordpress_url: Base WordPress URL (e.g., https://example.com)
            username: WordPress username for authentication
            app_password: WordPress application password
        """
        self.base_url = wordpress_url.rstrip("/")
        self.api_url = f"{self.base_url}/wp-json/wp-abilities/v1"
        self.username = username
        self.app_password = app_password

    def _get_auth(self) -> aiohttp.BasicAuth | None:
        """Get authentication for requests."""
        if self.username and self.app_password:
            return aiohttp.BasicAuth(self.username, self.app_password)
        return None

    async def list_abilities(self, category: str | None = None) -> list[dict[str, Any]]:
        """
        List all registered abilities.

        Args:
            category: Optional category filter

        Returns:
            List of ability objects
        """
        params = {}
        if category:
            params["category"] = category

        async with (
            aiohttp.ClientSession() as session,
            session.get(
                f"{self.api_url}/abilities",
                params=params,
                auth=self._get_auth(),
            ) as response,
        ):
            response.raise_for_status()
            return await response.json()

    async def get_ability(self, name: str) -> dict[str, Any] | None:
        """
        Get details for a specific ability.

        Args:
            name: Ability name (e.g., "devskyy/generate-image")

        Returns:
            Ability details or None if not found
        """
        async with (
            aiohttp.ClientSession() as session,
            session.get(
                f"{self.api_url}/abilities/{name}",
                auth=self._get_auth(),
            ) as response,
        ):
            if response.status == 404:
                return None
            response.raise_for_status()
            return await response.json()

    async def execute_ability(
        self,
        name: str,
        input_data: Any | None = None,
        method: str = "POST",
    ) -> dict[str, Any]:
        """
        Execute an ability.

        Args:
            name: Ability name
            input_data: Input data for the ability
            method: HTTP method (GET for readonly, POST for updates, DELETE for destructive)

        Returns:
            Ability execution result
        """
        async with aiohttp.ClientSession() as session:
            kwargs: dict[str, Any] = {"auth": self._get_auth()}

            if method == "GET":
                kwargs["params"] = {"input": input_data} if input_data else {}
            else:
                kwargs["json"] = {"input": input_data} if input_data else {}

            async with session.request(
                method,
                f"{self.api_url}/abilities/{name}/run",
                **kwargs,
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def check_plugin_active(self) -> bool:
        """Check if Abilities API plugin is active."""
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(f"{self.api_url}/abilities") as response,
            ):
                return response.status == 200
        except Exception:
            return False

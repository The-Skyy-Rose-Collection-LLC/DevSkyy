"""
Backend Dev Agent Spec — PHP, Python, Node.js, APIs, databases.

Model: Claude Sonnet 4.6 (best coding model for server logic)
"""

from __future__ import annotations


def _build_spec() -> dict:
    """
    Constructs the backend_dev agent specification used by the Elite Web Builder.
    
    Returns:
        spec (dict): A mapping containing the agent specification with the following top-level keys:
            - role (str): Agent role identifier.
            - name (str): Agent name.
            - system_prompt (str): System prompt describing capabilities, constraints, and integration notes.
            - capabilities (List[dict]): Capability entries, each with `name` (str), `description` (str), and `tags` (List[str]).
            - knowledge_files (List[str]): Paths to knowledge resources the agent may reference.
            - preferred_model (dict): Model preference with `provider` (str) and `model` (str).
    """
    return {
        "role": "backend_dev",
        "name": "backend_dev",
        "system_prompt": (
            "You are a Backend Development specialist for the Elite Web Builder. "
            "You write PHP 8.x, Python/FastAPI, Node.js/Express, and database "
            "schemas. You configure WooCommerce (products, cart, checkout, "
            "webhooks, HPOS) and WordPress REST API. "
            "Build Shopify integrations using Storefront API (GraphQL) and Admin API. "
            "Configure Shopify Functions for custom discounts and payment flows. "
            "Use parameterized queries for all database access. "
            "Validate all user inputs with Zod/schema validation. "
            "Environment variables for all secrets. "
            "WordPress API: use index.php?rest_route= (NOT /wp-json/)."
        ),
        "capabilities": [
            {
                "name": "php_wordpress",
                "description": "Write WordPress PHP: hooks, filters, REST endpoints",
                "tags": ["backend", "php", "wordpress"],
            },
            {
                "name": "woocommerce",
                "description": "Configure WooCommerce: products, payments, shipping, tax",
                "tags": ["backend", "woocommerce", "ecommerce"],
            },
            {
                "name": "api_development",
                "description": "Build REST/GraphQL APIs with auth and validation",
                "tags": ["backend", "api", "graphql"],
            },
            {
                "name": "database",
                "description": "Design schemas, write migrations, optimize queries",
                "tags": ["backend", "database", "sql"],
            },
            {
                "name": "shopify_api",
                "description": "Integrate Shopify Storefront and Admin APIs",
                "tags": ["backend", "shopify", "graphql"],
            },
        ],
        "knowledge_files": [
            "knowledge/wordpress.md",
            "knowledge/shopify.md",
            "knowledge/woocommerce.md",
            "knowledge/security_checklist.md",
        ],
        "preferred_model": {"provider": "anthropic", "model": "claude-sonnet-4-6"},
    }


BACKEND_DEV_SPEC = _build_spec()
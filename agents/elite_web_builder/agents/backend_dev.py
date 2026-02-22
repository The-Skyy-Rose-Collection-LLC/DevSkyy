"""Backend Dev Agent — PHP, Python, Node.js, databases, APIs, WooCommerce.

Model: Claude Sonnet 4.6 (best coding model for server logic)
"""

from __future__ import annotations

from agents.base import AgentCapability, AgentRole, AgentSpec

BACKEND_DEV_SPEC = AgentSpec(
    role=AgentRole.BACKEND_DEV,
    name="backend_dev",
    system_prompt=(
        "You are a Backend Development specialist. You build server-side "
        "logic, APIs, database interactions, and platform integrations.\n\n"
        "Core responsibilities:\n"
        "- Write PHP for WordPress hooks, filters, and REST API endpoints\n"
        "- Build Python/FastAPI services and Node.js APIs\n"
        "- Configure WooCommerce products, payments, and shipping\n"
        "- Design database schemas and optimize queries\n"
        "- Implement authentication, authorization, and security\n"
        "- Build webhook handlers and third-party integrations\n\n"
        "Output rules:\n"
        "- All database queries use parameterized statements (no string concat)\n"
        "- Secrets loaded from environment variables, never hardcoded\n"
        "- Error handling at every boundary (try/catch with logging)\n"
        "- Input validation on all user-facing endpoints\n"
        "- Rate limiting on public APIs\n"
        "- WordPress REST routes use index.php?rest_route= (not /wp-json/)\n"
        "- WordPress.com MCP tools available for direct content management\n"
        "- Target site: skyyrose.co (Blog ID: 238510894, Atomic platform)\n"
        "- ALWAYS create content as draft, NEVER publish without user approval\n"
        "- Use theme preset slugs (gold, crimson, rose) not hardcoded hex values\n"
        "- Check _content_warnings after every content API save"
    ),
    capabilities=[
        AgentCapability(
            name="wordpress_php",
            description="Write PHP for WordPress hooks, filters, shortcodes, REST API",
            tags=("backend", "php", "wordpress"),
        ),
        AgentCapability(
            name="woocommerce",
            description="Configure WooCommerce products, payments, shipping, tax",
            tags=("backend", "woocommerce", "ecommerce"),
        ),
        AgentCapability(
            name="api_development",
            description="Build REST and GraphQL APIs with auth and validation",
            tags=("backend", "api", "rest", "graphql"),
        ),
        AgentCapability(
            name="database",
            description="Design schemas, write migrations, optimize queries",
            tags=("backend", "database", "sql"),
        ),
        AgentCapability(
            name="integrations",
            description="Wire third-party services (Klaviyo, Stripe, TikTok, Pinterest)",
            tags=("backend", "integrations"),
        ),
    ],
    knowledge_files=[
        "knowledge/wordpress.md",
        "knowledge/wordpress_deployment.md",
        "knowledge/photo_generation.md",
        "knowledge/security_checklist.md",
    ],
)

"""SEO & Content Agent — meta tags, schema.org, copywriting, structured data.

Model: GPT-4o (strongest natural language generation)
"""

from __future__ import annotations

from agents.base import AgentCapability, AgentRole, AgentSpec

SEO_CONTENT_SPEC = AgentSpec(
    role=AgentRole.SEO_CONTENT,
    name="seo_content",
    system_prompt=(
        "You are an SEO & Content specialist. You optimize web content "
        "for search engines and write compelling copy that converts.\n\n"
        "Core responsibilities:\n"
        "- Write meta titles (50-60 chars) and descriptions (150-160 chars)\n"
        "- Implement schema.org structured data (JSON-LD)\n"
        "- Configure Open Graph and Twitter Card meta tags\n"
        "- Write product descriptions, page copy, and CTAs\n"
        "- Build XML sitemaps and robots.txt\n"
        "- Optimize heading hierarchy (single H1, logical H2-H6)\n\n"
        "Output rules:\n"
        "- Every page must have unique title and meta description\n"
        "- Schema.org uses JSON-LD format (not microdata)\n"
        "- Product pages include Product, Offer, and BreadcrumbList schemas\n"
        "- Copy matches brand voice (luxury, aspirational, confident)\n"
        "- No keyword stuffing — natural, readable prose\n"
        "- All images have descriptive alt text"
    ),
    capabilities=[
        AgentCapability(
            name="meta_tags",
            description="Write optimized meta titles, descriptions, and social tags",
            tags=("seo", "meta", "opengraph"),
        ),
        AgentCapability(
            name="structured_data",
            description="Implement schema.org JSON-LD structured data",
            tags=("seo", "schema", "json-ld"),
        ),
        AgentCapability(
            name="copywriting",
            description="Write brand-aligned product descriptions and page copy",
            tags=("content", "copywriting"),
        ),
        AgentCapability(
            name="sitemap",
            description="Generate and optimize XML sitemaps",
            tags=("seo", "sitemap"),
        ),
    ],
    knowledge_files=[
        "knowledge/wordpress.md",
        "knowledge/wordpress_deployment.md",
        "knowledge/photo_generation.md",
    ],
)

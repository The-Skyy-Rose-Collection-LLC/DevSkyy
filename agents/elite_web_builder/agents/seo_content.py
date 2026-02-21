"""
SEO & Content Agent Spec — Meta tags, schema.org, copywriting, structured data.

Model: GPT-4o (strongest natural language generation)
"""

from __future__ import annotations


def _build_spec() -> dict:
    """
    Builds the SEO & Content agent specification used by Elite Web Builder.
    
    Returns:
        spec (dict): Specification dictionary containing the keys "role", "name", "system_prompt", "capabilities", "knowledge_files", and "preferred_model".
    """
    return {
        "role": "seo_content",
        "name": "seo_content",
        "system_prompt": (
            "You are an SEO & Content specialist for the Elite Web Builder. "
            "You generate meta tags, Open Graph, Twitter Cards, "
            "schema.org structured data (JSON-LD), sitemaps, "
            "and optimized copy. You write product descriptions, "
            "collection narratives, and landing page content. "
            "Generate SEO content compatible with both WordPress Yoast/RankMath "
            "and Shopify's native SEO fields. "
            "All content must be original, brand-aligned, and keyword-optimized. "
            "No keyword stuffing. Natural language priority."
        ),
        "capabilities": [
            {
                "name": "meta_tags",
                "description": "Generate meta titles, descriptions, OG tags",
                "tags": ["seo", "meta", "opengraph"],
            },
            {
                "name": "structured_data",
                "description": "Create schema.org JSON-LD for products, articles, org",
                "tags": ["seo", "schema", "jsonld"],
            },
            {
                "name": "copywriting",
                "description": "Write brand-aligned product and page copy",
                "tags": ["content", "copywriting", "brand"],
            },
            {
                "name": "sitemap",
                "description": "Generate and validate XML sitemaps",
                "tags": ["seo", "sitemap", "xml"],
            },
        ],
        "knowledge_files": [
            "knowledge/wordpress.md",
            "knowledge/shopify.md",
        ],
        "preferred_model": {"provider": "openai", "model": "gpt-4o"},
    }


SEO_CONTENT_SPEC = _build_spec()
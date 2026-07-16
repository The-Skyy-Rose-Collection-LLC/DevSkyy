"""OpenAI ChatGPT product-feed generator package.

Maps live WooCommerce products (skyyrose.co) to the OpenAI Commerce "Stable"
file-upload product feed schema documented in
docs/integrations/openai-product-feed-spec.md, validates every item against
the spec's required fields, and writes a spec-accepted feed file.

See scripts/openai_product_feed.py for the CLI entry point.
"""

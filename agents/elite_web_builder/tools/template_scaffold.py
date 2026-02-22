"""Template scaffolding tool — WordPress, Shopify, and frontend components.

Generates skeleton template files for WordPress FSE themes, Shopify Online
Store 2.0, and frontend component frameworks. All outputs are frozen
dataclasses (immutable).

Usage:
    result = scaffold_wordpress_template("page", "about")
    for f in result.files:
        print(f.path, len(f.content))

    result = scaffold_shopify_template("section", "hero-banner")
    result = scaffold_component("react", "HeroBanner")
    catalog = list_templates()
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ScaffoldError(Exception):
    """Raised when scaffolding fails (invalid type, unsupported framework)."""


# ---------------------------------------------------------------------------
# Data models (immutable)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScaffoldFile:
    """A single generated file with its relative path and content."""

    path: str
    content: str


@dataclass(frozen=True)
class ScaffoldResult:
    """Immutable result of a scaffold operation."""

    platform: str
    template_type: str
    name: str
    files: tuple[ScaffoldFile, ...]
    metadata: dict[str, Any]


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_name(name: str, label: str = "name") -> str:
    """Validate and return stripped name. Raises ValueError if empty."""
    if not name or not name.strip():
        raise ValueError(f"{label} must not be empty")
    return name.strip()


def _slugify(name: str) -> str:
    """Convert a name to a URL-safe slug (lowercase, hyphens, no specials)."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


# ---------------------------------------------------------------------------
# WordPress constants
# ---------------------------------------------------------------------------

_WP_TEMPLATE_TYPES = frozenset({
    "page", "archive", "single", "template-part", "block-pattern",
})


# ---------------------------------------------------------------------------
# WordPress generators (each under 50 lines)
# ---------------------------------------------------------------------------


def _wp_page(name: str, slug: str, options: dict[str, Any]) -> tuple[ScaffoldFile, ...]:
    """Generate WordPress FSE page template + block pattern JSON."""
    title = options.get("title", name)
    html_content = (
        f'<!-- wp:template-part {{"slug":"header","area":"header"}} /-->\n'
        f"\n"
        f'<!-- wp:group {{"tagName":"main","layout":{{"type":"constrained"}}}} -->\n'
        f'<main class="wp-block-group">\n'
        f"  <!-- wp:heading -->\n"
        f"  <h1>{title}</h1>\n"
        f"  <!-- /wp:heading -->\n"
        f"\n"
        f"  <!-- wp:paragraph -->\n"
        f"  <p>Content for {title} goes here.</p>\n"
        f"  <!-- /wp:paragraph -->\n"
        f"</main>\n"
        f"<!-- /wp:group -->\n"
        f"\n"
        f'<!-- wp:template-part {{"slug":"footer","area":"footer"}} /-->\n'
    )
    pattern_json = json.dumps(
        {
            "title": title,
            "slug": slug,
            "description": options.get("description", f"Template for {title}"),
            "templateTypes": ["page"],
            "blockTypes": ["core/post-content"],
        },
        indent=2,
    )
    return (
        ScaffoldFile(path=f"templates/{slug}.html", content=html_content),
        ScaffoldFile(path=f"patterns/{slug}.json", content=pattern_json),
    )


def _wp_archive(name: str, slug: str, options: dict[str, Any]) -> tuple[ScaffoldFile, ...]:
    """Generate WordPress FSE archive template."""
    title = options.get("title", name)
    html_content = (
        f'<!-- wp:template-part {{"slug":"header","area":"header"}} /-->\n'
        f"\n"
        f'<!-- wp:group {{"tagName":"main","layout":{{"type":"constrained"}}}} -->\n'
        f'<main class="wp-block-group">\n'
        f"  <!-- wp:query-title {{\"type\":\"archive\"}} /-->\n"
        f"  <!-- wp:query -->\n"
        f"    <!-- wp:post-template -->\n"
        f"      <!-- wp:post-title {{\"isLink\":true}} /-->\n"
        f"      <!-- wp:post-excerpt /-->\n"
        f"      <!-- wp:post-date /-->\n"
        f"    <!-- /wp:post-template -->\n"
        f"    <!-- wp:query-pagination /-->\n"
        f"  <!-- /wp:query -->\n"
        f"</main>\n"
        f"<!-- /wp:group -->\n"
        f"\n"
        f'<!-- wp:template-part {{"slug":"footer","area":"footer"}} /-->\n'
    )
    return (ScaffoldFile(path=f"templates/archive-{slug}.html", content=html_content),)


def _wp_single(name: str, slug: str, options: dict[str, Any]) -> tuple[ScaffoldFile, ...]:
    """Generate WordPress FSE single post template."""
    html_content = (
        f'<!-- wp:template-part {{"slug":"header","area":"header"}} /-->\n'
        f"\n"
        f'<!-- wp:group {{"tagName":"main","layout":{{"type":"constrained"}}}} -->\n'
        f'<main class="wp-block-group">\n'
        f"  <!-- wp:post-title /-->\n"
        f"  <!-- wp:post-featured-image /-->\n"
        f"  <!-- wp:post-content /-->\n"
        f"  <!-- wp:post-terms {{\"term\":\"category\"}} /-->\n"
        f"  <!-- wp:post-terms {{\"term\":\"post_tag\"}} /-->\n"
        f"</main>\n"
        f"<!-- /wp:group -->\n"
        f"\n"
        f'<!-- wp:template-part {{"slug":"footer","area":"footer"}} /-->\n'
    )
    return (ScaffoldFile(path=f"templates/single-{slug}.html", content=html_content),)


def _wp_template_part(name: str, slug: str, options: dict[str, Any]) -> tuple[ScaffoldFile, ...]:
    """Generate WordPress FSE template part."""
    area = options.get("area", "uncategorized")
    html_content = (
        f'<!-- wp:group {{"layout":{{"type":"constrained"}}}} -->\n'
        f'<div class="wp-block-group">\n'
        f"  <!-- Add {name} content here -->\n"
        f"</div>\n"
        f"<!-- /wp:group -->\n"
    )
    return (ScaffoldFile(path=f"parts/{slug}.html", content=html_content),)


def _wp_block_pattern(name: str, slug: str, options: dict[str, Any]) -> tuple[ScaffoldFile, ...]:
    """Generate WordPress block pattern with registration PHP."""
    title = options.get("title", name)
    description = options.get("description", f"Block pattern: {title}")
    category = options.get("category", "custom")
    php_content = (
        f"<?php\n"
        f"/**\n"
        f" * Block Pattern: {title}\n"
        f" *\n"
        f" * @package theme\n"
        f" */\n"
        f"\n"
        f"register_block_pattern(\n"
        f"    'theme/{slug}',\n"
        f"    array(\n"
        f"        'title'       => __( '{title}', 'theme' ),\n"
        f"        'description' => __( '{description}', 'theme' ),\n"
        f"        'categories'  => array( '{category}' ),\n"
        f"        'content'     => '\n"
        f'<!-- wp:group {{"layout":{{"type":"constrained"}}}} -->\n'
        f'<div class="wp-block-group">\n'
        f"  <!-- wp:heading -->\n"
        f"  <h2>{title}</h2>\n"
        f"  <!-- /wp:heading -->\n"
        f"  <!-- wp:paragraph -->\n"
        f"  <p>Pattern content goes here.</p>\n"
        f"  <!-- /wp:paragraph -->\n"
        f"</div>\n"
        f"<!-- /wp:group -->\n"
        f"',\n"
        f"    )\n"
        f");\n"
    )
    return (ScaffoldFile(path=f"patterns/{slug}.php", content=php_content),)


_WP_GENERATORS = {
    "page": _wp_page,
    "archive": _wp_archive,
    "single": _wp_single,
    "template-part": _wp_template_part,
    "block-pattern": _wp_block_pattern,
}


# ---------------------------------------------------------------------------
# Shopify constants
# ---------------------------------------------------------------------------

_SHOPIFY_TEMPLATE_TYPES = frozenset({
    "page", "collection", "product", "section", "snippet",
})


# ---------------------------------------------------------------------------
# Shopify generators (each under 50 lines)
# ---------------------------------------------------------------------------


def _shopify_json_template(slug: str, title: str, template_type: str) -> str:
    """Build Shopify Online Store 2.0 JSON template content."""
    return json.dumps(
        {
            "name": title,
            "sections": {
                "main": {
                    "type": f"main-{template_type}",
                    "settings": {},
                },
            },
            "order": ["main"],
        },
        indent=2,
    )


def _shopify_page(name: str, slug: str, options: dict[str, Any]) -> tuple[ScaffoldFile, ...]:
    """Generate Shopify page JSON template."""
    title = options.get("title", name)
    content = _shopify_json_template(slug, title, "page")
    return (ScaffoldFile(path=f"templates/page.{slug}.json", content=content),)


def _shopify_collection(name: str, slug: str, options: dict[str, Any]) -> tuple[ScaffoldFile, ...]:
    """Generate Shopify collection JSON template."""
    title = options.get("title", name)
    content = _shopify_json_template(slug, title, "collection")
    return (ScaffoldFile(path=f"templates/collection.{slug}.json", content=content),)


def _shopify_product(name: str, slug: str, options: dict[str, Any]) -> tuple[ScaffoldFile, ...]:
    """Generate Shopify product JSON template."""
    title = options.get("title", name)
    content = _shopify_json_template(slug, title, "product")
    return (ScaffoldFile(path=f"templates/product.{slug}.json", content=content),)


def _shopify_section(name: str, slug: str, options: dict[str, Any]) -> tuple[ScaffoldFile, ...]:
    """Generate Shopify section Liquid file with schema."""
    title = options.get("title", name)
    schema = json.dumps(
        {
            "name": title,
            "tag": "section",
            "class": f"section-{slug}",
            "settings": [
                {
                    "type": "text",
                    "id": "heading",
                    "label": "Heading",
                    "default": title,
                },
            ],
            "presets": [{"name": title}],
        },
        indent=2,
    )
    liquid = (
        f'<section class="section-{slug}">\n'
        f"  <div class=\"container\">\n"
        f"    <h2>{{{{ section.settings.heading }}}}</h2>\n"
        f"    <!-- Section content for {title} -->\n"
        f"  </div>\n"
        f"</section>\n"
        f"\n"
        f"{{% schema %}}\n"
        f"{schema}\n"
        f"{{% endschema %}}\n"
    )
    return (ScaffoldFile(path=f"sections/{slug}.liquid", content=liquid),)


def _shopify_snippet(name: str, slug: str, options: dict[str, Any]) -> tuple[ScaffoldFile, ...]:
    """Generate Shopify snippet Liquid file."""
    title = options.get("title", name)
    liquid = (
        f'{{% comment %}}\n'
        f"  Snippet: {title}\n"
        f"  Usage: {{% render '{slug}' %}}\n"
        f'{{% endcomment %}}\n'
        f"\n"
        f'<div class="snippet-{slug}">\n'
        f"  <!-- {title} content -->\n"
        f"</div>\n"
    )
    return (ScaffoldFile(path=f"snippets/{slug}.liquid", content=liquid),)


_SHOPIFY_GENERATORS = {
    "page": _shopify_page,
    "collection": _shopify_collection,
    "product": _shopify_product,
    "section": _shopify_section,
    "snippet": _shopify_snippet,
}


# ---------------------------------------------------------------------------
# Component generators (each under 50 lines)
# ---------------------------------------------------------------------------

_COMPONENT_FRAMEWORKS = frozenset({"react", "vue", "vanilla"})


def _component_react(name: str, slug: str, options: dict[str, Any]) -> tuple[ScaffoldFile, ...]:
    """Generate React TSX component + test + CSS module."""
    component = (
        f"import React from 'react';\n"
        f"import styles from './{name}.module.css';\n"
        f"\n"
        f"interface {name}Props {{\n"
        f"  className?: string;\n"
        f"}}\n"
        f"\n"
        f"export function {name}({{ className }}: {name}Props) {{\n"
        f"  return (\n"
        f"    <div className={{`${{styles.root}} ${{className ?? ''}}`}}>\n"
        f"      <h2>{name}</h2>\n"
        f"    </div>\n"
        f"  );\n"
        f"}}\n"
        f"\n"
        f"export default {name};\n"
    )
    test = (
        f"import {{ render, screen }} from '@testing-library/react';\n"
        f"import {{ {name} }} from './{name}';\n"
        f"\n"
        f"describe('{name}', () => {{\n"
        f"  it('renders without crashing', () => {{\n"
        f"    render(<{name} />);\n"
        f"    expect(screen.getByText('{name}')).toBeInTheDocument();\n"
        f"  }});\n"
        f"}});\n"
    )
    css = (
        f".root {{\n"
        f"  /* {name} styles */\n"
        f"}}\n"
    )
    return (
        ScaffoldFile(path=f"{name}/{name}.tsx", content=component),
        ScaffoldFile(path=f"{name}/{name}.test.tsx", content=test),
        ScaffoldFile(path=f"{name}/{name}.module.css", content=css),
    )


def _component_vue(name: str, slug: str, options: dict[str, Any]) -> tuple[ScaffoldFile, ...]:
    """Generate Vue SFC component + test + CSS module."""
    vue = (
        f"<template>\n"
        f'  <div :class="$style.root">\n'
        f"    <h2>{name}</h2>\n"
        f"  </div>\n"
        f"</template>\n"
        f"\n"
        f"<script setup lang=\"ts\">\n"
        f"defineProps<{{\n"
        f"  className?: string;\n"
        f"}}>();\n"
        f"</script>\n"
        f"\n"
        f"<style module>\n"
        f".root {{\n"
        f"  /* {name} styles */\n"
        f"}}\n"
        f"</style>\n"
    )
    test = (
        f"import {{ mount }} from '@vue/test-utils';\n"
        f"import {name} from './{name}.vue';\n"
        f"\n"
        f"describe('{name}', () => {{\n"
        f"  it('renders correctly', () => {{\n"
        f"    const wrapper = mount({name});\n"
        f"    expect(wrapper.text()).toContain('{name}');\n"
        f"  }});\n"
        f"}});\n"
    )
    css = (
        f".root {{\n"
        f"  /* {name} styles */\n"
        f"}}\n"
    )
    return (
        ScaffoldFile(path=f"{name}/{name}.vue", content=vue),
        ScaffoldFile(path=f"{name}/{name}.test.ts", content=test),
        ScaffoldFile(path=f"{name}/{name}.module.css", content=css),
    )


def _component_vanilla(name: str, slug: str, options: dict[str, Any]) -> tuple[ScaffoldFile, ...]:
    """Generate vanilla JS/TS component + test + CSS."""
    use_ts = options.get("typescript", False)
    ext = "ts" if use_ts else "js"
    component = (
        f"/**\n"
        f" * {name} component\n"
        f" */\n"
        f"export function create{name}(container) {{\n"
        f"  const el = document.createElement('div');\n"
        f"  el.className = '{slug}';\n"
        f"  el.innerHTML = '<h2>{name}</h2>';\n"
        f"  container.appendChild(el);\n"
        f"  return el;\n"
        f"}}\n"
    )
    test = (
        f"import {{ create{name} }} from './{name}';\n"
        f"\n"
        f"describe('{name}', () => {{\n"
        f"  it('creates element in container', () => {{\n"
        f"    const container = document.createElement('div');\n"
        f"    const el = create{name}(container);\n"
        f"    expect(el.textContent).toContain('{name}');\n"
        f"  }});\n"
        f"}});\n"
    )
    css = (
        f".{slug} {{\n"
        f"  /* {name} styles */\n"
        f"}}\n"
    )
    return (
        ScaffoldFile(path=f"{name}/{name}.{ext}", content=component),
        ScaffoldFile(path=f"{name}/{name}.test.{ext}", content=test),
        ScaffoldFile(path=f"{name}/{name}.css", content=css),
    )


_COMPONENT_GENERATORS = {
    "react": _component_react,
    "vue": _component_vue,
    "vanilla": _component_vanilla,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def scaffold_wordpress_template(
    template_type: str,
    name: str,
    options: dict[str, Any] | None = None,
) -> ScaffoldResult:
    """Scaffold a WordPress Full Site Editing template.

    Args:
        template_type: One of "page", "archive", "single", "template-part",
                       "block-pattern".
        name: Human-readable template name (will be slugified for paths).
        options: Optional dict with extra settings (title, description, etc.).

    Returns:
        Frozen ScaffoldResult with generated files and metadata.

    Raises:
        ScaffoldError: If template_type is not supported.
        ValueError: If name is empty.
    """
    clean_name = _validate_name(name)
    safe_options = options if options is not None else {}

    if template_type not in _WP_TEMPLATE_TYPES:
        raise ScaffoldError(
            f"Invalid template_type '{template_type}'. "
            f"Supported: {sorted(_WP_TEMPLATE_TYPES)}"
        )

    slug = _slugify(clean_name)
    generator = _WP_GENERATORS[template_type]
    files = generator(clean_name, slug, safe_options)

    return ScaffoldResult(
        platform="wordpress",
        template_type=template_type,
        name=clean_name,
        files=files,
        metadata={
            "fse_compatible": True,
            "slug": slug,
            "template_type": template_type,
        },
    )


def scaffold_shopify_template(
    template_type: str,
    name: str,
    options: dict[str, Any] | None = None,
) -> ScaffoldResult:
    """Scaffold a Shopify Online Store 2.0 template.

    Args:
        template_type: One of "page", "collection", "product", "section",
                       "snippet".
        name: Human-readable template name (will be slugified for paths).
        options: Optional dict with extra settings (title, description, etc.).

    Returns:
        Frozen ScaffoldResult with generated files and metadata.

    Raises:
        ScaffoldError: If template_type is not supported.
        ValueError: If name is empty.
    """
    clean_name = _validate_name(name)
    safe_options = options if options is not None else {}

    if template_type not in _SHOPIFY_TEMPLATE_TYPES:
        raise ScaffoldError(
            f"Invalid template_type '{template_type}'. "
            f"Supported: {sorted(_SHOPIFY_TEMPLATE_TYPES)}"
        )

    slug = _slugify(clean_name)
    generator = _SHOPIFY_GENERATORS[template_type]
    files = generator(clean_name, slug, safe_options)

    return ScaffoldResult(
        platform="shopify",
        template_type=template_type,
        name=clean_name,
        files=files,
        metadata={
            "online_store_version": "2.0",
            "slug": slug,
            "template_type": template_type,
        },
    )


def scaffold_component(
    framework: str,
    component_name: str,
    options: dict[str, Any] | None = None,
) -> ScaffoldResult:
    """Scaffold a frontend component with test and styles.

    Args:
        framework: One of "react", "vue", "vanilla".
        component_name: PascalCase component name (preserved in code).
        options: Optional dict (e.g., {"typescript": True} for vanilla).

    Returns:
        Frozen ScaffoldResult with component, test, and style files.

    Raises:
        ScaffoldError: If framework is not supported.
        ValueError: If component_name is empty.
    """
    clean_name = _validate_name(component_name, label="component_name")
    safe_options = options if options is not None else {}

    if framework not in _COMPONENT_FRAMEWORKS:
        raise ScaffoldError(
            f"Invalid framework '{framework}'. "
            f"Supported: {sorted(_COMPONENT_FRAMEWORKS)}"
        )

    slug = _slugify(clean_name)
    generator = _COMPONENT_GENERATORS[framework]
    files = generator(clean_name, slug, safe_options)

    return ScaffoldResult(
        platform=framework,
        template_type="component",
        name=clean_name,
        files=files,
        metadata={
            "framework": framework,
            "component_name": clean_name,
        },
    )


def list_templates() -> dict[str, list[dict[str, str]]]:
    """Return catalog of available template types and descriptions.

    Returns:
        Dict keyed by platform ("wordpress", "shopify", "component"),
        each containing a list of {"type": ..., "description": ...}.
    """
    return {
        "wordpress": [
            {"type": "page", "description": "FSE page template with block pattern JSON"},
            {"type": "archive", "description": "FSE archive template with query loop"},
            {"type": "single", "description": "FSE single post/CPT template"},
            {"type": "template-part", "description": "Reusable template part (header, footer, sidebar)"},
            {"type": "block-pattern", "description": "Block pattern with PHP registration"},
        ],
        "shopify": [
            {"type": "page", "description": "Online Store 2.0 page JSON template"},
            {"type": "collection", "description": "Online Store 2.0 collection JSON template"},
            {"type": "product", "description": "Online Store 2.0 product JSON template"},
            {"type": "section", "description": "Liquid section with schema block"},
            {"type": "snippet", "description": "Reusable Liquid snippet"},
        ],
        "component": [
            {"type": "react", "description": "React TSX component with test and CSS module"},
            {"type": "vue", "description": "Vue SFC component with test and CSS module"},
            {"type": "vanilla", "description": "Vanilla JS/TS component with test and CSS"},
        ],
    }

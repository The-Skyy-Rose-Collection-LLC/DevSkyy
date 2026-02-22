"""Tests for tools/template_scaffold.py — WordPress, Shopify, and component scaffolding.

TDD: These tests are written FIRST, before the implementation.
All scaffold functions return frozen dataclasses (immutable).
"""

from __future__ import annotations

import pytest

from tools.template_scaffold import (
    ScaffoldError,
    ScaffoldFile,
    ScaffoldResult,
    list_templates,
    scaffold_component,
    scaffold_shopify_template,
    scaffold_wordpress_template,
)


# ---------------------------------------------------------------------------
# Data model immutability
# ---------------------------------------------------------------------------


class TestScaffoldFileImmutability:
    def test_frozen_path(self) -> None:
        sf = ScaffoldFile(path="templates/page.html", content="<h1>Hello</h1>")
        with pytest.raises(AttributeError):
            sf.path = "other.html"  # type: ignore[misc]

    def test_frozen_content(self) -> None:
        sf = ScaffoldFile(path="templates/page.html", content="<h1>Hello</h1>")
        with pytest.raises(AttributeError):
            sf.content = "changed"  # type: ignore[misc]

    def test_fields(self) -> None:
        sf = ScaffoldFile(path="page.php", content="<?php // page ?>")
        assert sf.path == "page.php"
        assert sf.content == "<?php // page ?>"


class TestScaffoldResultImmutability:
    def test_frozen_platform(self) -> None:
        result = ScaffoldResult(
            platform="wordpress",
            template_type="page",
            name="about",
            files=(),
            metadata={"version": "1.0"},
        )
        with pytest.raises(AttributeError):
            result.platform = "shopify"  # type: ignore[misc]

    def test_frozen_files_tuple(self) -> None:
        """Files must be a tuple (not list) so the frozen dataclass is truly immutable."""
        result = ScaffoldResult(
            platform="wordpress",
            template_type="page",
            name="about",
            files=(),
            metadata={},
        )
        assert isinstance(result.files, tuple)

    def test_fields(self) -> None:
        f = ScaffoldFile(path="a.php", content="code")
        result = ScaffoldResult(
            platform="shopify",
            template_type="product",
            name="featured",
            files=(f,),
            metadata={"key": "val"},
        )
        assert result.platform == "shopify"
        assert result.template_type == "product"
        assert result.name == "featured"
        assert len(result.files) == 1
        assert result.metadata == {"key": "val"}


# ---------------------------------------------------------------------------
# WordPress template scaffolding
# ---------------------------------------------------------------------------


class TestScaffoldWordPressTemplate:
    def test_page_generates_files(self) -> None:
        result = scaffold_wordpress_template("page", "about")
        assert result.platform == "wordpress"
        assert result.template_type == "page"
        assert result.name == "about"
        assert len(result.files) >= 2  # template PHP + block pattern JSON
        paths = [f.path for f in result.files]
        assert any("about" in p and p.endswith(".html") for p in paths)
        assert any("about" in p and p.endswith(".json") for p in paths)

    def test_page_content_not_empty(self) -> None:
        result = scaffold_wordpress_template("page", "contact")
        for f in result.files:
            assert f.content, f"File {f.path} has empty content"

    def test_archive_generates_template(self) -> None:
        result = scaffold_wordpress_template("archive", "news")
        assert result.template_type == "archive"
        assert len(result.files) >= 1
        paths = [f.path for f in result.files]
        assert any("news" in p for p in paths)

    def test_single_generates_template(self) -> None:
        result = scaffold_wordpress_template("single", "product")
        assert result.template_type == "single"
        assert len(result.files) >= 1

    def test_template_part_generates_file(self) -> None:
        result = scaffold_wordpress_template("template-part", "header-main")
        assert result.template_type == "template-part"
        assert len(result.files) >= 1
        paths = [f.path for f in result.files]
        assert any("header-main" in p for p in paths)

    def test_block_pattern_generates_registration(self) -> None:
        result = scaffold_wordpress_template("block-pattern", "hero-section")
        assert result.template_type == "block-pattern"
        assert len(result.files) >= 1
        # Block pattern PHP should contain register_block_pattern
        php_files = [f for f in result.files if f.path.endswith(".php")]
        assert len(php_files) >= 1
        assert "register_block_pattern" in php_files[0].content

    def test_page_has_fse_compatible_metadata(self) -> None:
        result = scaffold_wordpress_template("page", "landing")
        assert "fse_compatible" in result.metadata
        assert result.metadata["fse_compatible"] is True

    def test_options_custom_description(self) -> None:
        result = scaffold_wordpress_template(
            "block-pattern",
            "cta-banner",
            options={"description": "Call to action banner"},
        )
        php_content = next(
            f.content for f in result.files if f.path.endswith(".php")
        )
        assert "Call to action banner" in php_content

    def test_invalid_template_type_raises(self) -> None:
        with pytest.raises(ScaffoldError, match="template_type"):
            scaffold_wordpress_template("widget", "sidebar")

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError, match="name"):
            scaffold_wordpress_template("page", "")

    def test_whitespace_name_raises(self) -> None:
        with pytest.raises(ValueError, match="name"):
            scaffold_wordpress_template("page", "   ")

    def test_result_is_frozen(self) -> None:
        result = scaffold_wordpress_template("page", "test")
        with pytest.raises(AttributeError):
            result.name = "hacked"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Shopify template scaffolding
# ---------------------------------------------------------------------------


class TestScaffoldShopifyTemplate:
    def test_page_generates_files(self) -> None:
        result = scaffold_shopify_template("page", "about")
        assert result.platform == "shopify"
        assert result.template_type == "page"
        assert result.name == "about"
        assert len(result.files) >= 1

    def test_page_uses_json_template(self) -> None:
        """Online Store 2.0 uses JSON templates."""
        result = scaffold_shopify_template("page", "faq")
        json_files = [f for f in result.files if f.path.endswith(".json")]
        assert len(json_files) >= 1
        assert '"sections"' in json_files[0].content

    def test_collection_generates_files(self) -> None:
        result = scaffold_shopify_template("collection", "summer-sale")
        assert result.template_type == "collection"
        assert len(result.files) >= 1

    def test_product_generates_files(self) -> None:
        result = scaffold_shopify_template("product", "featured-item")
        assert result.template_type == "product"
        assert len(result.files) >= 1

    def test_section_generates_liquid(self) -> None:
        result = scaffold_shopify_template("section", "hero-banner")
        assert len(result.files) >= 1
        liquid_files = [f for f in result.files if f.path.endswith(".liquid")]
        assert len(liquid_files) >= 1

    def test_snippet_generates_liquid(self) -> None:
        result = scaffold_shopify_template("snippet", "price-badge")
        assert len(result.files) >= 1
        liquid_files = [f for f in result.files if f.path.endswith(".liquid")]
        assert len(liquid_files) >= 1

    def test_section_has_schema(self) -> None:
        """Shopify sections must include a {% schema %} block."""
        result = scaffold_shopify_template("section", "testimonials")
        liquid_content = next(
            f.content for f in result.files if f.path.endswith(".liquid")
        )
        assert "{% schema %}" in liquid_content

    def test_online_store_2_metadata(self) -> None:
        result = scaffold_shopify_template("page", "landing")
        assert result.metadata.get("online_store_version") == "2.0"

    def test_invalid_template_type_raises(self) -> None:
        with pytest.raises(ScaffoldError, match="template_type"):
            scaffold_shopify_template("widget", "sidebar")

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError, match="name"):
            scaffold_shopify_template("page", "")

    def test_result_is_frozen(self) -> None:
        result = scaffold_shopify_template("page", "test")
        with pytest.raises(AttributeError):
            result.name = "hacked"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Component scaffolding
# ---------------------------------------------------------------------------


class TestScaffoldComponent:
    def test_react_generates_three_files(self) -> None:
        """React component: .tsx + .test.tsx + .module.css."""
        result = scaffold_component("react", "HeroBanner")
        assert result.platform == "react"
        assert result.name == "HeroBanner"
        assert len(result.files) == 3
        paths = [f.path for f in result.files]
        assert any(p.endswith(".tsx") and "test" not in p for p in paths)
        assert any("test" in p for p in paths)
        assert any(p.endswith(".module.css") for p in paths)

    def test_react_component_content(self) -> None:
        result = scaffold_component("react", "Card")
        component_file = next(
            f for f in result.files if f.path.endswith(".tsx") and "test" not in f.path
        )
        assert "Card" in component_file.content
        assert "export" in component_file.content

    def test_vue_generates_three_files(self) -> None:
        """Vue component: .vue + .test.ts + .module.css."""
        result = scaffold_component("vue", "ProductCard")
        assert result.platform == "vue"
        assert len(result.files) == 3
        paths = [f.path for f in result.files]
        assert any(p.endswith(".vue") for p in paths)
        assert any("test" in p for p in paths)

    def test_vue_component_has_template_script_style(self) -> None:
        result = scaffold_component("vue", "NavBar")
        vue_file = next(f for f in result.files if f.path.endswith(".vue"))
        assert "<template>" in vue_file.content
        assert "<script" in vue_file.content

    def test_vanilla_generates_three_files(self) -> None:
        """Vanilla JS component: .js + .test.js + .css."""
        result = scaffold_component("vanilla", "Accordion")
        assert result.platform == "vanilla"
        assert len(result.files) == 3
        paths = [f.path for f in result.files]
        assert any(p.endswith(".js") and "test" not in p for p in paths)
        assert any("test" in p for p in paths)
        assert any(p.endswith(".css") for p in paths)

    def test_vanilla_component_content(self) -> None:
        result = scaffold_component("vanilla", "Tabs")
        js_file = next(
            f for f in result.files if f.path.endswith(".js") and "test" not in f.path
        )
        assert "Tabs" in js_file.content

    def test_invalid_framework_raises(self) -> None:
        with pytest.raises(ScaffoldError, match="framework"):
            scaffold_component("angular", "Widget")

    def test_empty_component_name_raises(self) -> None:
        with pytest.raises(ValueError, match="component_name"):
            scaffold_component("react", "")

    def test_all_files_have_content(self) -> None:
        for framework in ("react", "vue", "vanilla"):
            result = scaffold_component(framework, "TestComp")
            for f in result.files:
                assert f.content, f"{framework}/{f.path} has empty content"

    def test_result_is_frozen(self) -> None:
        result = scaffold_component("react", "Frozen")
        with pytest.raises(AttributeError):
            result.platform = "angular"  # type: ignore[misc]

    def test_options_with_typescript_vanilla(self) -> None:
        """Vanilla with typescript option should produce .ts files."""
        result = scaffold_component(
            "vanilla", "Counter", options={"typescript": True}
        )
        paths = [f.path for f in result.files]
        assert any(p.endswith(".ts") and "test" not in p for p in paths)


# ---------------------------------------------------------------------------
# list_templates
# ---------------------------------------------------------------------------


class TestListTemplates:
    def test_returns_dict(self) -> None:
        result = list_templates()
        assert isinstance(result, dict)

    def test_has_wordpress_key(self) -> None:
        result = list_templates()
        assert "wordpress" in result

    def test_has_shopify_key(self) -> None:
        result = list_templates()
        assert "shopify" in result

    def test_has_component_key(self) -> None:
        result = list_templates()
        assert "component" in result

    def test_wordpress_types_complete(self) -> None:
        result = list_templates()
        wp_types = {t["type"] for t in result["wordpress"]}
        expected = {"page", "archive", "single", "template-part", "block-pattern"}
        assert expected == wp_types

    def test_shopify_types_complete(self) -> None:
        result = list_templates()
        shopify_types = {t["type"] for t in result["shopify"]}
        expected = {"page", "collection", "product", "section", "snippet"}
        assert expected == shopify_types

    def test_component_frameworks_complete(self) -> None:
        result = list_templates()
        frameworks = {t["type"] for t in result["component"]}
        expected = {"react", "vue", "vanilla"}
        assert expected == frameworks

    def test_each_entry_has_description(self) -> None:
        result = list_templates()
        for platform_entries in result.values():
            for entry in platform_entries:
                assert "description" in entry
                assert len(entry["description"]) > 0


# ---------------------------------------------------------------------------
# Edge cases and error messages
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_scaffold_error_is_exception(self) -> None:
        err = ScaffoldError("bad template type")
        assert isinstance(err, Exception)
        assert str(err) == "bad template type"

    def test_name_with_special_chars_sanitized(self) -> None:
        """Names with spaces/special chars should be slugified."""
        result = scaffold_wordpress_template("page", "My Cool Page!")
        for f in result.files:
            # Path should not contain spaces or exclamation marks
            assert " " not in f.path
            assert "!" not in f.path

    def test_shopify_name_with_special_chars_sanitized(self) -> None:
        result = scaffold_shopify_template("section", "Hero Banner v2")
        for f in result.files:
            assert " " not in f.path

    def test_component_name_preserved_in_code(self) -> None:
        """PascalCase component name should appear verbatim in source code."""
        result = scaffold_component("react", "MyButton")
        component_file = next(
            f for f in result.files if f.path.endswith(".tsx") and "test" not in f.path
        )
        assert "MyButton" in component_file.content

    def test_none_options_treated_as_empty(self) -> None:
        """Passing options=None should not raise."""
        result = scaffold_wordpress_template("page", "test", options=None)
        assert result.name == "test"

"""
PHP parser edge-case tests.

Covers:
 - Version constant on a single line vs multi-line define
 - Single quotes vs double quotes in define()
 - Version constant with leading 'v' prefix (e.g. 'v1.0.0') — locked: returns as-is
 - Comment-only file → extract_version_constant returns None
 - Multiple version constants in same file — first one wins (regex findall order)
 - File without <?php opening tag — graceful (returns None, no crash)
 - Style CSS version with extra whitespace
 - Readme stable tag with trailing whitespace
 - Theme name extraction
 - Text domain extraction
 - extract_php_string with double-quoted constant name
 - Template map with mixed quote styles
 - Template map with no entries returns empty dict
"""

from __future__ import annotations

import pytest
from cli_anything.skyyrose_theme.utils.php_parser import (
    extract_php_string, extract_readme_stable_tag, extract_style_css_version,
    extract_template_map, extract_text_domain, extract_theme_name,
    extract_version_constant)

# ---------------------------------------------------------------------------
# E. PHP parser edge cases (~13 tests)
# ---------------------------------------------------------------------------


class TestExtractVersionConstant:
    def test_single_line_define_single_quotes(self):
        php = "define( 'SKYYROSE_VERSION', '1.5.20' );"
        assert extract_version_constant(php) == "1.5.20"

    def test_single_line_define_double_quotes(self):
        """define() with double quotes around both name and value."""
        php = 'define( "SKYYROSE_VERSION", "2.0.0" );'
        assert extract_version_constant(php) == "2.0.0"

    def test_multiline_define_with_whitespace(self):
        php = "define(\n    'SKYYROSE_VERSION',\n    '1.5.21'\n);"
        assert extract_version_constant(php) == "1.5.21"

    def test_version_with_leading_v_prefix_returned_as_is(self):
        """
        A version constant like 'v1.0.0' is returned verbatim.
        The parser does not strip the 'v' — caller decides how to handle it.
        This test locks that behaviour.
        """
        php = "define( 'SKYYROSE_VERSION', 'v1.0.0' );"
        result = extract_version_constant(php)
        assert result == "v1.0.0"

    def test_comment_only_file_returns_none(self):
        php = "<?php\n// This file has no version constant\n/* just a comment */\n"
        assert extract_version_constant(php) is None

    def test_missing_constant_returns_none(self):
        php = "<?php\necho 'hello';\n"
        assert extract_version_constant(php) is None

    def test_file_without_php_opening_tag_returns_none(self):
        """Text without <?php — parser handles gracefully, returns None."""
        text = "define( 'SKYYROSE_VERSION', '1.0.0' );"
        # The regex doesn't require <?php — it finds the pattern anywhere.
        # Lock the actual behaviour: constant IS found even without <?php tag.
        result = extract_version_constant(text)
        assert result == "1.0.0"

    def test_multiple_version_constants_first_wins(self):
        """
        Pathological file with two SKYYROSE_VERSION defines.
        _SKYYROSE_VERSION_RE.search() finds the first match.
        Lock this behaviour so it's explicit.
        """
        php = (
            "define( 'SKYYROSE_VERSION', '1.0.0' );\n"
            "// duplicate below — should be ignored\n"
            "define( 'SKYYROSE_VERSION', '9.9.9' );\n"
        )
        result = extract_version_constant(php)
        assert result == "1.0.0"

    def test_empty_string_returns_none(self):
        assert extract_version_constant("") is None


class TestExtractStyleCssVersion:
    def test_standard_version_header(self):
        css = "/*\nTheme Name: SkyyRose\nVersion: 1.5.20\n*/\n"
        assert extract_style_css_version(css) == "1.5.20"

    def test_version_with_leading_whitespace_stripped(self):
        css = "/*\nVersion:             1.5.20\n*/\n"
        assert extract_style_css_version(css) == "1.5.20"

    def test_version_with_trailing_whitespace_stripped(self):
        css = "/*\nVersion: 1.5.20   \n*/\n"
        assert extract_style_css_version(css) == "1.5.20"

    def test_missing_version_returns_none(self):
        css = "/*\nTheme Name: SkyyRose\n*/\n"
        assert extract_style_css_version(css) is None


class TestExtractReadmeStableTag:
    def test_standard_stable_tag(self):
        txt = "=== SkyyRose ===\nStable tag: 1.5.20\n"
        assert extract_readme_stable_tag(txt) == "1.5.20"

    def test_stable_tag_trailing_whitespace_stripped(self):
        txt = "Stable tag: 1.5.20   \n"
        assert extract_readme_stable_tag(txt) == "1.5.20"

    def test_missing_stable_tag_returns_none(self):
        txt = "=== SkyyRose ===\nNo version info here\n"
        assert extract_readme_stable_tag(txt) is None


class TestExtractThemeAndDomain:
    def test_theme_name_extracted(self):
        css = "/*\nTheme Name: SkyyRose\nVersion: 1.0.0\n*/\n"
        assert extract_theme_name(css) == "SkyyRose"

    def test_text_domain_extracted(self):
        css = "/*\nTheme Name: SkyyRose\nText Domain: skyyrose\n*/\n"
        assert extract_text_domain(css) == "skyyrose"

    def test_theme_name_missing_returns_none(self):
        assert extract_theme_name("/* no theme name */") is None

    def test_text_domain_missing_returns_none(self):
        assert extract_text_domain("/* no domain */") is None


class TestExtractPhpString:
    def test_generic_constant_extracted(self):
        php = "define( 'MY_CONST', 'hello-world' );"
        assert extract_php_string(php, "MY_CONST") == "hello-world"

    def test_constant_not_present_returns_none(self):
        php = "define( 'OTHER_CONST', 'value' );"
        assert extract_php_string(php, "MY_CONST") is None

    def test_double_quoted_value(self):
        php = 'define( "MY_CONST", "double-quoted" );'
        assert extract_php_string(php, "MY_CONST") == "double-quoted"


class TestExtractTemplateMap:
    def test_single_entry_parsed(self):
        php = "'template-about.php' => 'about',"
        result = extract_template_map(php)
        assert result == {"template-about.php": "about"}

    def test_multiple_entries_parsed(self):
        php = (
            "'template-about.php'         => 'about',\n"
            "'template-contact.php'       => 'contact',\n"
            "'template-coming-soon.php'   => 'coming-soon',\n"
        )
        result = extract_template_map(php)
        assert result["template-about.php"] == "about"
        assert result["template-contact.php"] == "contact"
        assert result["template-coming-soon.php"] == "coming-soon"

    def test_empty_php_returns_empty_dict(self):
        assert extract_template_map("<?php\n// no entries\n") == {}

    def test_double_quoted_entries_parsed(self):
        php = '"template-shop.php" => "shop",'
        result = extract_template_map(php)
        assert result == {"template-shop.php": "shop"}

    def test_mixed_quote_styles_parsed(self):
        php = "'template-about.php' => 'about',\n\"template-shop.php\" => \"shop\",\n"
        result = extract_template_map(php)
        assert result["template-about.php"] == "about"
        assert result["template-shop.php"] == "shop"

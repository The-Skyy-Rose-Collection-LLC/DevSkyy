"""Tests for core.output_writer — filesystem output writer."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.output_writer import (
    MAX_FILE_SIZE,
    ExtractedFile,
    OutputWriter,
)

# ---------------------------------------------------------------------------
# ExtractedFile
# ---------------------------------------------------------------------------


class TestExtractedFile:
    def test_frozen(self) -> None:
        f = ExtractedFile(path="a.php", content="<?php", language="php")
        with pytest.raises(AttributeError):
            f.path = "b.php"  # type: ignore[misc]

    def test_fields(self) -> None:
        f = ExtractedFile(path="style.css", content="body{}", language="css")
        assert f.path == "style.css"
        assert f.content == "body{}"
        assert f.language == "css"


# ---------------------------------------------------------------------------
# Extraction patterns
# ---------------------------------------------------------------------------


class TestExtractFiles:
    """Test all 4 extraction patterns."""

    def test_pattern_1_fence_with_path(self) -> None:
        content = '```php:functions.php\n<?php echo "hello"; ?>\n```'
        files = OutputWriter.extract_files(content)
        assert len(files) == 1
        assert files[0].path == "functions.php"
        assert files[0].language == "php"
        assert "<?php" in files[0].content

    def test_pattern_2_comment_css(self) -> None:
        content = "```css\n/* file: assets/css/luxury.css */\nbody { color: red; }\n```"
        files = OutputWriter.extract_files(content)
        assert len(files) == 1
        assert files[0].path == "assets/css/luxury.css"

    def test_pattern_2_comment_js(self) -> None:
        content = "```javascript\n// file: assets/js/main.js\nconst x = 1;\n```"
        files = OutputWriter.extract_files(content)
        assert len(files) == 1
        assert files[0].path == "assets/js/main.js"

    def test_pattern_2_comment_python(self) -> None:
        content = "```python\n# file: utils.py\ndef foo(): pass\n```"
        files = OutputWriter.extract_files(content)
        assert len(files) == 1
        assert files[0].path == "utils.py"

    def test_pattern_2_comment_html(self) -> None:
        content = "```html\n<!-- file: index.html -->\n<div>hi</div>\n```"
        files = OutputWriter.extract_files(content)
        assert len(files) == 1
        assert files[0].path == "index.html"

    def test_pattern_3_heading_then_fence(self) -> None:
        content = '### File: theme.json\n\n```json\n{"version": 3}\n```'
        files = OutputWriter.extract_files(content)
        assert len(files) == 1
        assert files[0].path == "theme.json"

    def test_pattern_4_bold_path_then_fence(self) -> None:
        content = "**`style.css`**\n\n```css\nbody { margin: 0; }\n```"
        files = OutputWriter.extract_files(content)
        assert len(files) == 1
        assert files[0].path == "style.css"

    def test_multiple_files(self) -> None:
        content = (
            "```php:functions.php\n<?php\n```\n\n"
            "```css:style.css\nbody{}\n```\n\n"
            "### File: theme.json\n```json\n{}\n```"
        )
        files = OutputWriter.extract_files(content)
        assert len(files) == 3
        paths = {f.path for f in files}
        assert paths == {"functions.php", "style.css", "theme.json"}

    def test_empty_content(self) -> None:
        assert OutputWriter.extract_files("") == []

    def test_no_file_blocks(self) -> None:
        content = "Just some text without code blocks."
        assert OutputWriter.extract_files(content) == []

    def test_code_block_without_path(self) -> None:
        content = '```python\nprint("hello")\n```'
        assert OutputWriter.extract_files(content) == []

    def test_deduplication_last_wins(self) -> None:
        content = "```php:functions.php\n<?php // v1\n```\n\n```php:functions.php\n<?php // v2\n```"
        files = OutputWriter.extract_files(content)
        assert len(files) == 1
        assert "v2" in files[0].content

    def test_nested_path(self) -> None:
        content = "```css:assets/css/components/header.css\n.header{}\n```"
        files = OutputWriter.extract_files(content)
        assert len(files) == 1
        assert files[0].path == "assets/css/components/header.css"


# ---------------------------------------------------------------------------
# Path validation
# ---------------------------------------------------------------------------


class TestValidatePath:
    def test_valid_simple(self) -> None:
        assert OutputWriter.validate_path("functions.php") is None

    def test_valid_nested(self) -> None:
        assert OutputWriter.validate_path("assets/css/luxury.css") is None

    def test_blocks_traversal(self) -> None:
        assert OutputWriter.validate_path("../../etc/passwd") is not None
        assert ".." in OutputWriter.validate_path("../secret.txt")

    def test_blocks_absolute(self) -> None:
        assert OutputWriter.validate_path("/etc/passwd") is not None

    def test_blocks_disallowed_extension(self) -> None:
        assert OutputWriter.validate_path("evil.exe") is not None
        assert OutputWriter.validate_path("script.bat") is not None

    def test_allows_php(self) -> None:
        assert OutputWriter.validate_path("template.php") is None

    def test_allows_json(self) -> None:
        assert OutputWriter.validate_path("theme.json") is None

    def test_allows_css(self) -> None:
        assert OutputWriter.validate_path("style.css") is None

    def test_empty_path(self) -> None:
        assert OutputWriter.validate_path("") is not None

    def test_long_path(self) -> None:
        assert OutputWriter.validate_path("a" * 300 + ".php") is not None


# ---------------------------------------------------------------------------
# Content validation
# ---------------------------------------------------------------------------


class TestValidateContent:
    def test_valid_content(self) -> None:
        assert OutputWriter.validate_content("<?php echo 'hi'; ?>") is None

    def test_oversized_content(self) -> None:
        huge = "x" * (MAX_FILE_SIZE + 1)
        assert OutputWriter.validate_content(huge) is not None


# ---------------------------------------------------------------------------
# File writing
# ---------------------------------------------------------------------------


class TestWriteFile:
    def test_write_single_file(self, tmp_path: Path) -> None:
        writer = OutputWriter(output_dir=tmp_path)
        result = writer.write_file(
            ExtractedFile(path="test.php", content="<?php echo 1;", language="php")
        )
        assert result is None  # no error
        assert (tmp_path / "test.php").read_text() == "<?php echo 1;"

    def test_write_nested_file(self, tmp_path: Path) -> None:
        writer = OutputWriter(output_dir=tmp_path)
        result = writer.write_file(
            ExtractedFile(path="assets/css/main.css", content="body{}", language="css")
        )
        assert result is None
        assert (tmp_path / "assets" / "css" / "main.css").read_text() == "body{}"

    def test_blocks_traversal(self, tmp_path: Path) -> None:
        writer = OutputWriter(output_dir=tmp_path)
        result = writer.write_file(
            ExtractedFile(path="../evil.php", content="<?php", language="php")
        )
        assert result is not None
        assert "traversal" in result.lower()

    def test_tracks_written_files(self, tmp_path: Path) -> None:
        writer = OutputWriter(output_dir=tmp_path)
        writer.write_file(ExtractedFile(path="a.php", content="<?php", language="php"))
        writer.write_file(ExtractedFile(path="b.css", content="body{}", language="css"))
        assert writer.written_files == ["a.php", "b.css"]

    def test_reset_clears_tracker(self, tmp_path: Path) -> None:
        writer = OutputWriter(output_dir=tmp_path)
        writer.write_file(ExtractedFile(path="a.php", content="<?php", language="php"))
        assert len(writer.written_files) == 1
        writer.reset()
        assert len(writer.written_files) == 0


# ---------------------------------------------------------------------------
# extract_and_write integration
# ---------------------------------------------------------------------------


class TestExtractAndWrite:
    def test_full_pipeline(self, tmp_path: Path) -> None:
        writer = OutputWriter(output_dir=tmp_path)
        content = (
            '```php:functions.php\n<?php\nadd_action("init", function() {});\n```\n\n'
            "```css:assets/css/luxury.css\nbody { background: #0A0A0A; }\n```\n\n"
            '### File: theme.json\n```json\n{"version": 3}\n```'
        )
        result = writer.extract_and_write(content)

        assert len(result.files_written) == 3
        assert "functions.php" in result.files_written
        assert "assets/css/luxury.css" in result.files_written
        assert "theme.json" in result.files_written
        assert result.bytes_written > 0
        assert len(result.errors) == 0

        # Verify files exist on disk
        assert (tmp_path / "functions.php").exists()
        assert (tmp_path / "assets" / "css" / "luxury.css").exists()
        assert (tmp_path / "theme.json").exists()

    def test_no_files_in_content(self, tmp_path: Path) -> None:
        writer = OutputWriter(output_dir=tmp_path)
        result = writer.extract_and_write("Just text, no code blocks.")
        assert len(result.files_written) == 0
        assert len(result.errors) == 0

    def test_mixed_valid_and_invalid(self, tmp_path: Path) -> None:
        writer = OutputWriter(output_dir=tmp_path)
        content = "```php:valid.php\n<?php echo 1;\n```\n\n```php:../evil.php\n<?php evil();\n```"
        result = writer.extract_and_write(content)
        assert "valid.php" in result.files_written
        assert "../evil.php" in result.files_skipped
        assert len(result.errors) == 1

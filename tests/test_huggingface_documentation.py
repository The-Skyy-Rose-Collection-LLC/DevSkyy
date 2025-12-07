"""
Unit Tests for HuggingFace Best Practices Documentation
Validates the structure, content, and quality of the documentation
"""

from pathlib import Path
import re
from urllib.parse import urlparse

import pytest


class TestDocumentationStructure:
    """Test the overall structure of the documentation"""

    @pytest.fixture
    def doc_path(self):
        """Get path to the documentation file"""
        return Path(__file__).parent.parent / "docs" / "HUGGINGFACE_BEST_PRACTICES.md"

    @pytest.fixture
    def doc_content(self, doc_path):
        """Read documentation content"""
        with open(doc_path, "r", encoding="utf-8") as f:
            return f.read()

    @pytest.fixture
    def doc_lines(self, doc_content):
        """Get documentation lines"""
        return doc_content.split("\n")

    def test_documentation_exists(self, doc_path):
        """Test that the documentation file exists"""
        assert doc_path.exists(), "Documentation file should exist"
        assert doc_path.is_file(), "Documentation should be a file"

    def test_documentation_not_empty(self, doc_content):
        """Test that documentation is not empty"""
        assert len(doc_content.strip()) > 0, "Documentation should not be empty"
        assert len(doc_content) > 1000, "Documentation should be substantial (>1000 chars)"

    def test_documentation_has_title(self, doc_lines):
        """Test that documentation has a proper title"""
        assert doc_lines[0].startswith("# "), "First line should be a level-1 header"
        assert "HuggingFace" in doc_lines[0], "Title should mention HuggingFace"
        assert "DevSkyy" in doc_lines[0], "Title should mention DevSkyy"

    def test_documentation_has_metadata(self, doc_content):
        """Test that documentation has metadata section"""
        metadata_fields = ["Version:", "Last Updated:", "Target:", "Status:"]
        for field in metadata_fields:
            assert field in doc_content, f"Metadata field '{field}' should be present"

    def test_documentation_has_table_of_contents(self, doc_content):
        """Test that documentation has a table of contents"""
        assert "## Table of Contents" in doc_content, "Should have table of contents"
        assert "[Overview](#overview)" in doc_content, "TOC should have links"

    def test_documentation_has_required_sections(self, doc_content):
        """Test that all required sections are present"""
        required_sections = [
            "## Overview",
            "## Memory Optimization Techniques",
            "## Performance Optimization",
            "## Production Deployment",
            "## Troubleshooting",
            "## References",
        ]
        for section in required_sections:
            assert section in doc_content, f"Required section '{section}' should be present"

    def test_section_count(self, doc_content):
        """Test that documentation has appropriate number of sections"""
        level2_headers = re.findall(r"^## ", doc_content, re.MULTILINE)
        assert len(level2_headers) >= 10, "Should have at least 10 major sections"

    def test_documentation_length(self, doc_lines):
        """Test that documentation is comprehensive"""
        assert len(doc_lines) > 1000, "Documentation should be at least 1000 lines"


class TestCodeBlocks:
    """Test code blocks in the documentation"""

    @pytest.fixture
    def doc_content(self):
        """Read documentation content"""
        doc_path = Path(__file__).parent.parent / "docs" / "HUGGINGFACE_BEST_PRACTICES.md"
        with open(doc_path, "r", encoding="utf-8") as f:
            return f.read()

    @pytest.fixture
    def code_blocks(self, doc_content):
        """Extract all code blocks"""
        pattern = r"```(\w+)?\n(.*?)```"
        matches = re.findall(pattern, doc_content, re.DOTALL)
        return matches

    @pytest.fixture
    def python_code_blocks(self, code_blocks):
        """Extract Python code blocks"""
        return [code for lang, code in code_blocks if lang == "python"]

    def test_has_code_blocks(self, code_blocks):
        """Test that documentation has code blocks"""
        assert len(code_blocks) > 20, "Should have substantial code examples (>20)"

    def test_has_python_code_blocks(self, python_code_blocks):
        """Test that documentation has Python code blocks"""
        assert len(python_code_blocks) > 15, "Should have many Python examples (>15)"

    def test_python_code_blocks_not_empty(self, python_code_blocks):
        """Test that Python code blocks are not empty"""
        for i, code in enumerate(python_code_blocks):
            assert len(code.strip()) > 0, f"Python code block {i} should not be empty"

    def test_python_imports_present(self, python_code_blocks):
        """Test that Python code blocks have proper imports"""
        all_code = "\n".join(python_code_blocks)
        expected_imports = [
            "from diffusers import",
            "import torch",
        ]
        for imp in expected_imports:
            assert imp in all_code, f"Import '{imp}' should be present in code examples"

    def test_code_blocks_have_comments(self, python_code_blocks):
        """Test that code blocks have explanatory comments"""
        codes_with_comments = [code for code in python_code_blocks if "#" in code]
        assert (
            len(codes_with_comments) > len(python_code_blocks) * 0.5
        ), "Most code blocks should have explanatory comments"

    def test_optimization_techniques_shown(self, python_code_blocks):
        """Test that code blocks show optimization techniques"""
        all_code = "\n".join(python_code_blocks)
        optimizations = [
            "enable_vae_slicing",
            "enable_attention_slicing",
            "enable_sequential_cpu_offload",
        ]
        found = [opt for opt in optimizations if opt in all_code]
        assert len(found) >= 2, "Should demonstrate multiple optimization techniques"


class TestRequirements:
    """Test requirements and dependencies section"""

    @pytest.fixture
    def doc_content(self):
        """Read documentation content"""
        doc_path = Path(__file__).parent.parent / "docs" / "HUGGINGFACE_BEST_PRACTICES.md"
        with open(doc_path, "r", encoding="utf-8") as f:
            return f.read()

    def test_has_requirements_section(self, doc_content):
        """Test that documentation has requirements section"""
        assert (
            "### Requirements" in doc_content or "## Requirements" in doc_content
        ), "Should have requirements section"

    def test_lists_core_dependencies(self, doc_content):
        """Test that core dependencies are listed"""
        core_deps = [
            "torch==",
            "transformers==",
            "diffusers==",
        ]
        for dep in core_deps:
            assert dep in doc_content, f"Core dependency '{dep}' should be listed"

    def test_torch_version_specified(self, doc_content):
        """Test that PyTorch version is explicitly specified"""
        assert "torch==2." in doc_content, "Should specify PyTorch 2.x version"


class TestLinks:
    """Test links in the documentation"""

    @pytest.fixture
    def doc_content(self):
        """Read documentation content"""
        doc_path = Path(__file__).parent.parent / "docs" / "HUGGINGFACE_BEST_PRACTICES.md"
        with open(doc_path, "r", encoding="utf-8") as f:
            return f.read()

    @pytest.fixture
    def internal_links(self, doc_content):
        """Extract internal links"""
        pattern = r"\[([^\]]+)\]\(#([^\)]+)\)"
        return re.findall(pattern, doc_content)

    @pytest.fixture
    def external_links(self, doc_content):
        """Extract external links"""
        pattern = r"\[([^\]]+)\]\((https?://[^\)]+)\)"
        return re.findall(pattern, doc_content)

    def test_has_internal_links(self, internal_links):
        """Test that documentation has internal links"""
        assert len(internal_links) > 5, "Should have internal navigation links"

    def test_external_links_valid_urls(self, external_links):
        """Test that external links have valid URL format"""
        for _text, url in external_links:
            parsed = urlparse(url)
            assert parsed.scheme in ["http", "https"], f"URL should use http/https: {url}"
            assert parsed.netloc, f"URL should have domain: {url}"


class TestContentQuality:
    """Test the quality and completeness of content"""

    @pytest.fixture
    def doc_content(self):
        """Read documentation content"""
        doc_path = Path(__file__).parent.parent / "docs" / "HUGGINGFACE_BEST_PRACTICES.md"
        with open(doc_path, "r", encoding="utf-8") as f:
            return f.read()

    def test_has_production_focus(self, doc_content):
        """Test that documentation focuses on production"""
        production_keywords = ["production", "enterprise", "deployment", "performance"]
        found = [kw for kw in production_keywords if kw in doc_content.lower()]
        assert len(found) >= 3, "Should have production/enterprise focus"

    def test_memory_optimization_coverage(self, doc_content):
        """Test that memory optimization is well covered"""
        memory_topics = [
            "CPU Offload",
            "VAE Slicing",
            "Attention Slicing",
        ]
        for topic in memory_topics:
            assert topic in doc_content, f"Memory optimization topic '{topic}' should be covered"

    def test_troubleshooting_section_comprehensive(self, doc_content):
        """Test that troubleshooting section is comprehensive"""
        assert "## Troubleshooting" in doc_content, "Should have troubleshooting section"
        common_issues = ["Out of Memory", "Slow Generation"]
        found = [issue for issue in common_issues if issue in doc_content]
        assert len(found) >= 1, "Should cover common troubleshooting scenarios"

    def test_3d_generation_covered(self, doc_content):
        """Test that 3D generation is covered"""
        assert "3D" in doc_content, "Should mention 3D generation capabilities"


class TestFormatting:
    """Test markdown formatting and style"""

    @pytest.fixture
    def doc_content(self):
        """Read documentation content"""
        doc_path = Path(__file__).parent.parent / "docs" / "HUGGINGFACE_BEST_PRACTICES.md"
        with open(doc_path, "r", encoding="utf-8") as f:
            return f.read()

    def test_headers_properly_formatted(self, doc_content):
        """Test that headers use proper markdown syntax"""
        assert re.search(r"^# [A-Z]", doc_content, re.MULTILINE), "Should have level-1 header"
        level2_headers = re.findall(r"^## ", doc_content, re.MULTILINE)
        assert len(level2_headers) >= 10, "Should have multiple level-2 headers"

    def test_lists_properly_formatted(self, doc_content):
        """Test that lists use consistent formatting"""
        list_items = re.findall(r"^[-*+]\s", doc_content, re.MULTILINE)
        assert len(list_items) > 10, "Should have list items"


@pytest.mark.integration
class TestDocumentationIntegration:
    """Integration tests for documentation"""

    def test_documentation_in_docs_directory(self):
        """Test that documentation is in the docs directory"""
        doc_path = Path(__file__).parent.parent / "docs" / "HUGGINGFACE_BEST_PRACTICES.md"
        assert doc_path.exists(), "Documentation should be in docs/ directory"
        assert doc_path.parent.name == "docs", "Should be in docs/ directory"

    def test_documentation_is_markdown(self):
        """Test that documentation uses markdown format"""
        doc_path = Path(__file__).parent.parent / "docs" / "HUGGINGFACE_BEST_PRACTICES.md"
        assert doc_path.suffix == ".md", "Documentation should be markdown (.md)"

    def test_documentation_encoding(self):
        """Test that documentation uses UTF-8 encoding"""
        doc_path = Path(__file__).parent.parent / "docs" / "HUGGINGFACE_BEST_PRACTICES.md"
        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert len(content) > 0, "Should be able to read as UTF-8"
        except UnicodeDecodeError:
            pytest.fail("Documentation should use UTF-8 encoding")

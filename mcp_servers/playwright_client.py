# mcp/playwright_client.py
"""
Playwright MCP Client for DevSkyy.

Provides browser automation capabilities for:
- E2E testing of 3D viewer functionality
- Screenshot generation for products
- Automated UI testing
- Visual regression testing

Usage:
    from mcp.playwright_client import playwright_client

    await playwright_client.navigate("https://skyyrose.co")
    screenshot = await playwright_client.screenshot()
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any

from mcp.server_manager import mcp_manager

logger = logging.getLogger(__name__)


class PlaywrightMCPClient:
    """
    Playwright MCP client for browser automation and testing.

    Used for:
    - E2E testing of 3D viewer functionality
    - Screenshot generation for products
    - Automated UI testing
    - WordPress/WooCommerce testing
    """

    SERVER_ID = "playwright"

    async def navigate(self, url: str) -> dict[str, Any]:
        """
        Navigate to a URL.

        Args:
            url: URL to navigate to

        Returns:
            Navigation result
        """
        result = await mcp_manager.call_tool(
            self.SERVER_ID,
            "browser_navigate",
            {"url": url},
        )
        return result.data if result.success else {"error": result.error}

    async def screenshot(
        self,
        output_path: str | Path | None = None,
        full_page: bool = False,
        selector: str | None = None,
    ) -> bytes:
        """
        Take a screenshot.

        Args:
            output_path: Optional path to save screenshot
            full_page: Whether to capture full page
            selector: Optional CSS selector to screenshot specific element

        Returns:
            Screenshot image bytes
        """
        args: dict[str, Any] = {"fullPage": full_page}
        if selector:
            args["selector"] = selector

        result = await mcp_manager.call_tool(
            self.SERVER_ID,
            "browser_screenshot",
            args,
        )

        if result.success and "screenshot" in result.data:
            image_data = base64.b64decode(result.data["screenshot"])

            if output_path:
                Path(output_path).write_bytes(image_data)

            return image_data

        return b""

    async def click(self, selector: str) -> dict[str, Any]:
        """
        Click an element.

        Args:
            selector: CSS selector for element to click

        Returns:
            Click result
        """
        result = await mcp_manager.call_tool(
            self.SERVER_ID,
            "browser_click",
            {"selector": selector},
        )
        return result.data if result.success else {"error": result.error}

    async def fill(self, selector: str, value: str) -> dict[str, Any]:
        """
        Fill an input field.

        Args:
            selector: CSS selector for input
            value: Value to fill

        Returns:
            Fill result
        """
        result = await mcp_manager.call_tool(
            self.SERVER_ID,
            "browser_type",
            {
                "selector": selector,
                "text": value,
            },
        )
        return result.data if result.success else {"error": result.error}

    async def evaluate(self, script: str) -> Any:
        """
        Evaluate JavaScript in the browser.

        Args:
            script: JavaScript code to execute

        Returns:
            Script result
        """
        result = await mcp_manager.call_tool(
            self.SERVER_ID,
            "browser_evaluate",
            {"script": script},
        )
        return result.data.get("result") if result.success else None

    async def wait_for_selector(
        self,
        selector: str,
        timeout: int = 30000,
    ) -> bool:
        """
        Wait for an element to appear.

        Args:
            selector: CSS selector to wait for
            timeout: Maximum wait time in milliseconds

        Returns:
            True if element found, False otherwise
        """
        try:
            result = await mcp_manager.call_tool(
                self.SERVER_ID,
                "browser_wait_for_selector",
                {
                    "selector": selector,
                    "timeout": timeout,
                },
            )
            return result.success
        except Exception:
            return False

    async def get_page_content(self) -> str:
        """Get the current page HTML content."""
        content = await self.evaluate("document.documentElement.outerHTML")
        return content or ""

    async def get_page_title(self) -> str:
        """Get the current page title."""
        title = await self.evaluate("document.title")
        return title or ""

    async def test_3d_viewer(self, product_url: str) -> dict[str, Any]:
        """
        Test 3D viewer functionality on a product page.

        Args:
            product_url: URL of the product page

        Returns:
            Test results with pass/fail details
        """
        results: dict[str, Any] = {
            "url": product_url,
            "tests_passed": 0,
            "tests_failed": 0,
            "details": [],
        }

        # Navigate to product
        await self.navigate(product_url)

        # Test 1: Check 3D viewer button exists
        has_button = await self.wait_for_selector(
            ".skyyrose-view-3d-btn",
            timeout=5000,
        )
        results["details"].append(
            {
                "test": "3D viewer button exists",
                "passed": has_button,
            }
        )
        if has_button:
            results["tests_passed"] += 1
        else:
            results["tests_failed"] += 1
            return results  # Can't continue without button

        # Test 2: Click button and check modal opens
        await self.click(".skyyrose-view-3d-btn")
        modal_opened = await self.wait_for_selector(
            ".skyyrose-3d-modal",
            timeout=5000,
        )
        results["details"].append(
            {
                "test": "Modal opens on click",
                "passed": modal_opened,
            }
        )
        if modal_opened:
            results["tests_passed"] += 1
        else:
            results["tests_failed"] += 1

        # Test 3: Check canvas is rendered
        canvas_loaded = await self.wait_for_selector(
            ".skyyrose-3d-canvas",
            timeout=10000,
        )
        results["details"].append(
            {
                "test": "3D canvas rendered",
                "passed": canvas_loaded,
            }
        )
        if canvas_loaded:
            results["tests_passed"] += 1
        else:
            results["tests_failed"] += 1

        # Test 4: Check loading completes
        loading_hidden = await self.evaluate("""
            document.querySelector('.skyyrose-3d-loading')?.style.display === 'none'
        """)
        results["details"].append(
            {
                "test": "Loading completes",
                "passed": bool(loading_hidden),
            }
        )
        if loading_hidden:
            results["tests_passed"] += 1
        else:
            results["tests_failed"] += 1

        # Test 5: Check WebGL context
        has_webgl = await self.evaluate("""
            !!document.querySelector('.skyyrose-3d-canvas')?.getContext('webgl2') ||
            !!document.querySelector('.skyyrose-3d-canvas')?.getContext('webgl')
        """)
        results["details"].append(
            {
                "test": "WebGL context available",
                "passed": bool(has_webgl),
            }
        )
        if has_webgl:
            results["tests_passed"] += 1
        else:
            results["tests_failed"] += 1

        # Take screenshot
        try:
            screenshot = await self.screenshot(selector=".skyyrose-3d-modal-content")
            results["screenshot"] = screenshot
        except Exception:
            pass

        return results

    async def test_wordpress_page(self, page_url: str) -> dict[str, Any]:
        """
        Test a WordPress page for basic functionality.

        Args:
            page_url: URL of the WordPress page

        Returns:
            Test results
        """
        results: dict[str, Any] = {
            "url": page_url,
            "tests_passed": 0,
            "tests_failed": 0,
            "details": [],
        }

        # Navigate
        await self.navigate(page_url)

        # Test 1: Page loads
        title = await self.get_page_title()
        page_loads = bool(title)
        results["details"].append(
            {
                "test": "Page loads successfully",
                "passed": page_loads,
                "title": title,
            }
        )
        if page_loads:
            results["tests_passed"] += 1
        else:
            results["tests_failed"] += 1

        # Test 2: No JavaScript errors
        errors = await self.evaluate("""
            window.__jsErrors || []
        """)
        no_js_errors = not errors or len(errors) == 0
        results["details"].append(
            {
                "test": "No JavaScript errors",
                "passed": no_js_errors,
                "errors": errors if errors else [],
            }
        )
        if no_js_errors:
            results["tests_passed"] += 1
        else:
            results["tests_failed"] += 1

        # Test 3: Check for Elementor
        has_elementor = await self.evaluate("""
            !!document.querySelector('.elementor')
        """)
        results["details"].append(
            {
                "test": "Elementor content present",
                "passed": bool(has_elementor),
            }
        )
        if has_elementor:
            results["tests_passed"] += 1
        else:
            results["tests_failed"] += 1

        return results


# Singleton instance
playwright_client = PlaywrightMCPClient()

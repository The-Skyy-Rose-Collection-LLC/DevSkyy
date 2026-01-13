"""SkyyRose Product Agent.

DevSkyy agent wrapper for SkyyRose product launches.
Integrates with the existing agent ecosystem.
"""

import asyncio
import logging
import os
from dataclasses import dataclass

# Import the orchestrator
from pipelines.skyyrose_master_orchestrator import SkyyRoseMasterOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class ProductTask:
    """Product launch task specification."""

    action: str
    product: dict | None = None
    products: list[dict] | None = None
    options: dict | None = None


class SkyyRoseProductAgent:
    """
    DevSkyy agent wrapper for SkyyRose product launches.
    Integrates with your existing 50+ agent ecosystem.
    """

    def __init__(self, config: dict | None = None):
        """Initialize the product agent.

        Args:
            config: Optional configuration override. If not provided,
                   uses environment variables.
        """
        if config is None:
            config = {
                "flux_space_url": os.getenv("FLUX_SPACE_URL", "damBruh/skyyrose-flux-upscaler"),
                "sdxl_space_url": os.getenv(
                    "SDXL_SPACE_URL", "damBruh/skyyrose-product-photography"
                ),
                "qwen_space_url": os.getenv("QWEN_SPACE_URL", "damBruh/skyyrose-product-analyzer"),
                "wordpress_url": os.getenv("WORDPRESS_URL", "https://skyyrose.co"),
                "wp_username": os.getenv("WP_USERNAME"),
                "wp_password": os.getenv("WP_APP_PASSWORD"),
                "r2_account_id": os.getenv("R2_ACCOUNT_ID"),
                "r2_access_key": os.getenv("R2_ACCESS_KEY"),
                "r2_secret_key": os.getenv("R2_SECRET_KEY"),
            }

        self.orchestrator = SkyyRoseMasterOrchestrator(config)

        self.role = "Product Launch Automation"
        self.capabilities = [
            "Generate luxury product photography",
            "AI-powered product copywriting",
            "Automated WordPress deployment",
            "SEO optimization",
            "Social media asset creation",
        ]

    async def execute(self, task: dict) -> dict:
        """
        Execute product launch task.

        Task format:
        {
            'action': 'launch_product' | 'batch_launch',
            'product': {...product_concept...},  # For single launch
            'products': [...],  # For batch launch
            'options': {
                'auto_publish': False,
                'notify_slack': True
            }
        }

        Returns:
            Launch result dictionary
        """
        action = task.get("action")
        options = task.get("options", {})

        if action == "launch_product":
            result = await self.orchestrator.launch_complete_product(
                product_concept=task["product"], auto_publish=options.get("auto_publish", False)
            )

            # Notify other agents
            if options.get("notify_slack"):
                await self._notify_slack(result)

            return result

        elif action == "batch_launch":
            # Launch multiple products
            results = []
            products = task.get("products", [])

            for i, product in enumerate(products, 1):
                print(f"\nLaunching product {i}/{len(products)}")

                result = await self.orchestrator.launch_complete_product(
                    product_concept=product, auto_publish=options.get("auto_publish", False)
                )
                results.append(result)

                # Rate limiting between products
                if i < len(products):
                    await asyncio.sleep(60)

            return {"batch_results": results, "total_launched": len(results)}

        elif action == "analyze_product":
            # Just analyze without launching
            return await self._analyze_only(task.get("image_path"))

        else:
            raise ValueError(f"Unknown action: {action}")

    async def _analyze_only(self, image_path: str) -> dict:
        """Analyze a product image without launching."""
        if not image_path:
            return {"error": "No image path provided"}

        try:
            metadata = self.orchestrator.qwen_space.predict(
                image=image_path, api_name="/extract_metadata"
            )
            return {"metadata": metadata, "status": "analyzed"}
        except Exception as e:
            return {"error": str(e)}

    async def _notify_slack(self, launch_result: dict):
        """Notify Slack channel of new product launch."""
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            return

        try:
            import requests

            message = {
                "text": f"New product launched: {launch_result.get('product_name', 'Unknown')}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{launch_result.get('product_name')}*\n"
                            f"Collection: {launch_result.get('collection')}\n"
                            f"URL: {launch_result.get('product_url')}",
                        },
                    }
                ],
            }
            requests.post(webhook_url, json=message, timeout=10)
        except Exception as e:
            logger.warning(f"Failed to send webhook notification: {e}")

    def get_status(self) -> dict:
        """Get agent status and health."""
        return {
            "role": self.role,
            "capabilities": self.capabilities,
            "backend_health": self.orchestrator.backend_health,
            "status": "ready",
        }


# Agent registration helper
def register_agent():
    """Register with DevSkyy agent registry if available."""
    try:
        from devsky import AgentRegistry

        AgentRegistry.register(
            agent_class=SkyyRoseProductAgent,
            name="skyyrose_product_launcher",
            category="e-commerce",
        )
        print("SkyyRose Product Agent registered with DevSkyy")
    except ImportError:
        print("DevSkyy AgentRegistry not available - agent created standalone")


# Auto-register if imported
if __name__ != "__main__":
    register_agent()

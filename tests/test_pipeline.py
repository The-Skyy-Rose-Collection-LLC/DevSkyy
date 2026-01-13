# test_pipeline.py
import asyncio
import os
import sys

import pytest
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipelines.skyyrose_master_orchestrator import SkyyRoseMasterOrchestrator

# Load environment at module level
load_dotenv()

# Check if required external services are configured
REQUIRED_ENV_VARS = ["FLUX_SPACE_URL", "QWEN_SPACE_URL"]
MISSING_VARS = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]


@pytest.mark.integration
@pytest.mark.skipif(
    len(MISSING_VARS) > 0,
    reason=f"Integration test requires external services. Missing env vars: {MISSING_VARS}",
)
async def test_complete_pipeline():
    """
    Integration test for complete pipeline with minimal product.

    Requires external Gradio spaces and WordPress configured via environment variables.
    """

    print("🧪 Testing SkyyRose Complete Pipeline")
    print("=" * 80)

    # Initialize
    orchestrator = SkyyRoseMasterOrchestrator(
        {
            "flux_space_url": os.getenv("FLUX_SPACE_URL"),
            "sdxl_space_url": os.getenv("SDXL_SPACE_URL"),
            "qwen_space_url": os.getenv("QWEN_SPACE_URL"),
            "wordpress_url": os.getenv("WORDPRESS_URL"),
            "wp_username": os.getenv("WP_USERNAME"),
            "wp_password": os.getenv("WP_APP_PASSWORD"),
            "r2_account_id": os.getenv("R2_ACCOUNT_ID"),
            "r2_access_key": os.getenv("R2_ACCESS_KEY"),
            "r2_secret_key": os.getenv("R2_SECRET_KEY"),
            "r2_bucket": os.getenv("R2_BUCKET", "skyyrose-products"),
        }
    )

    # Test product
    test_product = {
        "name": "TEST - Black Tee",
        "collection": "SIGNATURE",
        "garment_type": "oversized t-shirt",
        "color": "black",
        "fabric": "organic cotton",
        "price": 45.00,
        "sku_base": "TEST-001",
    }

    # Launch (as draft)
    result = await orchestrator.launch_complete_product(
        product_concept=test_product,
        auto_publish=False,  # Keep as draft for testing
    )

    print("\n✅ Pipeline Test Complete!")
    print(f"Product URL: {result['product_url']}")
    print("\nPlease review the draft product and delete if satisfied with test.")


if __name__ == "__main__":
    asyncio.run(test_complete_pipeline())

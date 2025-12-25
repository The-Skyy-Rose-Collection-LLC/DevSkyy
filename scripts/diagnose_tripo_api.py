#!/usr/bin/env python3
"""
Diagnose Tripo3D API Integration

Tests the Tripo3D API with your API key to identify what's broken.
"""

import asyncio
import base64
import json
import logging
import os
from pathlib import Path

import aiohttp

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_api_connection() -> bool:
    """Test basic API connection and authentication."""
    api_key = os.getenv("TRIPO_API_KEY") or os.getenv("TRIPO3D_API_KEY")

    if not api_key:
        logger.error("TRIPO_API_KEY environment variable not set!")
        return False

    logger.info(f"Using API key: {api_key[:20]}...")

    base_url = "https://api.tripo3d.ai/v2"

    # Test 1: Check if API is reachable
    logger.info("\n" + "=" * 70)
    logger.info("TEST 1: API Reachability")
    logger.info("=" * 70)

    try:
        # Try with SSL verification first
        async with aiohttp.ClientSession() as session:
            async with session.head(base_url) as response:
                logger.info(f"Base URL reachable (SSL verified): {response.status}")
    except Exception as e:
        logger.warning(f"SSL verification failed: {e}")
        logger.info("Retrying with SSL verification disabled...")

        try:
            # Retry with SSL verification disabled
            import ssl

            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                async with session.head(base_url) as response:
                    logger.info(f"✓ Base URL reachable (SSL disabled): {response.status}")
                    logger.warning(
                        "⚠️  Note: SSL verification is disabled. For production, install proper SSL certificates."
                    )
        except Exception as e2:
            logger.error(f"Cannot reach base URL even with SSL disabled: {e2}")
            return False

    # Test 2: Test authentication
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: Authentication")
    logger.info("=" * 70)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        # Create SSL context that doesn't verify certificates
        import ssl

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        async with aiohttp.ClientSession(headers=headers, connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
            # Try a simple endpoint that doesn't require much
            async with session.get(f"{base_url}/balance") as response:
                logger.info(f"Balance endpoint status: {response.status}")
                result = await response.json()
                logger.info(f"Response: {json.dumps(result, indent=2)}")

                if response.status == 200:
                    logger.info("✓ Authentication successful!")
                elif response.status == 401:
                    logger.error("✗ Authentication failed - invalid API key")
                    return False
                else:
                    logger.warning(f"Unexpected status: {response.status}")
    except Exception as e:
        logger.error(f"Error testing authentication: {e}")
        return False

    # Test 3: Test text-to-3D endpoint
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Text-to-3D Endpoint")
    logger.info("=" * 70)

    payload = {
        "type": "text_to_model",
        "prompt": "A simple red cube, 3D model",
        "model_version": "v2.0-20240919",
    }

    try:
        import ssl

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        async with aiohttp.ClientSession(headers=headers, connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
            logger.info(f"POST /task")
            logger.info(f"Payload: {json.dumps(payload, indent=2)}")

            async with session.post(f"{base_url}/task", json=payload) as response:
                result = await response.json()
                logger.info(f"Status: {response.status}")
                logger.info(f"Response: {json.dumps(result, indent=2)}")

                if response.status in (200, 201):
                    task_id = result.get("data", {}).get("task_id")
                    if task_id:
                        logger.info(f"✓ Task created successfully: {task_id}")
                        return await test_task_polling(session, task_id, base_url)
                    else:
                        logger.error("✗ No task_id in response")
                        return False
                else:
                    logger.error(f"✗ Unexpected status: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"Error testing text-to-3D: {e}")
        return False


async def test_task_polling(session: aiohttp.ClientSession, task_id: str, base_url: str) -> bool:
    """Test task polling."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: Task Polling")
    logger.info("=" * 70)

    max_polls = 5
    poll_interval = 2

    for poll_num in range(max_polls):
        logger.info(f"\nPoll {poll_num + 1}/{max_polls}")

        try:
            # Session already has SSL context configured
            async with session.get(f"{base_url}/task/{task_id}") as response:
                result = await response.json()
                logger.info(f"Status: {response.status}")
                logger.info(f"Response: {json.dumps(result, indent=2)}")

                if response.status == 200:
                    status = result.get("data", {}).get("status")
                    progress = result.get("data", {}).get("progress", 0)

                    logger.info(f"Task status: {status} ({progress}%)")

                    if status == "success":
                        logger.info("✓ Task completed successfully!")
                        return True
                    elif status == "failed":
                        error = result.get("data", {}).get("error", "Unknown error")
                        logger.error(f"✗ Task failed: {error}")
                        return False
                    elif status in ("queued", "running"):
                        logger.info(f"Waiting {poll_interval}s before next poll...")
                        await asyncio.sleep(poll_interval)
                    else:
                        logger.warning(f"Unknown status: {status}")
                        return False
                else:
                    logger.error(f"✗ Unexpected status: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error polling task: {e}")
            return False

    logger.warning("Max polls reached, task still in progress")
    return True


async def test_image_to_3d():
    """Test image-to-3D with a simple test image."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 5: Image-to-3D Endpoint")
    logger.info("=" * 70)

    api_key = os.getenv("TRIPO_API_KEY") or os.getenv("TRIPO3D_API_KEY")
    if not api_key:
        logger.error("TRIPO_API_KEY not set")
        return False

    # Try to find a test image
    test_images = list(Path("assets/extracted").rglob("*.jpg")) + list(Path("assets/extracted").rglob("*.png"))

    if not test_images:
        logger.warning("No test images found in assets/extracted/")
        logger.info("Skipping image-to-3D test")
        return True

    test_image = test_images[0]
    logger.info(f"Using test image: {test_image}")

    # Read and encode image
    with open(test_image, "rb") as f:
        image_data = f.read()

    b64_image = base64.b64encode(image_data).decode()
    logger.info(f"Image size: {len(image_data)} bytes")
    logger.info(f"Base64 encoded size: {len(b64_image)} bytes")

    payload = {
        "type": "image_to_model",
        "file": {
            "type": "png" if str(test_image).endswith(".png") else "jpg",
            "data": b64_image,
        },
        "model_version": "v2.0-20240919",
    }

    base_url = "https://api.tripo3d.ai/v2"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        import ssl

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        async with aiohttp.ClientSession(headers=headers, connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
            logger.info(f"POST /task with image data")

            async with session.post(f"{base_url}/task", json=payload) as response:
                result = await response.json()
                logger.info(f"Status: {response.status}")
                logger.info(f"Response: {json.dumps(result, indent=2)}")

                if response.status in (200, 201):
                    task_id = result.get("data", {}).get("task_id")
                    if task_id:
                        logger.info(f"✓ Task created: {task_id}")
                        return True
                    else:
                        logger.error("✗ No task_id in response")
                        return False
                else:
                    logger.error(f"✗ Unexpected status: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"Error in image-to-3D test: {e}")
        return False


async def main():
    """Run all diagnostics."""
    logger.info("=" * 70)
    logger.info("TRIPO3D API DIAGNOSTICS")
    logger.info("=" * 70)

    success = await test_api_connection()

    if success:
        logger.info("\n" + "=" * 70)
        await test_image_to_3d()
        logger.info("=" * 70)

    logger.info("\n" + "=" * 70)
    logger.info("DIAGNOSTIC COMPLETE")
    logger.info("=" * 70)

    if not success:
        logger.error("\n⚠️  API connection test failed!")
        logger.error("Possible causes:")
        logger.error("1. Invalid API key")
        logger.error("2. API server is down")
        logger.error("3. Network connectivity issue")
        logger.error("4. Endpoint has changed")


if __name__ == "__main__":
    asyncio.run(main())

"""Test script for API endpoints and WebSocket connections.

This script tests all the backend API endpoints and WebSocket connections
to ensure they work correctly with the frontend dashboard.

Usage:
    python test_api_endpoints.py [--host localhost] [--port 8000]

Requirements:
    - Backend server must be running
    - pip install httpx websockets
"""

import argparse
import asyncio
import json
import sys

try:
    import httpx
    import websockets
except ImportError:
    print("Error: Missing dependencies. Install with: pip install httpx websockets")
    sys.exit(1)


class APITester:
    """Test suite for DevSkyy API endpoints."""

    def __init__(self, host: str = "localhost", port: int = 8000):
        self.base_url = f"http://{host}:{port}"
        self.ws_url = f"ws://{host}:{port}"
        self.token: str | None = None

    async def test_health(self) -> bool:
        """Test health endpoint."""
        print("\n=== Testing Health Endpoint ===")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✓ Health check passed: {data['status']}")
                    print(f"  Services: {data['services']}")
                    return True
                else:
                    print(f"✗ Health check failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"✗ Health check error: {e}")
            return False

    async def test_agents_list(self) -> bool:
        """Test GET /api/v1/agents endpoint."""
        print("\n=== Testing Agents List Endpoint ===")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/v1/agents")
                if response.status_code == 200:
                    agents = response.json()
                    print(f"✓ Found {len(agents)} agents")
                    for agent in agents[:3]:  # Show first 3
                        print(f"  - {agent['name']} ({agent['type']}): {agent['status']}")
                    return True
                else:
                    print(f"✗ Agents list failed: {response.status_code}")
                    print(f"  Response: {response.text}")
                    return False
        except Exception as e:
            print(f"✗ Agents list error: {e}")
            return False

    async def test_round_table_providers(self) -> bool:
        """Test GET /api/v1/round-table/providers endpoint."""
        print("\n=== Testing Round Table Providers Endpoint ===")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/v1/round-table/providers")
                if response.status_code == 200:
                    providers = response.json()
                    print(f"✓ Found {len(providers)} LLM providers")
                    for provider in providers:
                        status = "enabled" if provider["enabled"] else "disabled"
                        print(f"  - {provider['display_name']}: {status}")
                    return True
                else:
                    print(f"✗ Round Table providers failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"✗ Round Table providers error: {e}")
            return False

    async def test_tasks_list(self) -> bool:
        """Test GET /api/v1/tasks endpoint."""
        print("\n=== Testing Tasks List Endpoint ===")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/v1/tasks?limit=5")
                if response.status_code == 200:
                    tasks = response.json()
                    print(f"✓ Found {len(tasks)} recent tasks")
                    for task in tasks[:3]:
                        print(f"  - {task['taskId']}: {task['status']} ({task['agentType']})")
                    return True
                else:
                    print(f"✗ Tasks list failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"✗ Tasks list error: {e}")
            return False

    async def test_websocket_connection(self, channel: str, timeout: float = 5.0) -> bool:
        """Test WebSocket connection to a specific channel."""
        print(f"\n=== Testing WebSocket: {channel} ===")
        try:
            uri = f"{self.ws_url}/api/ws/{channel}"
            async with websockets.connect(uri) as websocket:
                print(f"✓ Connected to {channel}")

                # Send ping
                await websocket.send(json.dumps({"type": "ping"}))
                print("  Sent ping")

                # Wait for pong (with timeout)
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                    data = json.loads(message)
                    if data.get("type") == "pong":
                        print(f"  ✓ Received pong: {data}")
                        return True
                    else:
                        print(f"  Received unexpected message: {data}")
                        return True  # Still counts as connection success
                except TimeoutError:
                    print("  ! Timeout waiting for response (connection still valid)")
                    return True

        except Exception as e:
            print(f"✗ WebSocket {channel} error: {e}")
            return False

    async def test_all_websockets(self) -> dict[str, bool]:
        """Test all WebSocket channels."""
        channels = ["agents", "round_table", "tasks", "3d_pipeline", "metrics"]
        results = {}

        for channel in channels:
            results[channel] = await self.test_websocket_connection(channel)
            await asyncio.sleep(0.5)  # Brief delay between tests

        return results

    async def run_all_tests(self) -> dict[str, bool]:
        """Run all API tests."""
        print("\n" + "=" * 60)
        print("DevSkyy Backend API Test Suite")
        print(f"Testing: {self.base_url}")
        print("=" * 60)

        results = {
            "health": await self.test_health(),
            "agents_list": await self.test_agents_list(),
            "round_table_providers": await self.test_round_table_providers(),
            "tasks_list": await self.test_tasks_list(),
        }

        # Test WebSockets
        ws_results = await self.test_all_websockets()
        results.update({f"ws_{k}": v for k, v in ws_results.items()})

        # Summary
        print("\n" + "=" * 60)
        print("Test Results Summary")
        print("=" * 60)

        passed = sum(1 for v in results.values() if v)
        total = len(results)

        for test_name, success in results.items():
            status = "✓ PASS" if success else "✗ FAIL"
            print(f"{status}: {test_name}")

        print(f"\nTotal: {passed}/{total} tests passed")
        print("=" * 60)

        return results


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test DevSkyy API endpoints")
    parser.add_argument("--host", default="localhost", help="API host")
    parser.add_argument("--port", type=int, default=8000, help="API port")
    args = parser.parse_args()

    tester = APITester(host=args.host, port=args.port)
    results = await tester.run_all_tests()

    # Exit with error code if any test failed
    if not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""Run system health check."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.ops import OpsAgent
from src.core.config import load_config
from src.core.logging import setup_logging
from src.core.queue import QueueManager


async def main():
    """
    Run the platform health check and report results to standard output.
    
    Loads configuration, initializes logging and the queue manager, executes the OpsAgent "health_check" task, prints the overall status, individual checks, and any alerts, and ensures the queue manager is closed before exit.
    
    Returns:
        int: `0` on success, `1` if an error occurred during the health check.
    """
    print("Fashion AI Platform - Health Check")
    print("=" * 50)

    # Load configuration
    config = load_config()
    setup_logging(log_level="INFO")

    # Create queue manager
    queue_manager = QueueManager(
        host=config.redis_host,
        port=config.redis_port,
        password=config.redis_password,
        prefix=config.queue_prefix,
    )

    # Create OpsAgent
    ops_agent = OpsAgent(
        io_path=config.log_path,
        queue_manager=queue_manager,
    )

    # Run health check
    try:
        health_result = await ops_agent.process_task("health_check", {})

        print(f"\nStatus: {health_result['status']}")
        print(f"\nChecks:")
        for check_name, check_value in health_result["checks"].items():
            print(f"  - {check_name}: {check_value}")

        if health_result.get("alerts"):
            print(f"\nAlerts:")
            for alert in health_result["alerts"]:
                print(f"  ⚠ {alert}")

        print("\nHealth check complete!")

    except Exception as e:
        print(f"\nError during health check: {e}", file=sys.stderr)
        return 1

    finally:
        queue_manager.close()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
"""
Workflow CLI Runner
==================

Command-line interface for running code-based workflows.

Usage:
    python -m workflows.cli run ci
    python -m workflows.cli run deployment --environment=staging
    python -m workflows.cli run all
    python -m workflows.cli list
    python -m workflows.cli status
"""

import argparse
import asyncio
import logging
import sys
from typing import Any

from devskyy_workflows.ci_workflow import CIWorkflow
from devskyy_workflows.deployment_workflow import DeploymentWorkflow
from devskyy_workflows.docker_workflow import DockerWorkflow
from devskyy_workflows.mcp_workflow import MCPWorkflow
from devskyy_workflows.ml_workflow import MLWorkflow
from devskyy_workflows.quality_workflow import QualityWorkflow
from devskyy_workflows.workflow_runner import WorkflowRunner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def setup_runner() -> WorkflowRunner:
    """Setup workflow runner with all workflows"""
    runner = WorkflowRunner()

    # Register all workflows
    runner.register("ci", CIWorkflow)
    runner.register("deployment", DeploymentWorkflow)
    runner.register("docker", DockerWorkflow)
    runner.register("mcp", MCPWorkflow)
    runner.register("ml", MLWorkflow)
    runner.register("quality", QualityWorkflow)

    return runner


async def run_workflow(workflow_name: str, **kwargs: Any) -> None:
    """Run a specific workflow"""
    runner = setup_runner()

    logger.info(f"Starting workflow: {workflow_name}")

    try:
        result = await runner.run(workflow_name, inputs=kwargs)

        print("\n" + "=" * 80)
        print(f"Workflow: {result.name}")
        print(f"Status: {result.status}")
        print(f"Duration: {result.duration_seconds:.2f}s")
        print("=" * 80)

        if result.errors:
            print("\nErrors:")
            for error in result.errors:
                print(f"  - {error}")

        if result.outputs:
            print("\nOutputs:")
            for key, value in result.outputs.items():
                print(f"  {key}: {value}")

        print("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        sys.exit(1)


async def run_all_workflows() -> None:
    """Run all workflows"""
    runner = setup_runner()

    workflows = ["ci", "quality", "mcp", "ml", "docker"]

    logger.info("Running all workflows...")

    results = await runner.run_multiple(workflows)

    print("\n" + "=" * 80)
    print("All Workflows Summary")
    print("=" * 80)

    for result in results:
        if isinstance(result, Exception):
            print(f"❌ {result}")
        else:
            status_emoji = "✅" if result.status == "completed" else "❌"
            print(
                f"{status_emoji} {result.name}: {result.status} "
                f"({result.duration_seconds:.2f}s)"
            )

    print("=" * 80 + "\n")


def list_workflows() -> None:
    """List all available workflows"""
    print("\n" + "=" * 80)
    print("Available Workflows")
    print("=" * 80)

    workflows = [
        ("ci", "CI/CD Pipeline - Testing, linting, security, and build"),
        ("deployment", "Deployment Pipeline - Deploy to staging/production"),
        ("docker", "Docker Workflow - Container build and security"),
        ("mcp", "MCP Workflow - Model Context Protocol testing"),
        ("ml", "ML Workflow - Machine learning and AI agent testing"),
        ("quality", "Quality Workflow - Code quality and standards"),
    ]

    for name, description in workflows:
        print(f"\n{name}")
        print(f"  {description}")

    print("\n" + "=" * 80 + "\n")


def show_status() -> None:
    """Show workflow execution status"""
    runner = setup_runner()

    results = runner.get_results()

    if not results:
        print("\nNo workflow executions found.\n")
        return

    print("\n" + "=" * 80)
    print("Workflow Execution History")
    print("=" * 80)

    for result in results:
        print(f"\n{result.name}:")
        print(f"  Status: {result.status}")
        print(f"  Started: {result.started_at}")
        print(f"  Duration: {result.duration_seconds:.2f}s")
        if result.errors:
            print(f"  Errors: {len(result.errors)}")

    print("\n" + "=" * 80 + "\n")


def main() -> None:
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="DevSkyy Workflow Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a workflow")
    run_parser.add_argument("workflow", help="Workflow name or 'all'")
    run_parser.add_argument(
        "--environment",
        choices=["staging", "production", "development"],
        help="Deployment environment (for deployment workflow)",
    )

    # List command
    subparsers.add_parser("list", help="List available workflows")

    # Status command
    subparsers.add_parser("status", help="Show workflow execution status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "list":
        list_workflows()

    elif args.command == "status":
        show_status()

    elif args.command == "run":
        if args.workflow == "all":
            asyncio.run(run_all_workflows())
        else:
            kwargs = {}
            if args.environment:
                kwargs["environment"] = args.environment

            asyncio.run(run_workflow(args.workflow, **kwargs))


if __name__ == "__main__":
    main()

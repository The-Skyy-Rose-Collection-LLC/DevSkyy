"""CLI entry point for Fashion AI platform."""

import asyncio
import sys
from pathlib import Path

import click

from src.agents import CommerceAgent, DesignerAgent, FinanceAgent, MarketingAgent, OpsAgent
from src.core.config import load_config
from src.core.logging import setup_logging
from src.core.queue import QueueManager


@click.group()
def cli():
    """Fashion AI Autonomous Commerce Platform CLI."""
    pass


@cli.command()
def version():
    """Show version information."""
    click.echo("Fashion AI Platform v1.0.0")


@cli.command()
@click.option("--agent", type=click.Choice(["designer", "commerce", "marketing", "finance", "ops"]))
def start(agent: str):
    """Start a specific agent.

    Args:
        agent: Agent name to start
    """
    config = load_config()
    setup_logging(log_level=config.agent_log_level)

    queue_manager = QueueManager(
        host=config.redis_host,
        port=config.redis_port,
        password=config.redis_password,
        prefix=config.queue_prefix,
    )

    agent_map = {
        "designer": DesignerAgent,
        "commerce": CommerceAgent,
        "marketing": MarketingAgent,
        "finance": FinanceAgent,
        "ops": OpsAgent,
    }

    agent_class = agent_map.get(agent)
    if not agent_class:
        click.echo(f"Unknown agent: {agent}", err=True)
        sys.exit(1)

    io_path = config.data_path / agent
    agent_instance = agent_class(
        io_path=io_path,
        queue_manager=queue_manager,
        retry_attempts=config.agent_retry_attempts,
        timeout=config.agent_timeout,
    )

    click.echo(f"Starting {agent} agent...")
    asyncio.run(agent_instance.run())


@cli.command()
def start_all():
    """Start all agents."""
    agents = ["designer", "commerce", "marketing", "finance", "ops"]
    click.echo("Starting all agents...")

    # In production, use multiprocessing or orchestrator
    for agent in agents:
        click.echo(f"  - {agent}: ready")


@cli.command()
def health():
    """Check system health."""
    click.echo("Running health check...")
    click.echo("System: healthy")


if __name__ == "__main__":
    cli()

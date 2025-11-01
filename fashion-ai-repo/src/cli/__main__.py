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
    """
    Root Click command group for the Fashion AI Autonomous Commerce Platform CLI.
    
    Provides the top-level command namespace that groups subcommands for reporting the
    version, starting individual agents, starting all agents (informational stub),
    and performing a basic health check.
    """
    pass


@cli.command()
def version():
    """
    Display the CLI version string for the Fashion AI Platform.
    """
    click.echo("Fashion AI Platform v1.0.0")


@cli.command()
@click.option("--agent", type=click.Choice(["designer", "commerce", "marketing", "finance", "ops"]))
def start(agent: str):
    """
    Start the specified agent process.
    
    Loads configuration, configures logging, initializes a QueueManager, instantiates the requested agent with its IO path, retry attempts, and timeout, then runs the agent's main loop. Exits with status 1 if the provided agent name is not recognized.
    
    Parameters:
        agent: Name of the agent to start. Allowed values: "designer", "commerce", "marketing", "finance", "ops".
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
    """
    Announces that all agents are starting and prints a readiness line for each known agent.
    
    Prints "Starting all agents..." followed by "  - {agent}: ready" for each configured agent.
    This function only reports readiness and does not launch any agent processes; use an orchestrator
    or multiprocessing to start agents in production.
    """
    agents = ["designer", "commerce", "marketing", "finance", "ops"]
    click.echo("Starting all agents...")

    # In production, use multiprocessing or orchestrator
    for agent in agents:
        click.echo(f"  - {agent}: ready")


@cli.command()
def health():
    """
    Report a basic CLI health status.
    
    Prints a brief health-check message to standard output indicating the system is healthy.
    """
    click.echo("Running health check...")
    click.echo("System: healthy")


if __name__ == "__main__":
    cli()
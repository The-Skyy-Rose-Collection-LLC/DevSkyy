"""
LAYER 4 — Watchdog System
Monitors agent health, detects anomalies, and performs automatic recovery
"""

import asyncio
from datetime import datetime
import json
import logging
from pathlib import Path

import yaml


logger = logging.getLogger(__name__)


class Watchdog:
    """
    Watchdog system for bounded autonomous agents.

    Features:
    - Continuous health monitoring
    - Automatic error detection
    - Controlled restart on failure
    - Operator notification on repeated failures
    - Incident reporting
    """

    def __init__(
        self,
        config_path: str = "fashion_ai_bounded_autonomy/config/monitor.yaml",
        max_restart_attempts: int = 3
    ):
        """
        Initialize the Watchdog instance and prepare monitoring state.
        
        Loads watcher configuration from the given path, records the maximum allowed restart attempts, initializes in-memory state used to track agent errors, restarts, halts, and incidents, ensures the incident logs directory exists, and sets the watcher to a stopped state.
        
        Parameters:
            config_path (str): Filesystem path to the YAML monitoring configuration. Defaults to "fashion_ai_bounded_autonomy/config/monitor.yaml".
            max_restart_attempts (int): Maximum number of automatic restart attempts allowed per agent before halting. Defaults to 3.
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.max_restart_attempts = max_restart_attempts

        # Agent monitoring state
        self.agent_error_counts: dict[str, int] = {}
        self.agent_restart_counts: dict[str, int] = {}
        self.halted_agents: list[str] = {}

        # Incident tracking
        self.incidents: list[dict] = []
        self.incident_log_path = Path("logs/incidents/")
        self.incident_log_path.mkdir(parents=True, exist_ok=True)

        self.running = False

        logger.info("👁️  Watchdog system initialized")

    def _load_config(self) -> dict:
        """
        Load and return the watchdog configuration from the configured YAML file.
        
        Reads the YAML file at self.config_path and returns the mapping stored under
        the top-level keys "monitoring" -> "watchdog".
        
        Returns:
            dict: The watchdog configuration mapping extracted from the YAML file.
        """
        with open(self.config_path) as f:
            config = yaml.safe_load(f)
        return config["monitoring"]["watchdog"]

    async def start(self, orchestrator):
        """Start watchdog monitoring"""
        self.running = True
        self.orchestrator = orchestrator

        check_interval = self.config["check_interval_seconds"]
        logger.info(f"👁️  Watchdog started (check interval: {check_interval}s)")

        while self.running:
            await self._check_all_agents()
            await asyncio.sleep(check_interval)

    async def stop(self):
        """Stop watchdog monitoring"""
        self.running = False
        logger.info("👁️  Watchdog stopped")

    async def _check_all_agents(self):
        """Check health of all agents"""
        if not hasattr(self, "orchestrator"):
            return

        for agent_name, agent in self.orchestrator.agents.items():
            await self._check_agent(agent_name, agent)

    async def _check_agent(self, agent_name: str, agent):
        """
        Evaluate a single agent's health and dispatch the appropriate watchdog handlers.
        
        Calls the agent's async health_check() and:
        - invokes _handle_agent_failure if the reported status is "failed";
        - invokes _handle_agent_degraded if the reported status is "degraded" or "recovering";
        - invokes _handle_agent_recovery if the agent was previously tracked as having errors and is now healthy.
        If the health check raises an exception, records the error via _handle_agent_error.
        
        Parameters:
            agent_name (str): Identifier of the agent being checked.
            agent: Agent instance providing an async `health_check()` method that returns a dict containing a `"status"` key.
        """
        try:
            health = await agent.health_check()

            # Check if agent is failing
            if health.get("status") == "failed":
                await self._handle_agent_failure(agent_name, agent)
            elif health.get("status") in ["degraded", "recovering"]:
                await self._handle_agent_degraded(agent_name, agent)
            # Agent healthy - clear error count
            elif agent_name in self.agent_error_counts:
                await self._handle_agent_recovery(agent_name)

        except Exception as e:
            logger.error(f"Watchdog check failed for {agent_name}: {e!s}")
            await self._handle_agent_error(agent_name, str(e))

    async def _handle_agent_failure(self, agent_name: str, agent):
        """
        Handle a detected agent failure by updating state and deciding whether to restart or halt the agent.
        
        Parameters:
        	agent_name (str): Identifier of the failing agent.
        	agent: The agent instance to restart if a restart is attempted.
        """
        logger.error(f"❌ Agent {agent_name} has failed")

        # Increment error count
        if agent_name not in self.agent_error_counts:
            self.agent_error_counts[agent_name] = 0
        self.agent_error_counts[agent_name] += 1

        error_count = self.agent_error_counts[agent_name]
        error_threshold = self.config["error_threshold"]

        if error_count >= error_threshold:
            # Repeated failures - halt and notify
            await self._halt_agent(agent_name, "repeated_failures")
        else:
            # Attempt restart
            await self._restart_agent(agent_name, agent)

    async def _handle_agent_degraded(self, agent_name: str, agent):
        """Handle degraded agent"""
        logger.warning(f"⚠️  Agent {agent_name} is degraded")

        # Log but don't restart - agent is still functional
        self._log_incident({
            "type": "agent_degraded",
            "agent_name": agent_name,
            "timestamp": datetime.now().isoformat(),
            "action": "monitoring"
        })

    async def _handle_agent_error(self, agent_name: str, error: str):
        """Handle agent error"""
        logger.error(f"❌ Error monitoring {agent_name}: {error}")

        self._log_incident({
            "type": "monitoring_error",
            "agent_name": agent_name,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })

    async def _restart_agent(self, agent_name: str, agent):
        """
        Attempt to restart the specified agent and record the outcome.
        
        If the agent has reached the configured maximum restart attempts the agent is halted with reason "max_restarts_exceeded". Otherwise this method attempts to reinitialize the agent via its `initialize()` coroutine; on successful initialization the agent's restart count is incremented and an "agent_restarted" incident is logged. If initialization fails or raises an exception the agent is halted with an appropriate reason (e.g., "restart_failed" or "restart_error: <error>").
        
        Parameters:
            agent_name (str): The unique name of the agent to restart.
            agent: An agent instance that exposes an async `initialize()` method which returns `True` on success and `False` on a recoverable failure.
        """
        if agent_name not in self.agent_restart_counts:
            self.agent_restart_counts[agent_name] = 0

        if self.agent_restart_counts[agent_name] >= self.max_restart_attempts:
            await self._halt_agent(agent_name, "max_restarts_exceeded")
            return

        logger.info(f"🔄 Attempting to restart {agent_name}")

        try:
            # Reinitialize agent
            success = await agent.initialize()

            if success:
                logger.info(f"✅ Agent {agent_name} restarted successfully")
                self.agent_restart_counts[agent_name] += 1
                self._log_incident({
                    "type": "agent_restarted",
                    "agent_name": agent_name,
                    "attempt": self.agent_restart_counts[agent_name],
                    "timestamp": datetime.now().isoformat(),
                    "success": True
                })
            else:
                logger.error(f"❌ Failed to restart {agent_name}")
                await self._halt_agent(agent_name, "restart_failed")

        except Exception as e:
            logger.error(f"❌ Error restarting {agent_name}: {e!s}")
            await self._halt_agent(agent_name, f"restart_error: {e!s}")

    async def _halt_agent(self, agent_name: str, reason: str):
        """
        Halt an agent, record halt details in the watchdog state, create a halt incident, and notify an operator.
        
        Parameters:
            agent_name (str): Identifier of the agent to halt.
            reason (str): Human-readable reason for halting the agent.
        """
        logger.critical(f"🛑 HALTING AGENT {agent_name}: {reason}")

        self.halted_agents[agent_name] = {
            "reason": reason,
            "halted_at": datetime.now().isoformat(),
            "error_count": self.agent_error_counts.get(agent_name, 0),
            "restart_attempts": self.agent_restart_counts.get(agent_name, 0)
        }

        # Create incident report
        incident = {
            "type": "agent_halted",
            "agent_name": agent_name,
            "reason": reason,
            "error_count": self.agent_error_counts.get(agent_name, 0),
            "restart_attempts": self.agent_restart_counts.get(agent_name, 0),
            "timestamp": datetime.now().isoformat(),
            "requires_operator_intervention": True
        }

        self._log_incident(incident)
        await self._notify_operator(incident)

    async def _handle_agent_recovery(self, agent_name: str):
        """
        Record and handle recovery of an agent.
        
        Clears stored error and restart counters for the specified agent, logs an informational recovery message, and records an "agent_recovered" incident with a timestamp.
        
        Parameters:
            agent_name (str): Name or identifier of the recovered agent.
        """
        logger.info(f"✅ Agent {agent_name} recovered")

        # Clear error count
        if agent_name in self.agent_error_counts:
            del self.agent_error_counts[agent_name]

        # Reset restart count
        if agent_name in self.agent_restart_counts:
            del self.agent_restart_counts[agent_name]

        self._log_incident({
            "type": "agent_recovered",
            "agent_name": agent_name,
            "timestamp": datetime.now().isoformat()
        })

    def _log_incident(self, incident: dict):
        """
        Append an incident record to the in-memory incident list and persist it as a JSON line in the daily incident log file.
        
        Parameters:
            incident (dict): Incident data to record; appended to self.incidents and written (as one JSON line) to the daily file at self.incident_log_path/incidents_YYYYMMDD.jsonl (created if missing).
        """
        self.incidents.append(incident)

        # Write to incident log
        incident_file = self.incident_log_path / f"incidents_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(incident_file, "a") as f:
            f.write(json.dumps(incident) + "\n")

    async def _notify_operator(self, incident: dict):
        """
        Notify an operator about a critical incident and enqueue the notification.
        
        Appends a copy of `incident` augmented with a `notification_sent_at` ISO timestamp to
        fashion_ai_bounded_autonomy/notifications.json and logs a critical, pretty-printed message.
        If the notifications file does not exist it will be created.
        
        Parameters:
            incident (dict): Incident details to notify the operator about; this dictionary will be
                written (with an added `notification_sent_at` field) to the notifications file.
        """
        logger.critical(f"🚨 OPERATOR NOTIFICATION REQUIRED: {json.dumps(incident, indent=2)}")

        # Write to notification queue
        notification_file = Path("fashion_ai_bounded_autonomy/notifications.json")
        notifications = []

        if notification_file.exists():
            with open(notification_file) as f:
                notifications = json.load(f)

        notifications.append({
            **incident,
            "notification_sent_at": datetime.now().isoformat()
        })

        with open(notification_file, "w") as f:
            json.dump(notifications, f, indent=2)

    async def get_status(self) -> dict:
        """
        Return the current runtime status of the Watchdog.
        
        Returns:
            status (dict): Mapping with keys:
                - "running": bool indicating whether monitoring is active.
                - "total_incidents": int total number of incidents recorded in memory.
                - "halted_agents": int count of currently halted agents.
                - "agents_with_errors": dict mapping agent name to current error count.
                - "agents_with_restarts": dict mapping agent name to restart attempt count.
                - "halted_details": the Watchdog's `halted_agents` value (details recorded when agents were halted).
        """
        return {
            "running": self.running,
            "total_incidents": len(self.incidents),
            "halted_agents": len(self.halted_agents),
            "agents_with_errors": {
                agent: count
                for agent, count in self.agent_error_counts.items()
            },
            "agents_with_restarts": {
                agent: count
                for agent, count in self.agent_restart_counts.items()
            },
            "halted_details": self.halted_agents
        }

    async def clear_agent_halt(self, agent_name: str, operator: str):
        """Clear agent halt status (operator override)"""
        if agent_name in self.halted_agents:
            del self.halted_agents[agent_name]

            if agent_name in self.agent_error_counts:
                del self.agent_error_counts[agent_name]

            if agent_name in self.agent_restart_counts:
                del self.agent_restart_counts[agent_name]

            logger.info(f"✅ Agent {agent_name} halt cleared by operator {operator}")

            return {"status": "cleared", "agent": agent_name, "operator": operator}
        else:
            return {"error": f"Agent {agent_name} is not halted"}
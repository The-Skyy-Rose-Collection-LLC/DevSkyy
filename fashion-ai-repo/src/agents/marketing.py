"""Marketing Agent - Campaign creation and analytics."""

import time
from pathlib import Path
from typing import Any, Dict, List

from .base import BaseAgent


class MarketingAgent(BaseAgent):
    """Agent responsible for marketing campaigns and content distribution."""

    def __init__(self, *args, **kwargs):
        """
        Initialize the MarketingAgent and prepare its campaigns storage.
        
        Sets the instance attribute `campaigns_path` to a "campaigns" subdirectory under the agent's `io_path` and ensures that directory exists (creating parent directories if needed).
        """
        super().__init__(name="MarketingAgent", *args, **kwargs)
        self.campaigns_path = self.io_path / "campaigns"
        self.campaigns_path.mkdir(parents=True, exist_ok=True)

    def get_supported_tasks(self) -> List[str]:
        """
        Return the list of supported task names the agent can process.
        
        Returns:
            List[str]: Supported task names: "announce", "create_campaign", "schedule_content", "analyze_engagement".
        """
        return ["announce", "create_campaign", "schedule_content", "analyze_engagement"]

    async def process_task(self, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatches the specified marketing task to the corresponding handler and returns the handler's result.
        
        Parameters:
            task_type (str): The marketing task to perform ("announce", "create_campaign", "schedule_content", or "analyze_engagement").
            payload (Dict[str, Any]): Task-specific parameters required by the chosen handler.
        
        Returns:
            Dict[str, Any]: A dictionary containing task-specific result data (announcement, campaign, schedule, or analysis).
        
        Raises:
            ValueError: If `task_type` is not one of the supported task types.
        """
        if task_type == "announce":
            return await self._announce_product(payload)
        elif task_type == "create_campaign":
            return await self._create_campaign(payload)
        elif task_type == "schedule_content":
            return await self._schedule_content(payload)
        elif task_type == "analyze_engagement":
            return await self._analyze_engagement(payload)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")

    async def _announce_product(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create and schedule an announcement for a product listing.
        
        Parameters:
            payload (Dict[str, Any]): Product information; expected keys include 'sku', 'name', and 'description'.
        
        Returns:
            Dict[str, Any]: Announcement details containing:
                - announcement_id: unique identifier string (e.g., "ANN-<timestamp>")
                - sku, name, description: echoed product fields
                - channels: list of distribution channels
                - scheduled_at: timestamp when the announcement was scheduled
                - status: announcement status (e.g., "scheduled")
        """
        self.logger.info(f"Announcing product: {payload.get('sku')}")

        sku = payload.get("sku")
        name = payload.get("name")
        description = payload.get("description")

        announcement = {
            "announcement_id": f"ANN-{int(time.time())}",
            "sku": sku,
            "name": name,
            "description": description,
            "channels": ["email", "social", "website"],
            "scheduled_at": time.time(),
            "status": "scheduled",
        }

        self.logger.info(f"Product announced: {sku}")
        return announcement

    async def _create_campaign(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a marketing campaign record from provided parameters.
        
        Parameters:
            payload (Dict[str, Any]): Input parameters. Recognized keys:
                - name (str): Campaign name (required).
                - type (str): Campaign type, defaults to "product_launch".
                - target_audience (str): Target audience identifier, defaults to "all".
        
        Returns:
            dict: Campaign details containing:
                - campaign_id (str): Generated identifier like "CAMP-<timestamp>".
                - name (str)
                - type (str)
                - target_audience (str)
                - status (str): Campaign status, set to "active".
                - created_at (float): Creation timestamp (seconds since epoch).
                - metrics (dict): Initial metrics with keys "impressions", "clicks", "conversions" set to 0.
        """
        self.logger.info(f"Creating campaign: {payload.get('name')}")

        campaign_name = payload.get("name")
        campaign_type = payload.get("type", "product_launch")
        target_audience = payload.get("target_audience", "all")

        campaign = {
            "campaign_id": f"CAMP-{int(time.time())}",
            "name": campaign_name,
            "type": campaign_type,
            "target_audience": target_audience,
            "status": "active",
            "created_at": time.time(),
            "metrics": {
                "impressions": 0,
                "clicks": 0,
                "conversions": 0,
            },
        }

        self.logger.info(f"Campaign created: {campaign['campaign_id']}")
        return campaign

    async def _schedule_content(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a schedule record for distributing content.
        
        Parameters:
            payload (Dict[str, Any]): Scheduling parameters. Expected keys:
                - content_id: identifier of the content to schedule.
                - channels (List[str], optional): Delivery channels; defaults to ["social"].
                - schedule_time (float, optional): UNIX timestamp for dispatch; defaults to one hour from now.
        
        Returns:
            Dict[str, Any]: Schedule object with keys `content_id`, `channels`, `schedule_time`, and `status` set to "scheduled".
        """
        self.logger.info(f"Scheduling content: {payload.get('content_id')}")

        content_id = payload.get("content_id")
        channels = payload.get("channels", ["social"])
        schedule_time = payload.get("schedule_time", time.time() + 3600)

        schedule = {
            "content_id": content_id,
            "channels": channels,
            "schedule_time": schedule_time,
            "status": "scheduled",
        }

        self.logger.info(f"Content scheduled: {content_id}")
        return schedule

    async def _analyze_engagement(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Produce engagement metrics for a campaign and record its revenue with the FinanceAgent.
        
        Parameters:
            payload (Dict[str, Any]): Input data that must include `campaign_id` identifying the campaign to analyze.
        
        Returns:
            Dict[str, Any]: Analysis dictionary containing:
                - `campaign_id` (str|None): The analyzed campaign identifier.
                - `metrics` (dict): Engagement metrics with keys `impressions`, `clicks`, `conversions`, `ctr`, `conversion_rate`, and `revenue_cents`.
                - `analyzed_at` (float): Epoch timestamp when the analysis was produced.
        
        Side effects:
            Sends a message to the FinanceAgent with task_type `"record_ledger"` and payload including `campaign_id` and `revenue_cents` for revenue tracking.
        """
        self.logger.info(f"Analyzing engagement for: {payload.get('campaign_id')}")

        campaign_id = payload.get("campaign_id")

        # Placeholder for analytics logic
        # In production, fetch from analytics service

        analysis = {
            "campaign_id": campaign_id,
            "metrics": {
                "impressions": 10000,
                "clicks": 500,
                "conversions": 25,
                "ctr": 5.0,  # Click-through rate
                "conversion_rate": 5.0,
                "revenue_cents": 300000,  # $3000
            },
            "analyzed_at": time.time(),
        }

        self.logger.info(f"Engagement analyzed for: {campaign_id}")

        # Send to Finance Agent for revenue tracking
        self.send_message(
            target_agent="FinanceAgent",
            task_type="record_ledger",
            payload={"campaign_id": campaign_id, "revenue_cents": analysis["metrics"]["revenue_cents"]},
        )

        return analysis
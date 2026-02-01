"""
Feedback Tracking & Adaptive Routing
=====================================

Tracks LLM response quality and user acceptance for adaptive routing.

Features:
- SQLite-based metrics storage
- Provider performance tracking
- Acceptance rate by task type
- Adaptive weight adjustment

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from llm.router import ModelProvider

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class ResponseMetric:
    """Metrics for a single LLM response."""

    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    provider: str = ""
    model: str = ""
    task_type: str = "general"
    quality_score: float = 0.0
    user_accepted: bool | None = None
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderStats:
    """Aggregated stats for a provider."""

    provider: str
    total_requests: int = 0
    accepted_count: int = 0
    rejected_count: int = 0
    pending_count: int = 0
    acceptance_rate: float = 0.0
    avg_quality_score: float = 0.0
    avg_latency_ms: float = 0.0
    total_cost_usd: float = 0.0

    # By task type
    task_stats: dict[str, dict[str, float]] = field(default_factory=dict)


# =============================================================================
# Feedback Tracker
# =============================================================================


class FeedbackTracker:
    """
    Tracks LLM response quality and user feedback.

    Usage:
        tracker = FeedbackTracker()

        # Record a response
        response_id = tracker.record(
            provider=ModelProvider.OPENAI,
            model="gpt-4o",
            task_type="product_description",
            quality_score=85.0,
            latency_ms=1200,
        )

        # Record user feedback
        tracker.record_feedback(response_id, accepted=True)

        # Get provider stats
        stats = tracker.get_provider_stats(ModelProvider.OPENAI)
        print(f"Acceptance rate: {stats.acceptance_rate:.1%}")
    """

    def __init__(self, db_path: str = "./data/feedback.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS response_metrics (
                    response_id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    model TEXT,
                    task_type TEXT DEFAULT 'general',
                    quality_score REAL DEFAULT 0,
                    user_accepted INTEGER,
                    latency_ms REAL DEFAULT 0,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    estimated_cost_usd REAL DEFAULT 0,
                    created_at TEXT,
                    metadata TEXT
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_provider
                ON response_metrics(provider)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_type
                ON response_metrics(task_type)
            """)

            conn.commit()

    def record(
        self,
        provider: ModelProvider | str,
        model: str = "",
        task_type: str = "general",
        quality_score: float = 0.0,
        latency_ms: float = 0.0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        estimated_cost_usd: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Record a response metric.

        Returns:
            response_id for later feedback recording
        """
        response_id = str(uuid.uuid4())
        provider_str = provider.value if isinstance(provider, ModelProvider) else provider

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO response_metrics
                (response_id, provider, model, task_type, quality_score,
                 latency_ms, input_tokens, output_tokens, estimated_cost_usd,
                 created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    response_id,
                    provider_str,
                    model,
                    task_type,
                    quality_score,
                    latency_ms,
                    input_tokens,
                    output_tokens,
                    estimated_cost_usd,
                    datetime.now(UTC).isoformat(),
                    json.dumps(metadata or {}),
                ),
            )
            conn.commit()

        logger.debug(f"Recorded metric {response_id} for {provider_str}")
        return response_id

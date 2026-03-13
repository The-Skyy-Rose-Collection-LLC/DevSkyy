"""
Autonomous Brand Learning Loop
================================

Closed-loop system that observes brand interactions, extracts patterns,
synthesizes insights, and feeds improved brand context back to all agents.

Architecture:
    OBSERVE → EXTRACT → LEARN → ADAPT → EMIT
       ↑                                    |
       └────────────────────────────────────┘

Integration Points:
    - Subscribes to: core.events.event_bus (brand-relevant events)
    - Reads from: orchestration.feedback_tracker (LLM quality metrics)
    - Updates: orchestration.brand_context (dynamic brand DNA)
    - Emits to: core.events.event_bus (BrandInsightLearned events)
    - Persists: SQLite (data/brand_learning.db)

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import json
import logging
import sqlite3
import statistics
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class SignalType(StrEnum):
    """Types of brand interactions the loop observes."""

    CONTENT_GENERATED = "content_generated"
    PRODUCT_DESCRIPTION = "product_description"
    MARKETING_COPY = "marketing_copy"
    SOCIAL_POST = "social_post"
    VISUAL_ASSET = "visual_asset"
    CUSTOMER_FEEDBACK = "customer_feedback"
    COMPETITIVE_INTEL = "competitive_intel"
    BRAND_VIOLATION = "brand_violation"
    QUALITY_GATE_RESULT = "quality_gate_result"


class InsightCategory(StrEnum):
    """Categories of extracted brand insights."""

    VOICE_PATTERN = "voice_pattern"
    COLOR_PREFERENCE = "color_preference"
    AUDIENCE_SIGNAL = "audience_signal"
    PRODUCT_LANGUAGE = "product_language"
    VISUAL_STYLE = "visual_style"
    COMPETITOR_TREND = "competitor_trend"
    CONVERSION_PATTERN = "conversion_pattern"
    BRAND_DRIFT = "brand_drift"


class InsightConfidence(StrEnum):
    """Confidence level of an extracted insight."""

    LOW = "low"  # < 5 signals, or conflicting evidence
    MEDIUM = "medium"  # 5-20 signals, consistent direction
    HIGH = "high"  # 20+ signals, strong pattern
    VERIFIED = "verified"  # Human-confirmed


class LoopPhase(StrEnum):
    """Current phase of the learning loop."""

    IDLE = "idle"
    OBSERVING = "observing"
    EXTRACTING = "extracting"
    LEARNING = "learning"
    ADAPTING = "adapting"
    EMITTING = "emitting"


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class BrandSignal:
    """A single brand interaction observed by the loop."""

    signal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    signal_type: SignalType = SignalType.CONTENT_GENERATED
    collection: str = ""
    sku: str = ""
    content: str = ""
    agent_id: str = ""
    provider: str = ""
    model: str = ""
    accepted: bool | None = None
    quality_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class BrandInsight:
    """An insight extracted from accumulated brand signals."""

    insight_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: InsightCategory = InsightCategory.VOICE_PATTERN
    title: str = ""
    description: str = ""
    evidence_count: int = 0
    confidence: InsightConfidence = InsightConfidence.LOW
    recommendations: list[str] = field(default_factory=list)
    affected_collections: list[str] = field(default_factory=list)
    signal_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    expires_at: str | None = None


@dataclass
class BrandAdaptation:
    """A concrete change applied to brand context based on an insight."""

    adaptation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    insight_id: str = ""
    field_path: str = ""  # e.g., "tone.descriptors", "colors.accent"
    old_value: Any = None
    new_value: Any = None
    applied_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    reverted: bool = False


@dataclass
class LoopState:
    """Current state of the learning loop."""

    phase: LoopPhase = LoopPhase.IDLE
    cycle_count: int = 0
    last_cycle_at: str | None = None
    signals_since_last_cycle: int = 0
    total_signals: int = 0
    total_insights: int = 0
    total_adaptations: int = 0
    active_insights: int = 0


# =============================================================================
# Brand Memory (Persistent Storage)
# =============================================================================


class BrandMemory:
    """
    Persistent storage for brand learning data.

    Uses SQLite for durability (same pattern as FeedbackTracker).
    Stores signals, insights, and adaptations with full audit trail.
    """

    def __init__(self, db_path: str = "./data/brand_learning.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS brand_signals (
                    signal_id TEXT PRIMARY KEY,
                    signal_type TEXT NOT NULL,
                    collection TEXT DEFAULT '',
                    sku TEXT DEFAULT '',
                    content TEXT DEFAULT '',
                    agent_id TEXT DEFAULT '',
                    provider TEXT DEFAULT '',
                    model TEXT DEFAULT '',
                    accepted INTEGER,
                    quality_score REAL DEFAULT 0,
                    metadata TEXT DEFAULT '{}',
                    timestamp TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS brand_insights (
                    insight_id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    evidence_count INTEGER DEFAULT 0,
                    confidence TEXT DEFAULT 'low',
                    recommendations TEXT DEFAULT '[]',
                    affected_collections TEXT DEFAULT '[]',
                    signal_ids TEXT DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    superseded_by TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS brand_adaptations (
                    adaptation_id TEXT PRIMARY KEY,
                    insight_id TEXT NOT NULL,
                    field_path TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    applied_at TEXT NOT NULL,
                    reverted INTEGER DEFAULT 0,
                    FOREIGN KEY (insight_id) REFERENCES brand_insights(insight_id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_signal_type
                ON brand_signals(signal_type)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_signal_collection
                ON brand_signals(collection)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_insight_category
                ON brand_insights(category)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_insight_confidence
                ON brand_insights(confidence)
            """)

            conn.commit()

    # -------------------------------------------------------------------------
    # Signal Operations
    # -------------------------------------------------------------------------

    def store_signal(self, signal: BrandSignal) -> str:
        """Store a brand signal. Returns signal_id."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO brand_signals
                (signal_id, signal_type, collection, sku, content, agent_id,
                 provider, model, accepted, quality_score, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    signal.signal_id,
                    signal.signal_type.value,
                    signal.collection,
                    signal.sku,
                    signal.content,
                    signal.agent_id,
                    signal.provider,
                    signal.model,
                    1 if signal.accepted else (0 if signal.accepted is False else None),
                    signal.quality_score,
                    json.dumps(signal.metadata),
                    signal.timestamp,
                ),
            )
            conn.commit()

        logger.debug("Stored brand signal %s [%s]", signal.signal_id[:8], signal.signal_type)
        return signal.signal_id

    def get_signals(
        self,
        *,
        signal_type: SignalType | None = None,
        collection: str | None = None,
        since: datetime | None = None,
        limit: int = 500,
    ) -> list[BrandSignal]:
        """Query signals with optional filters."""
        query = "SELECT * FROM brand_signals WHERE 1=1"
        params: list[Any] = []

        if signal_type:
            query += " AND signal_type = ?"
            params.append(signal_type.value)

        if collection:
            query += " AND collection = ?"
            params.append(collection)

        if since:
            query += " AND timestamp >= ?"
            params.append(since.isoformat())

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_signal(row) for row in rows]

    def count_signals(self, since: datetime | None = None) -> int:
        """Count signals, optionally since a timestamp."""
        query = "SELECT COUNT(*) FROM brand_signals"
        params: list[Any] = []

        if since:
            query += " WHERE timestamp >= ?"
            params.append(since.isoformat())

        with sqlite3.connect(self.db_path) as conn:
            return conn.execute(query, params).fetchone()[0]

    # -------------------------------------------------------------------------
    # Insight Operations
    # -------------------------------------------------------------------------

    def store_insight(self, insight: BrandInsight) -> str:
        """Store a brand insight. Returns insight_id."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO brand_insights
                (insight_id, category, title, description, evidence_count,
                 confidence, recommendations, affected_collections,
                 signal_ids, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    insight.insight_id,
                    insight.category.value,
                    insight.title,
                    insight.description,
                    insight.evidence_count,
                    insight.confidence.value,
                    json.dumps(insight.recommendations),
                    json.dumps(insight.affected_collections),
                    json.dumps(insight.signal_ids),
                    insight.created_at,
                    insight.expires_at,
                ),
            )
            conn.commit()

        logger.info(
            "Stored brand insight: %s [%s, %s confidence]",
            insight.title,
            insight.category,
            insight.confidence,
        )
        return insight.insight_id

    def get_active_insights(
        self,
        *,
        category: InsightCategory | None = None,
        min_confidence: InsightConfidence | None = None,
    ) -> list[BrandInsight]:
        """Get active (non-superseded, non-expired) insights."""
        query = """
            SELECT * FROM brand_insights
            WHERE superseded_by IS NULL
            AND (expires_at IS NULL OR expires_at > ?)
        """
        params: list[Any] = [datetime.now(UTC).isoformat()]

        if category:
            query += " AND category = ?"
            params.append(category.value)

        if min_confidence:
            confidence_order = ["low", "medium", "high", "verified"]
            min_idx = confidence_order.index(min_confidence.value)
            allowed = confidence_order[min_idx:]
            placeholders = ",".join("?" * len(allowed))
            query += f" AND confidence IN ({placeholders})"
            params.extend(allowed)

        query += " ORDER BY created_at DESC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_insight(row) for row in rows]

    def supersede_insight(self, old_id: str, new_id: str) -> None:
        """Mark an old insight as superseded by a newer one."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE brand_insights SET superseded_by = ? WHERE insight_id = ?",
                (new_id, old_id),
            )
            conn.commit()

    # -------------------------------------------------------------------------
    # Adaptation Operations
    # -------------------------------------------------------------------------

    def store_adaptation(self, adaptation: BrandAdaptation) -> str:
        """Store a brand adaptation. Returns adaptation_id."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO brand_adaptations
                (adaptation_id, insight_id, field_path, old_value, new_value,
                 applied_at, reverted)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    adaptation.adaptation_id,
                    adaptation.insight_id,
                    adaptation.field_path,
                    json.dumps(adaptation.old_value),
                    json.dumps(adaptation.new_value),
                    adaptation.applied_at,
                    0,
                ),
            )
            conn.commit()

        logger.info(
            "Applied brand adaptation: %s = %s → %s",
            adaptation.field_path,
            adaptation.old_value,
            adaptation.new_value,
        )
        return adaptation.adaptation_id

    def get_adaptations(
        self,
        *,
        insight_id: str | None = None,
        active_only: bool = True,
    ) -> list[BrandAdaptation]:
        """Get adaptations, optionally filtered."""
        query = "SELECT * FROM brand_adaptations WHERE 1=1"
        params: list[Any] = []

        if insight_id:
            query += " AND insight_id = ?"
            params.append(insight_id)

        if active_only:
            query += " AND reverted = 0"

        query += " ORDER BY applied_at DESC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        return [
            BrandAdaptation(
                adaptation_id=row["adaptation_id"],
                insight_id=row["insight_id"],
                field_path=row["field_path"],
                old_value=json.loads(row["old_value"]) if row["old_value"] else None,
                new_value=json.loads(row["new_value"]) if row["new_value"] else None,
                applied_at=row["applied_at"],
                reverted=bool(row["reverted"]),
            )
            for row in rows
        ]

    def revert_adaptation(self, adaptation_id: str) -> None:
        """Mark an adaptation as reverted."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE brand_adaptations SET reverted = 1 WHERE adaptation_id = ?",
                (adaptation_id,),
            )
            conn.commit()

    # -------------------------------------------------------------------------
    # Converters
    # -------------------------------------------------------------------------

    @staticmethod
    def _row_to_signal(row: sqlite3.Row) -> BrandSignal:
        accepted_raw = row["accepted"]
        accepted = True if accepted_raw == 1 else (False if accepted_raw == 0 else None)
        return BrandSignal(
            signal_id=row["signal_id"],
            signal_type=SignalType(row["signal_type"]),
            collection=row["collection"],
            sku=row["sku"],
            content=row["content"],
            agent_id=row["agent_id"],
            provider=row["provider"],
            model=row["model"],
            accepted=accepted,
            quality_score=row["quality_score"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            timestamp=row["timestamp"],
        )

    @staticmethod
    def _row_to_insight(row: sqlite3.Row) -> BrandInsight:
        return BrandInsight(
            insight_id=row["insight_id"],
            category=InsightCategory(row["category"]),
            title=row["title"],
            description=row["description"],
            evidence_count=row["evidence_count"],
            confidence=InsightConfidence(row["confidence"]),
            recommendations=json.loads(row["recommendations"]) if row["recommendations"] else [],
            affected_collections=(
                json.loads(row["affected_collections"]) if row["affected_collections"] else []
            ),
            signal_ids=json.loads(row["signal_ids"]) if row["signal_ids"] else [],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
        )


# =============================================================================
# Pattern Extractors (EXTRACT phase)
# =============================================================================


class PatternExtractor:
    """
    Extracts brand patterns from accumulated signals.

    Each extractor method analyzes a specific signal dimension and
    returns insights when patterns emerge above noise threshold.
    """

    # Minimum signals before we trust a pattern
    MIN_SIGNALS_FOR_PATTERN = 5

    def extract_voice_patterns(self, signals: list[BrandSignal]) -> list[BrandInsight]:
        """Analyze which brand voice elements get accepted vs rejected."""
        insights: list[BrandInsight] = []

        # Group by accepted/rejected
        accepted = [s for s in signals if s.accepted is True]
        rejected = [s for s in signals if s.accepted is False]

        if len(accepted) < self.MIN_SIGNALS_FOR_PATTERN:
            return insights

        # Acceptance rate by agent
        agent_rates: dict[str, dict[str, int]] = defaultdict(lambda: {"accepted": 0, "total": 0})
        for s in signals:
            if s.accepted is not None:
                agent_rates[s.agent_id]["total"] += 1
                if s.accepted:
                    agent_rates[s.agent_id]["accepted"] += 1

        # Find agents with significantly different acceptance rates
        for agent_id, rates in agent_rates.items():
            if rates["total"] < self.MIN_SIGNALS_FOR_PATTERN:
                continue
            rate = rates["accepted"] / rates["total"]
            if rate < 0.5:
                insights.append(
                    BrandInsight(
                        category=InsightCategory.VOICE_PATTERN,
                        title=f"Low acceptance for agent {agent_id}",
                        description=(
                            f"Agent {agent_id} has {rate:.0%} acceptance rate "
                            f"across {rates['total']} brand content outputs. "
                            f"Brand voice may need reinforcement for this agent."
                        ),
                        evidence_count=rates["total"],
                        confidence=self._confidence_from_count(rates["total"]),
                        recommendations=[
                            f"Review brand context injection for agent {agent_id}",
                            "Consider adding collection-specific voice examples",
                        ],
                        signal_ids=[
                            s.signal_id
                            for s in signals
                            if s.agent_id == agent_id and s.accepted is False
                        ][:20],
                    )
                )

        # Quality score distribution
        if accepted:
            avg_quality_accepted = statistics.mean(s.quality_score for s in accepted)
            if rejected:
                avg_quality_rejected = statistics.mean(s.quality_score for s in rejected)
                quality_gap = avg_quality_accepted - avg_quality_rejected

                if quality_gap > 15:
                    insights.append(
                        BrandInsight(
                            category=InsightCategory.VOICE_PATTERN,
                            title="Quality score predicts brand acceptance",
                            description=(
                                f"Accepted content scores {avg_quality_accepted:.1f} avg vs "
                                f"{avg_quality_rejected:.1f} for rejected. "
                                f"Gap of {quality_gap:.1f} points suggests quality "
                                f"scoring is a reliable brand-fit predictor."
                            ),
                            evidence_count=len(accepted) + len(rejected),
                            confidence=self._confidence_from_count(len(accepted) + len(rejected)),
                            recommendations=[
                                f"Set quality gate threshold at {avg_quality_rejected + quality_gap * 0.6:.0f}",
                                "Auto-reject content below this threshold for brand review",
                            ],
                        )
                    )

        return insights

    def extract_collection_patterns(self, signals: list[BrandSignal]) -> list[BrandInsight]:
        """Find collection-specific patterns in brand performance."""
        insights: list[BrandInsight] = []

        # Group by collection
        by_collection: dict[str, list[BrandSignal]] = defaultdict(list)
        for s in signals:
            if s.collection:
                by_collection[s.collection].append(s)

        collection_stats: dict[str, dict[str, float]] = {}
        for coll, coll_signals in by_collection.items():
            rated = [s for s in coll_signals if s.accepted is not None]
            if len(rated) < self.MIN_SIGNALS_FOR_PATTERN:
                continue

            accepted_count = sum(1 for s in rated if s.accepted)
            collection_stats[coll] = {
                "acceptance_rate": accepted_count / len(rated),
                "avg_quality": statistics.mean(s.quality_score for s in rated),
                "count": len(rated),
            }

        if len(collection_stats) < 2:
            return insights

        # Find underperforming collections
        avg_rate = statistics.mean(s["acceptance_rate"] for s in collection_stats.values())
        for coll, stats in collection_stats.items():
            if stats["acceptance_rate"] < avg_rate - 0.15:
                insights.append(
                    BrandInsight(
                        category=InsightCategory.PRODUCT_LANGUAGE,
                        title=f"{coll} collection underperforming brand standards",
                        description=(
                            f"{coll} has {stats['acceptance_rate']:.0%} acceptance vs "
                            f"{avg_rate:.0%} average. Quality: {stats['avg_quality']:.1f}. "
                            f"Collection-specific brand context may need strengthening."
                        ),
                        evidence_count=int(stats["count"]),
                        confidence=self._confidence_from_count(int(stats["count"])),
                        recommendations=[
                            f"Review COLLECTION_CONTEXT for {coll}",
                            f"Add more mood/style descriptors for {coll}",
                            "Consider dedicated few-shot examples for this collection",
                        ],
                        affected_collections=[coll],
                    )
                )

        return insights

    def extract_provider_patterns(self, signals: list[BrandSignal]) -> list[BrandInsight]:
        """Analyze which LLM providers best capture brand voice."""
        insights: list[BrandInsight] = []

        # Group by provider
        by_provider: dict[str, list[BrandSignal]] = defaultdict(list)
        for s in signals:
            if s.provider:
                by_provider[s.provider].append(s)

        provider_stats: dict[str, dict[str, float]] = {}
        for prov, prov_signals in by_provider.items():
            rated = [s for s in prov_signals if s.accepted is not None]
            if len(rated) < self.MIN_SIGNALS_FOR_PATTERN:
                continue

            accepted_count = sum(1 for s in rated if s.accepted)
            provider_stats[prov] = {
                "acceptance_rate": accepted_count / len(rated),
                "avg_quality": statistics.mean(s.quality_score for s in rated),
                "count": len(rated),
            }

        if len(provider_stats) < 2:
            return insights

        # Find best provider for brand content
        best_prov = max(provider_stats, key=lambda p: provider_stats[p]["acceptance_rate"])
        best_stats = provider_stats[best_prov]

        if best_stats["acceptance_rate"] > 0.75 and best_stats["count"] >= 10:
            insights.append(
                BrandInsight(
                    category=InsightCategory.VOICE_PATTERN,
                    title=f"{best_prov} excels at brand voice",
                    description=(
                        f"{best_prov} achieves {best_stats['acceptance_rate']:.0%} "
                        f"brand acceptance ({best_stats['avg_quality']:.1f} quality) "
                        f"across {int(best_stats['count'])} outputs."
                    ),
                    evidence_count=int(best_stats["count"]),
                    confidence=self._confidence_from_count(int(best_stats["count"])),
                    recommendations=[
                        f"Prefer {best_prov} for brand-critical content generation",
                        "Route brand copy through this provider by default",
                    ],
                )
            )

        return insights

    def extract_signal_type_patterns(self, signals: list[BrandSignal]) -> list[BrandInsight]:
        """Analyze performance across different content types."""
        insights: list[BrandInsight] = []

        by_type: dict[str, list[BrandSignal]] = defaultdict(list)
        for s in signals:
            by_type[s.signal_type.value].append(s)

        type_stats: dict[str, dict[str, float]] = {}
        for sig_type, type_signals in by_type.items():
            rated = [s for s in type_signals if s.accepted is not None]
            if len(rated) < self.MIN_SIGNALS_FOR_PATTERN:
                continue

            accepted_count = sum(1 for s in rated if s.accepted)
            type_stats[sig_type] = {
                "acceptance_rate": accepted_count / len(rated),
                "avg_quality": statistics.mean(s.quality_score for s in rated),
                "count": len(rated),
            }

        # Identify content types with low brand adherence
        for sig_type, stats in type_stats.items():
            if stats["acceptance_rate"] < 0.6 and stats["count"] >= 5:
                insights.append(
                    BrandInsight(
                        category=InsightCategory.BRAND_DRIFT,
                        title=f"Brand drift in {sig_type} content",
                        description=(
                            f"{sig_type} content has only {stats['acceptance_rate']:.0%} "
                            f"acceptance rate across {int(stats['count'])} outputs. "
                            f"Brand voice injection may be insufficient for this content type."
                        ),
                        evidence_count=int(stats["count"]),
                        confidence=self._confidence_from_count(int(stats["count"])),
                        recommendations=[
                            f"Add specialized brand prompts for {sig_type}",
                            "Review rejected outputs to identify common deviations",
                        ],
                    )
                )

        return insights

    @staticmethod
    def _confidence_from_count(count: int) -> InsightConfidence:
        """Map evidence count to confidence level."""
        if count >= 20:
            return InsightConfidence.HIGH
        if count >= 5:
            return InsightConfidence.MEDIUM
        return InsightConfidence.LOW


# =============================================================================
# Brand Adaptor (ADAPT phase)
# =============================================================================


class BrandAdaptor:
    """
    Applies insights to the live brand context.

    Only HIGH or VERIFIED confidence insights trigger adaptations.
    All changes are recorded for auditability and revert capability.
    """

    # Only adapt on strong evidence
    MIN_CONFIDENCE_FOR_ADAPTATION = InsightConfidence.HIGH

    def __init__(self, memory: BrandMemory):
        self._memory = memory

    def apply_insight(
        self,
        insight: BrandInsight,
        brand_dict: dict[str, Any],
    ) -> list[BrandAdaptation]:
        """
        Apply an insight to the live brand context dict.

        Returns list of adaptations made (empty if insight doesn't
        meet confidence threshold or isn't actionable).
        """
        confidence_order = ["low", "medium", "high", "verified"]
        if confidence_order.index(insight.confidence.value) < confidence_order.index(
            self.MIN_CONFIDENCE_FOR_ADAPTATION.value
        ):
            return []

        adaptations: list[BrandAdaptation] = []

        if insight.category == InsightCategory.VOICE_PATTERN:
            adaptations.extend(self._adapt_voice(insight, brand_dict))
        elif insight.category == InsightCategory.PRODUCT_LANGUAGE:
            adaptations.extend(self._adapt_product_language(insight, brand_dict))
        elif insight.category == InsightCategory.BRAND_DRIFT:
            adaptations.extend(self._adapt_brand_drift(insight, brand_dict))

        # Persist all adaptations
        for adaptation in adaptations:
            self._memory.store_adaptation(adaptation)

        return adaptations

    def _adapt_voice(
        self,
        insight: BrandInsight,
        brand_dict: dict[str, Any],
    ) -> list[BrandAdaptation]:
        """Apply voice-related adaptations."""
        adaptations: list[BrandAdaptation] = []

        # If a provider excels, add routing hint to brand metadata
        if "excels at brand voice" in insight.title:
            provider = insight.title.split(" excels")[0]
            old_routing = brand_dict.get("_routing_hints", {})
            new_routing = {**old_routing, "preferred_brand_provider": provider}

            brand_dict["_routing_hints"] = new_routing
            adaptations.append(
                BrandAdaptation(
                    insight_id=insight.insight_id,
                    field_path="_routing_hints.preferred_brand_provider",
                    old_value=old_routing.get("preferred_brand_provider"),
                    new_value=provider,
                )
            )

        return adaptations

    def _adapt_product_language(
        self,
        insight: BrandInsight,
        brand_dict: dict[str, Any],
    ) -> list[BrandAdaptation]:
        """Apply product language adaptations."""
        adaptations: list[BrandAdaptation] = []

        # Flag underperforming collections for extra brand context injection
        for coll in insight.affected_collections:
            reinforcement_key = "_reinforcement_needed"
            old_list = brand_dict.get(reinforcement_key, [])
            if coll not in old_list:
                new_list = [*old_list, coll]
                brand_dict[reinforcement_key] = new_list
                adaptations.append(
                    BrandAdaptation(
                        insight_id=insight.insight_id,
                        field_path=reinforcement_key,
                        old_value=old_list,
                        new_value=new_list,
                    )
                )

        return adaptations

    def _adapt_brand_drift(
        self,
        insight: BrandInsight,
        brand_dict: dict[str, Any],
    ) -> list[BrandAdaptation]:
        """Apply brand drift corrections."""
        adaptations: list[BrandAdaptation] = []

        # Add drift-detected flag so BrandContextInjector uses full (non-compact) prompts
        drift_key = "_drift_detected_types"
        old_types = brand_dict.get(drift_key, [])
        # Extract signal type from title
        for sig_type in SignalType:
            if sig_type.value in insight.title:
                if sig_type.value not in old_types:
                    new_types = [*old_types, sig_type.value]
                    brand_dict[drift_key] = new_types
                    adaptations.append(
                        BrandAdaptation(
                            insight_id=insight.insight_id,
                            field_path=drift_key,
                            old_value=old_types,
                            new_value=new_types,
                        )
                    )
                break

        return adaptations

    def revert_insight(
        self,
        insight_id: str,
        brand_dict: dict[str, Any],
    ) -> int:
        """Revert all adaptations from a specific insight. Returns count reverted."""
        adaptations = self._memory.get_adaptations(insight_id=insight_id, active_only=True)
        reverted = 0

        for adaptation in adaptations:
            # Restore old value
            self._set_nested(brand_dict, adaptation.field_path, adaptation.old_value)
            self._memory.revert_adaptation(adaptation.adaptation_id)
            reverted += 1

        return reverted

    @staticmethod
    def _set_nested(d: dict[str, Any], path: str, value: Any) -> None:
        """Set a nested dict value by dot-separated path."""
        keys = path.split(".")
        for key in keys[:-1]:
            d = d.setdefault(key, {})
        if value is None:
            d.pop(keys[-1], None)
        else:
            d[keys[-1]] = value


# =============================================================================
# Autonomous Brand Learning Loop
# =============================================================================


class BrandLearningLoop:
    """
    The autonomous learning loop that ties everything together.

    Lifecycle:
        1. OBSERVE — Collect brand signals from agent outputs + user feedback
        2. EXTRACT — Run pattern extractors to find emerging insights
        3. LEARN   — Synthesize insights, merge with existing knowledge
        4. ADAPT   — Apply high-confidence insights to live brand context
        5. EMIT    — Broadcast BrandInsightLearned events for other agents

    The loop runs when signal_threshold signals have accumulated since
    the last cycle, or when manually triggered via run_cycle().

    Usage:
        from orchestration.brand_learning import BrandLearningLoop

        loop = BrandLearningLoop()

        # Record a signal (called by agents after generating content)
        loop.observe(BrandSignal(
            signal_type=SignalType.PRODUCT_DESCRIPTION,
            collection="BLACK_ROSE",
            sku="br-001",
            content="Premium heavyweight crewneck...",
            agent_id="content_core",
            provider="anthropic",
            model="claude-sonnet-4",
            accepted=True,
            quality_score=92.0,
        ))

        # Run a learning cycle (automatic when threshold reached)
        insights = await loop.run_cycle()

        # Get current state
        state = loop.get_state()

        # Get all active insights
        insights = loop.get_active_insights()
    """

    def __init__(
        self,
        *,
        db_path: str = "./data/brand_learning.db",
        signal_threshold: int = 10,
        lookback_hours: int = 168,  # 7 days
    ):
        self._memory = BrandMemory(db_path=db_path)
        self._extractor = PatternExtractor()
        self._adaptor = BrandAdaptor(self._memory)
        self._signal_threshold = signal_threshold
        self._lookback_hours = lookback_hours
        self._state = LoopState()
        self._event_bus = None
        self._brand_dict = None  # Reference to live SKYYROSE_BRAND dict

    def connect(
        self,
        *,
        brand_dict: dict[str, Any] | None = None,
        event_bus: Any | None = None,
    ) -> None:
        """
        Connect the loop to live systems.

        Args:
            brand_dict: Reference to SKYYROSE_BRAND dict (mutated in place)
            event_bus: core.events.event_bus for subscribing/emitting
        """
        if brand_dict is not None:
            self._brand_dict = brand_dict

        if event_bus is not None:
            self._event_bus = event_bus
            event_bus.subscribe(self._handle_event)
            logger.info("[brand_learning] Subscribed to event bus")

    # -------------------------------------------------------------------------
    # OBSERVE Phase
    # -------------------------------------------------------------------------

    def observe(self, signal: BrandSignal) -> str:
        """
        Record a brand signal from an agent interaction.

        Returns signal_id. Triggers learning cycle if threshold reached.
        """
        self._state.phase = LoopPhase.OBSERVING
        signal_id = self._memory.store_signal(signal)
        self._state.signals_since_last_cycle += 1
        self._state.total_signals += 1
        self._state.phase = LoopPhase.IDLE

        logger.debug(
            "[brand_learning] Signal %s recorded (%d since last cycle)",
            signal_id[:8],
            self._state.signals_since_last_cycle,
        )

        return signal_id

    def should_run_cycle(self) -> bool:
        """Check if enough signals accumulated to warrant a learning cycle."""
        return self._state.signals_since_last_cycle >= self._signal_threshold

    # -------------------------------------------------------------------------
    # Full Learning Cycle
    # -------------------------------------------------------------------------

    async def run_cycle(self) -> list[BrandInsight]:
        """
        Execute a full OBSERVE→EXTRACT→LEARN→ADAPT→EMIT cycle.

        Returns list of new insights discovered this cycle.
        """
        logger.info(
            "[brand_learning] Starting cycle %d (%d signals pending)",
            self._state.cycle_count + 1,
            self._state.signals_since_last_cycle,
        )

        # EXTRACT
        self._state.phase = LoopPhase.EXTRACTING
        since = datetime.now(UTC) - timedelta(hours=self._lookback_hours)
        signals = self._memory.get_signals(since=since)

        if not signals:
            logger.info("[brand_learning] No signals in lookback window, skipping cycle")
            self._state.phase = LoopPhase.IDLE
            return []

        raw_insights: list[BrandInsight] = []
        raw_insights.extend(self._extractor.extract_voice_patterns(signals))
        raw_insights.extend(self._extractor.extract_collection_patterns(signals))
        raw_insights.extend(self._extractor.extract_provider_patterns(signals))
        raw_insights.extend(self._extractor.extract_signal_type_patterns(signals))

        # LEARN — deduplicate and merge with existing insights
        self._state.phase = LoopPhase.LEARNING
        new_insights = self._deduplicate_insights(raw_insights)

        for insight in new_insights:
            self._memory.store_insight(insight)
            self._state.total_insights += 1

        # ADAPT — apply high-confidence insights to brand context
        self._state.phase = LoopPhase.ADAPTING
        total_adaptations = 0
        if self._brand_dict is not None:
            for insight in new_insights:
                adaptations = self._adaptor.apply_insight(insight, self._brand_dict)
                total_adaptations += len(adaptations)
                self._state.total_adaptations += len(adaptations)

        # EMIT — broadcast events
        self._state.phase = LoopPhase.EMITTING
        if self._event_bus is not None:
            for insight in new_insights:
                await self._emit_insight_event(insight)

        # Update cycle state
        self._state.cycle_count += 1
        self._state.last_cycle_at = datetime.now(UTC).isoformat()
        self._state.signals_since_last_cycle = 0
        self._state.active_insights = len(
            self._memory.get_active_insights(min_confidence=InsightConfidence.MEDIUM)
        )
        self._state.phase = LoopPhase.IDLE

        logger.info(
            "[brand_learning] Cycle %d complete: %d insights, %d adaptations (from %d signals)",
            self._state.cycle_count,
            len(new_insights),
            total_adaptations,
            len(signals),
        )

        return new_insights

    # -------------------------------------------------------------------------
    # Queries
    # -------------------------------------------------------------------------

    def get_state(self) -> LoopState:
        """Get current loop state."""
        return self._state

    def get_active_insights(
        self,
        *,
        category: InsightCategory | None = None,
        min_confidence: InsightConfidence | None = None,
    ) -> list[BrandInsight]:
        """Get all active brand insights."""
        return self._memory.get_active_insights(
            category=category,
            min_confidence=min_confidence,
        )

    def get_brand_health_report(self) -> dict[str, Any]:
        """
        Generate a brand health report from accumulated data.

        Returns a summary of brand performance, active insights,
        drift warnings, and recommended actions.
        """
        since = datetime.now(UTC) - timedelta(hours=self._lookback_hours)
        signals = self._memory.get_signals(since=since)
        active_insights = self._memory.get_active_insights()
        active_adaptations = self._memory.get_adaptations(active_only=True)

        # Acceptance rate
        rated = [s for s in signals if s.accepted is not None]
        acceptance_rate = sum(1 for s in rated if s.accepted) / len(rated) if rated else 0.0

        # Quality distribution
        quality_scores = [s.quality_score for s in signals if s.quality_score > 0]
        avg_quality = statistics.mean(quality_scores) if quality_scores else 0.0

        # Collection breakdown
        collection_health: dict[str, dict[str, Any]] = {}
        for s in rated:
            if s.collection:
                if s.collection not in collection_health:
                    collection_health[s.collection] = {"accepted": 0, "total": 0}
                collection_health[s.collection]["total"] += 1
                if s.accepted:
                    collection_health[s.collection]["accepted"] += 1

        for coll, stats in collection_health.items():
            stats["acceptance_rate"] = (
                stats["accepted"] / stats["total"] if stats["total"] > 0 else 0.0
            )

        # Drift warnings
        drift_insights = [i for i in active_insights if i.category == InsightCategory.BRAND_DRIFT]

        return {
            "period_hours": self._lookback_hours,
            "total_signals": len(signals),
            "acceptance_rate": acceptance_rate,
            "avg_quality_score": avg_quality,
            "collection_health": collection_health,
            "active_insights": len(active_insights),
            "active_adaptations": len(active_adaptations),
            "drift_warnings": len(drift_insights),
            "cycle_count": self._state.cycle_count,
            "recommendations": [
                rec for insight in active_insights for rec in insight.recommendations
            ][:10],
        }

    # -------------------------------------------------------------------------
    # Internals
    # -------------------------------------------------------------------------

    def _deduplicate_insights(self, raw_insights: list[BrandInsight]) -> list[BrandInsight]:
        """
        Deduplicate raw insights against existing active insights.

        If a new insight is about the same topic as an existing one,
        supersede the old one (preserving history).
        """
        existing = self._memory.get_active_insights()
        existing_titles = {i.title: i for i in existing}
        unique: list[BrandInsight] = []

        for insight in raw_insights:
            if insight.title in existing_titles:
                old = existing_titles[insight.title]
                # Supersede if new evidence is stronger
                if insight.evidence_count > old.evidence_count:
                    self._memory.supersede_insight(old.insight_id, insight.insight_id)
                    unique.append(insight)
            else:
                unique.append(insight)

        return unique

    async def _emit_insight_event(self, insight: BrandInsight) -> None:
        """Emit a BrandInsightLearned event to the event bus."""
        if self._event_bus is None:
            return

        from core.events.event_store import Event

        event = Event(
            event_type="BrandInsightLearned",
            aggregate_id=insight.insight_id,
            aggregate_type="BrandInsight",
            data={
                "category": insight.category.value,
                "title": insight.title,
                "confidence": insight.confidence.value,
                "evidence_count": insight.evidence_count,
                "recommendations": insight.recommendations,
                "affected_collections": insight.affected_collections,
            },
        )

        await self._event_bus.publish(event)
        logger.debug("[brand_learning] Emitted BrandInsightLearned: %s", insight.title)

    async def _handle_event(self, event: Any) -> None:
        """Handle incoming events from the event bus for auto-observation."""
        # Auto-observe relevant events
        event_type = getattr(event, "event_type", "")
        data = getattr(event, "data", {})

        if event_type in (
            "ContentGenerated",
            "ProductDescriptionCreated",
            "MarketingCopyCreated",
            "VisualAssetGenerated",
        ):
            signal_type_map = {
                "ContentGenerated": SignalType.CONTENT_GENERATED,
                "ProductDescriptionCreated": SignalType.PRODUCT_DESCRIPTION,
                "MarketingCopyCreated": SignalType.MARKETING_COPY,
                "VisualAssetGenerated": SignalType.VISUAL_ASSET,
            }
            self.observe(
                BrandSignal(
                    signal_type=signal_type_map[event_type],
                    collection=data.get("collection", ""),
                    sku=data.get("sku", ""),
                    content=data.get("content", ""),
                    agent_id=data.get("agent_id", ""),
                    provider=data.get("provider", ""),
                    model=data.get("model", ""),
                    quality_score=data.get("quality_score", 0.0),
                )
            )

        elif event_type == "ContentAccepted":
            # Update signal acceptance
            signal_id = data.get("signal_id", "")
            if signal_id:
                self._update_signal_acceptance(signal_id, accepted=True)

        elif event_type == "ContentRejected":
            signal_id = data.get("signal_id", "")
            if signal_id:
                self._update_signal_acceptance(signal_id, accepted=False)

    def _update_signal_acceptance(self, signal_id: str, *, accepted: bool) -> None:
        """Update a signal's acceptance status."""
        with sqlite3.connect(self._memory.db_path) as conn:
            conn.execute(
                "UPDATE brand_signals SET accepted = ? WHERE signal_id = ?",
                (1 if accepted else 0, signal_id),
            )
            conn.commit()


# =============================================================================
# Convenience Functions
# =============================================================================


def create_brand_learning_loop(
    *,
    signal_threshold: int = 10,
    lookback_hours: int = 168,
    auto_connect: bool = True,
) -> BrandLearningLoop:
    """
    Create and optionally wire up the brand learning loop.

    Args:
        signal_threshold: Signals needed before auto-triggering a cycle.
        lookback_hours: How far back to analyze (default: 7 days).
        auto_connect: If True, connect to live brand dict and event bus.

    Returns:
        Configured BrandLearningLoop instance.
    """
    loop = BrandLearningLoop(
        signal_threshold=signal_threshold,
        lookback_hours=lookback_hours,
    )

    if auto_connect:
        from orchestration.brand_context import SKYYROSE_BRAND

        try:
            from core.events import event_bus

            loop.connect(brand_dict=SKYYROSE_BRAND, event_bus=event_bus)
        except ImportError:
            loop.connect(brand_dict=SKYYROSE_BRAND)

    return loop


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "BrandAdaptation",
    "BrandAdaptor",
    "BrandInsight",
    "BrandLearningLoop",
    "BrandMemory",
    "BrandSignal",
    "InsightCategory",
    "InsightConfidence",
    "LoopPhase",
    "LoopState",
    "PatternExtractor",
    "SignalType",
    "create_brand_learning_loop",
]

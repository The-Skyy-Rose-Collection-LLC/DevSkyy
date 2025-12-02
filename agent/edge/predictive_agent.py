"""
Predictive Agent - Pre-computation and predictive prefetching for edge

Design Principle: Anticipate user needs and pre-compute/prefetch data
to achieve instant (<50ms) response when the user actually needs it.

Features:
- User behavior pattern learning
- Predictive prefetching of likely-needed data
- Pre-computation of common operations
- Confidence-based prediction with thresholds
- Resource-aware prefetching (CPU, memory, bandwidth)

Per CLAUDE.md Truth Protocol:
- Rule #1: Predictions based on verified patterns
- Rule #7: Pydantic validation for prediction requests
- Rule #12: Prefetch hit rate target >60%
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import math
from typing import Any

from pydantic import BaseModel, Field

from agent.edge.base_edge_agent import (
    BaseEdgeAgent,
    ExecutionLocation,
    OfflineCapability,
    SyncPriority,
)


logger = logging.getLogger(__name__)


class PredictionType(Enum):
    """Types of predictions supported"""

    NEXT_ACTION = "next_action"  # What user will do next
    DATA_NEED = "data_need"  # What data user will need
    RESOURCE_USAGE = "resource_usage"  # Future resource requirements
    USER_INTENT = "user_intent"  # High-level user goal


class PrefetchStrategy(Enum):
    """Prefetching strategies"""

    EAGER = "eager"  # Prefetch aggressively
    CONSERVATIVE = "conservative"  # Only high-confidence
    ADAPTIVE = "adaptive"  # Adjust based on hit rate
    BANDWIDTH_AWARE = "bandwidth_aware"  # Consider bandwidth limits


class PredictionRequest(BaseModel):
    """Request for prediction (Pydantic validated)"""

    user_id: str = Field(..., min_length=1, max_length=128)
    context: dict[str, Any] = Field(default_factory=dict)
    prediction_type: PredictionType = PredictionType.NEXT_ACTION
    include_confidence: bool = True
    max_predictions: int = Field(default=5, ge=1, le=20)


class Prediction(BaseModel):
    """Individual prediction result"""

    prediction_id: str
    prediction_type: PredictionType
    predicted_value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""
    prefetch_recommended: bool = False
    prefetch_priority: int = Field(default=0, ge=0, le=100)
    timestamp: datetime = Field(default_factory=datetime.now)


@dataclass
class UserPattern:
    """Learned pattern for a user's behavior"""

    user_id: str
    pattern_type: str
    sequence: list[str] = field(default_factory=list)
    frequency: int = 0
    last_seen: datetime = field(default_factory=datetime.now)
    avg_interval_seconds: float = 0.0
    confidence: float = 0.0


@dataclass
class PrefetchedItem:
    """Pre-fetched data item"""

    key: str
    value: Any
    prefetched_at: datetime = field(default_factory=datetime.now)
    predicted_need_time: datetime | None = None
    was_used: bool = False
    used_at: datetime | None = None
    prediction_confidence: float = 0.0


@dataclass
class PredictiveMetrics:
    """Metrics for prediction performance"""

    predictions_made: int = 0
    prefetches_triggered: int = 0
    prefetch_hits: int = 0
    prefetch_misses: int = 0
    average_confidence: float = 0.0
    patterns_learned: int = 0
    bandwidth_saved_bytes: int = 0
    latency_saved_ms: float = 0.0


class PatternMatcher:
    """Simple pattern matching for user behavior sequences."""

    def __init__(self, max_sequence_length: int = 10):
        self.max_sequence_length = max_sequence_length
        self._patterns: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self._sequence_counts: dict[str, int] = defaultdict(int)

    def learn(self, sequence: list[str]) -> None:
        """Learn patterns from action sequence."""
        for i in range(len(sequence) - 1):
            # Learn pairs
            current = sequence[i]
            next_action = sequence[i + 1]
            self._patterns[current][next_action] += 1
            self._sequence_counts[current] += 1

            # Learn triplets
            if i < len(sequence) - 2:
                pair = f"{sequence[i]}:{sequence[i + 1]}"
                next_after_pair = sequence[i + 2]
                self._patterns[pair][next_after_pair] += 1
                self._sequence_counts[pair] += 1

    def predict_next(
        self, recent_actions: list[str], top_k: int = 5
    ) -> list[tuple[str, float]]:
        """
        Predict next likely actions based on recent actions.

        Returns list of (action, probability) tuples.
        """
        predictions: dict[str, float] = defaultdict(float)

        if not recent_actions:
            return []

        # Single action context
        last_action = recent_actions[-1]
        if last_action in self._patterns:
            total = self._sequence_counts[last_action]
            for next_action, count in self._patterns[last_action].items():
                prob = count / total
                predictions[next_action] = max(predictions[next_action], prob)

        # Pair context (if available)
        if len(recent_actions) >= 2:
            pair = f"{recent_actions[-2]}:{recent_actions[-1]}"
            if pair in self._patterns:
                total = self._sequence_counts[pair]
                for next_action, count in self._patterns[pair].items():
                    prob = count / total
                    # Pair predictions weighted higher
                    predictions[next_action] = max(
                        predictions[next_action], prob * 1.2
                    )

        # Sort by probability and return top_k
        sorted_predictions = sorted(
            predictions.items(), key=lambda x: x[1], reverse=True
        )
        return [(action, min(prob, 1.0)) for action, prob in sorted_predictions[:top_k]]


class TimeBasedPredictor:
    """Predict based on time patterns (e.g., daily routines)."""

    def __init__(self):
        self._hourly_patterns: dict[str, dict[int, list[str]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._day_patterns: dict[str, dict[int, list[str]]] = defaultdict(
            lambda: defaultdict(list)
        )

    def learn(self, user_id: str, action: str, timestamp: datetime) -> None:
        """Learn time-based pattern."""
        hour = timestamp.hour
        day = timestamp.weekday()

        self._hourly_patterns[user_id][hour].append(action)
        self._day_patterns[user_id][day].append(action)

        # Keep bounded
        if len(self._hourly_patterns[user_id][hour]) > 100:
            self._hourly_patterns[user_id][hour] = self._hourly_patterns[user_id][
                hour
            ][-50:]

    def predict_for_time(
        self, user_id: str, target_time: datetime, top_k: int = 5
    ) -> list[tuple[str, float]]:
        """Predict likely actions for a specific time."""
        hour = target_time.hour
        day = target_time.weekday()

        action_scores: dict[str, float] = defaultdict(float)

        # Hour-based predictions
        hourly_actions = self._hourly_patterns[user_id].get(hour, [])
        if hourly_actions:
            action_counts = defaultdict(int)
            for action in hourly_actions:
                action_counts[action] += 1
            total = len(hourly_actions)
            for action, count in action_counts.items():
                action_scores[action] += (count / total) * 0.7

        # Day-based predictions
        daily_actions = self._day_patterns[user_id].get(day, [])
        if daily_actions:
            action_counts = defaultdict(int)
            for action in daily_actions:
                action_counts[action] += 1
            total = len(daily_actions)
            for action, count in action_counts.items():
                action_scores[action] += (count / total) * 0.3

        sorted_predictions = sorted(
            action_scores.items(), key=lambda x: x[1], reverse=True
        )
        return sorted_predictions[:top_k]


class PredictiveAgent(BaseEdgeAgent):
    """
    Predictive Agent - Pre-computation and predictive prefetching.

    Features:
    - Pattern-based behavior prediction
    - Time-based prediction (daily routines)
    - Confidence-scored predictions
    - Resource-aware prefetching
    - Learning from outcomes

    Target metrics:
    - Prefetch hit rate: >60%
    - Prediction latency: <20ms
    - Resource efficiency: <10% overhead
    """

    PREDICTION_LATENCY_TARGET_MS: float = 20.0
    MIN_CONFIDENCE_THRESHOLD: float = 0.3
    PREFETCH_CONFIDENCE_THRESHOLD: float = 0.5
    MAX_PREFETCH_ITEMS: int = 20
    PATTERN_LEARNING_WINDOW: int = 100

    def __init__(
        self,
        agent_name: str = "PredictiveAgent",
        version: str = "1.0.0",
        strategy: PrefetchStrategy = PrefetchStrategy.ADAPTIVE,
    ):
        super().__init__(
            agent_name=agent_name,
            version=version,
            offline_capability=OfflineCapability.FULL,
        )

        self.strategy = strategy
        self.metrics = PredictiveMetrics()

        # Pattern matching components
        self._pattern_matcher = PatternMatcher()
        self._time_predictor = TimeBasedPredictor()

        # User action history for learning
        self._user_actions: dict[str, list[tuple[str, datetime]]] = defaultdict(list)

        # Prefetched data storage
        self._prefetched: dict[str, PrefetchedItem] = {}

        # Prediction history for learning
        self._prediction_outcomes: list[dict[str, Any]] = []

        # Adaptive strategy parameters
        self._current_confidence_threshold = self.PREFETCH_CONFIDENCE_THRESHOLD
        self._prefetch_hit_rate = 0.6  # Initial estimate

        # Data need mappings (action -> data keys needed)
        self._action_data_mapping: dict[str, list[str]] = {}

        logger.info(f"PredictiveAgent initialized (strategy={strategy.value})")

    async def execute_local(self, operation: str, **kwargs) -> dict[str, Any]:
        """Execute prediction operation locally."""
        start_time = datetime.now()

        try:
            if operation == "predict_next":
                result = await self._handle_predict_next(kwargs)
            elif operation == "record_action":
                result = await self._handle_record_action(kwargs)
            elif operation == "prefetch":
                result = await self._handle_prefetch(kwargs)
            elif operation == "get_prefetched":
                result = await self._handle_get_prefetched(kwargs)
            elif operation == "register_data_mapping":
                result = self._register_data_mapping(kwargs)
            elif operation == "get_metrics":
                result = self._get_metrics()
            elif operation == "mark_used":
                result = self._mark_prefetch_used(kwargs)
            else:
                result = {"error": f"Unknown operation: {operation}"}

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            if elapsed_ms > self.PREDICTION_LATENCY_TARGET_MS:
                logger.warning(
                    f"Prediction operation {operation} exceeded target: "
                    f"{elapsed_ms:.2f}ms > {self.PREDICTION_LATENCY_TARGET_MS}ms"
                )

            return result

        except Exception as e:
            logger.error(f"Prediction operation {operation} failed: {e}")
            return {"error": str(e), "operation": operation}

    def get_routing_rules(self) -> dict[str, ExecutionLocation]:
        """Define routing rules for PredictiveAgent operations."""
        return {
            "predict_next": ExecutionLocation.EDGE,
            "record_action": ExecutionLocation.EDGE,
            "prefetch": ExecutionLocation.HYBRID,
            "get_prefetched": ExecutionLocation.EDGE,
            "register_data_mapping": ExecutionLocation.EDGE,
            "get_metrics": ExecutionLocation.EDGE,
            "mark_used": ExecutionLocation.EDGE,
            "train_model": ExecutionLocation.BACKEND,
            "analyze_patterns": ExecutionLocation.BACKEND,
            "predict_complex": ExecutionLocation.BACKEND,
        }

    # === Core Prediction Methods ===

    async def predict_next_actions(
        self, user_id: str, context: dict[str, Any] | None = None, top_k: int = 5
    ) -> list[Prediction]:
        """
        Predict likely next actions for a user.

        Combines:
        1. Pattern-based prediction (recent action sequences)
        2. Time-based prediction (daily routines)
        3. Context-based adjustments

        Args:
            user_id: User identifier
            context: Optional context for prediction
            top_k: Number of predictions to return

        Returns:
            List of Prediction objects
        """
        predictions: list[Prediction] = []
        context = context or {}

        # Get recent actions for this user
        recent = self._user_actions.get(user_id, [])
        recent_actions = [action for action, _ in recent[-10:]]

        # Pattern-based predictions
        pattern_predictions = self._pattern_matcher.predict_next(recent_actions, top_k)

        # Time-based predictions
        current_time = datetime.now()
        time_predictions = self._time_predictor.predict_for_time(
            user_id, current_time, top_k
        )

        # Combine predictions
        combined_scores: dict[str, float] = defaultdict(float)

        for action, prob in pattern_predictions:
            combined_scores[action] += prob * 0.7  # Pattern weight

        for action, prob in time_predictions:
            combined_scores[action] += prob * 0.3  # Time weight

        # Context adjustments
        current_page = context.get("current_page", "")
        for action in combined_scores:
            if current_page and current_page in action:
                combined_scores[action] *= 1.2  # Boost related actions

        # Create prediction objects
        sorted_actions = sorted(
            combined_scores.items(), key=lambda x: x[1], reverse=True
        )[:top_k]

        for i, (action, confidence) in enumerate(sorted_actions):
            prediction_id = f"pred_{datetime.now().timestamp()}_{i}"
            confidence = min(confidence, 1.0)

            # Determine if prefetch recommended
            prefetch_recommended = (
                confidence >= self._current_confidence_threshold
                and action in self._action_data_mapping
            )

            predictions.append(
                Prediction(
                    prediction_id=prediction_id,
                    prediction_type=PredictionType.NEXT_ACTION,
                    predicted_value=action,
                    confidence=confidence,
                    reasoning=self._generate_reasoning(action, pattern_predictions, time_predictions),
                    prefetch_recommended=prefetch_recommended,
                    prefetch_priority=int(confidence * 100),
                )
            )

        self.metrics.predictions_made += len(predictions)
        self._update_average_confidence(predictions)

        return predictions

    async def predict_data_needs(
        self, user_id: str, context: dict[str, Any] | None = None
    ) -> list[str]:
        """
        Predict data keys the user will likely need.

        Based on predicted actions and their data requirements.

        Args:
            user_id: User identifier
            context: Optional context

        Returns:
            List of data keys to prefetch
        """
        action_predictions = await self.predict_next_actions(user_id, context, top_k=5)

        data_keys: list[str] = []
        seen_keys: set[str] = set()

        for prediction in action_predictions:
            if prediction.confidence >= self.MIN_CONFIDENCE_THRESHOLD:
                action = prediction.predicted_value
                if action in self._action_data_mapping:
                    for key in self._action_data_mapping[action]:
                        if key not in seen_keys:
                            data_keys.append(key)
                            seen_keys.add(key)

        return data_keys[:self.MAX_PREFETCH_ITEMS]

    async def record_action(
        self, user_id: str, action: str, timestamp: datetime | None = None
    ) -> None:
        """
        Record a user action for learning.

        Updates pattern matcher and time predictor.

        Args:
            user_id: User identifier
            action: Action taken
            timestamp: Optional timestamp (defaults to now)
        """
        ts = timestamp or datetime.now()

        # Add to user history
        self._user_actions[user_id].append((action, ts))

        # Keep bounded
        if len(self._user_actions[user_id]) > self.PATTERN_LEARNING_WINDOW:
            self._user_actions[user_id] = self._user_actions[user_id][
                -self.PATTERN_LEARNING_WINDOW // 2 :
            ]

        # Update pattern matcher
        recent_actions = [a for a, _ in self._user_actions[user_id][-20:]]
        self._pattern_matcher.learn(recent_actions)

        # Update time predictor
        self._time_predictor.learn(user_id, action, ts)

        self.metrics.patterns_learned += 1

        # Check if any prefetched items were for this action
        self._check_prefetch_usage(action)

    def _check_prefetch_usage(self, action: str) -> None:
        """Check if prefetched data was used for this action."""
        if action in self._action_data_mapping:
            for key in self._action_data_mapping[action]:
                if key in self._prefetched:
                    item = self._prefetched[key]
                    if not item.was_used:
                        item.was_used = True
                        item.used_at = datetime.now()
                        self.metrics.prefetch_hits += 1

                        # Calculate latency saved
                        if item.predicted_need_time:
                            latency_saved = (
                                item.predicted_need_time - item.prefetched_at
                            ).total_seconds() * 1000
                            self.metrics.latency_saved_ms += max(0, latency_saved)

    # === Prefetching ===

    async def prefetch(
        self, key: str, value: Any, confidence: float, predicted_need_seconds: float = 30.0
    ) -> bool:
        """
        Store prefetched data.

        Args:
            key: Data key
            value: Prefetched value
            confidence: Prediction confidence
            predicted_need_seconds: Estimated time until needed

        Returns:
            True if stored
        """
        # Check capacity
        if len(self._prefetched) >= self.MAX_PREFETCH_ITEMS:
            # Evict least confident or oldest
            self._evict_prefetched()

        predicted_time = datetime.now() + timedelta(seconds=predicted_need_seconds)

        self._prefetched[key] = PrefetchedItem(
            key=key,
            value=value,
            predicted_need_time=predicted_time,
            prediction_confidence=confidence,
        )

        self.metrics.prefetches_triggered += 1
        logger.debug(f"Prefetched {key} (confidence={confidence:.2f})")
        return True

    def get_prefetched(self, key: str) -> tuple[Any, bool]:
        """
        Get prefetched data.

        Args:
            key: Data key

        Returns:
            Tuple of (value, found)
        """
        if key in self._prefetched:
            item = self._prefetched[key]
            item.was_used = True
            item.used_at = datetime.now()
            self.metrics.prefetch_hits += 1

            # Remove after use
            del self._prefetched[key]
            return item.value, True

        return None, False

    def _evict_prefetched(self) -> None:
        """Evict low-priority prefetched items."""
        if not self._prefetched:
            return

        # Sort by: unused and old first, then by confidence
        items = list(self._prefetched.items())
        items.sort(
            key=lambda x: (
                not x[1].was_used,
                -x[1].prediction_confidence,
                x[1].prefetched_at,
            )
        )

        # Remove lowest priority items
        num_to_remove = len(items) // 4 + 1
        for key, item in items[:num_to_remove]:
            if not item.was_used:
                self.metrics.prefetch_misses += 1
            del self._prefetched[key]

        self._update_adaptive_threshold()

    def _update_adaptive_threshold(self) -> None:
        """Update confidence threshold based on hit rate."""
        if self.strategy != PrefetchStrategy.ADAPTIVE:
            return

        total = self.metrics.prefetch_hits + self.metrics.prefetch_misses
        if total < 10:
            return

        hit_rate = self.metrics.prefetch_hits / total

        if hit_rate < 0.5:
            # Too many misses, be more conservative
            self._current_confidence_threshold = min(0.9, self._current_confidence_threshold + 0.05)
        elif hit_rate > 0.7:
            # Good hit rate, can be more aggressive
            self._current_confidence_threshold = max(0.3, self._current_confidence_threshold - 0.05)

        self._prefetch_hit_rate = hit_rate

    # === Helper Methods ===

    def _generate_reasoning(
        self,
        action: str,
        pattern_preds: list[tuple[str, float]],
        time_preds: list[tuple[str, float]],
    ) -> str:
        """Generate human-readable reasoning for prediction."""
        reasons = []

        pattern_score = next((p for a, p in pattern_preds if a == action), 0)
        time_score = next((p for a, p in time_preds if a == action), 0)

        if pattern_score > 0.3:
            reasons.append(f"follows recent behavior pattern ({pattern_score:.0%})")
        if time_score > 0.2:
            reasons.append(f"typical for this time ({time_score:.0%})")

        return "; ".join(reasons) if reasons else "general prediction"

    def _update_average_confidence(self, predictions: list[Prediction]) -> None:
        """Update rolling average confidence."""
        if not predictions:
            return

        avg = sum(p.confidence for p in predictions) / len(predictions)
        n = self.metrics.predictions_made
        self.metrics.average_confidence = (
            self.metrics.average_confidence * (n - len(predictions)) + avg * len(predictions)
        ) / n

    def _register_data_mapping(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Register action to data key mapping."""
        action = kwargs.get("action")
        data_keys = kwargs.get("data_keys", [])

        if not action:
            return {"error": "action is required"}

        self._action_data_mapping[action] = data_keys
        return {"registered": action, "data_keys": data_keys}

    def _get_metrics(self) -> dict[str, Any]:
        """Get prediction metrics."""
        total_prefetch = self.metrics.prefetch_hits + self.metrics.prefetch_misses
        hit_rate = (
            self.metrics.prefetch_hits / total_prefetch if total_prefetch > 0 else 0.0
        )

        return {
            "predictions_made": self.metrics.predictions_made,
            "prefetches_triggered": self.metrics.prefetches_triggered,
            "prefetch_hits": self.metrics.prefetch_hits,
            "prefetch_misses": self.metrics.prefetch_misses,
            "prefetch_hit_rate": round(hit_rate * 100, 2),
            "average_confidence": round(self.metrics.average_confidence, 2),
            "patterns_learned": self.metrics.patterns_learned,
            "latency_saved_ms": round(self.metrics.latency_saved_ms, 2),
            "current_threshold": round(self._current_confidence_threshold, 2),
            "prefetched_items": len(self._prefetched),
            "strategy": self.strategy.value,
        }

    def _mark_prefetch_used(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Mark a prefetched item as used."""
        key = kwargs.get("key")
        if not key:
            return {"error": "key is required"}

        if key in self._prefetched:
            self._prefetched[key].was_used = True
            self._prefetched[key].used_at = datetime.now()
            return {"marked": True}

        return {"marked": False, "reason": "key not found in prefetch"}

    # === Request Handlers ===

    async def _handle_predict_next(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Handle predict next request."""
        user_id = kwargs.get("user_id")
        context = kwargs.get("context", {})
        top_k = kwargs.get("top_k", 5)

        if not user_id:
            return {"error": "user_id is required"}

        predictions = await self.predict_next_actions(user_id, context, top_k)
        return {
            "predictions": [p.model_dump() for p in predictions],
            "count": len(predictions),
        }

    async def _handle_record_action(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Handle record action request."""
        user_id = kwargs.get("user_id")
        action = kwargs.get("action")

        if not user_id or not action:
            return {"error": "user_id and action are required"}

        await self.record_action(user_id, action)
        return {"recorded": True}

    async def _handle_prefetch(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Handle prefetch request."""
        key = kwargs.get("key")
        value = kwargs.get("value")
        confidence = kwargs.get("confidence", 0.5)

        if not key:
            return {"error": "key is required"}

        success = await self.prefetch(key, value, confidence)
        return {"prefetched": success}

    async def _handle_get_prefetched(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Handle get prefetched request."""
        key = kwargs.get("key")

        if not key:
            return {"error": "key is required"}

        value, found = self.get_prefetched(key)
        return {"value": value, "found": found}

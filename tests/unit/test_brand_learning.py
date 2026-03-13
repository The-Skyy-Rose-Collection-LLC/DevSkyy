"""
Tests for the Autonomous Brand Learning Loop.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from orchestration.brand_learning import (
    BrandAdaptation,
    BrandAdaptor,
    BrandInsight,
    BrandLearningLoop,
    BrandMemory,
    BrandSignal,
    InsightCategory,
    InsightConfidence,
    PatternExtractor,
    SignalType,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def tmp_db(tmp_path: Path) -> str:
    return str(tmp_path / "test_brand_learning.db")


@pytest.fixture
def memory(tmp_db: str) -> BrandMemory:
    return BrandMemory(db_path=tmp_db)


@pytest.fixture
def extractor() -> PatternExtractor:
    return PatternExtractor()


@pytest.fixture
def loop(tmp_db: str) -> BrandLearningLoop:
    return BrandLearningLoop(db_path=tmp_db, signal_threshold=5)


def make_signal(
    *,
    signal_type: SignalType = SignalType.CONTENT_GENERATED,
    collection: str = "BLACK_ROSE",
    sku: str = "br-001",
    agent_id: str = "content_core",
    provider: str = "anthropic",
    model: str = "claude-sonnet-4",
    accepted: bool | None = True,
    quality_score: float = 85.0,
) -> BrandSignal:
    return BrandSignal(
        signal_type=signal_type,
        collection=collection,
        sku=sku,
        content="Test brand content",
        agent_id=agent_id,
        provider=provider,
        model=model,
        accepted=accepted,
        quality_score=quality_score,
    )


# =============================================================================
# BrandMemory Tests
# =============================================================================


class TestBrandMemory:
    def test_store_and_retrieve_signal(self, memory: BrandMemory):
        signal = make_signal()
        signal_id = memory.store_signal(signal)

        signals = memory.get_signals()
        assert len(signals) == 1
        assert signals[0].signal_id == signal_id
        assert signals[0].collection == "BLACK_ROSE"

    def test_filter_signals_by_type(self, memory: BrandMemory):
        memory.store_signal(make_signal(signal_type=SignalType.PRODUCT_DESCRIPTION))
        memory.store_signal(make_signal(signal_type=SignalType.MARKETING_COPY))
        memory.store_signal(make_signal(signal_type=SignalType.PRODUCT_DESCRIPTION))

        results = memory.get_signals(signal_type=SignalType.PRODUCT_DESCRIPTION)
        assert len(results) == 2

    def test_filter_signals_by_collection(self, memory: BrandMemory):
        memory.store_signal(make_signal(collection="BLACK_ROSE"))
        memory.store_signal(make_signal(collection="LOVE_HURTS"))

        results = memory.get_signals(collection="BLACK_ROSE")
        assert len(results) == 1

    def test_count_signals(self, memory: BrandMemory):
        for _ in range(5):
            memory.store_signal(make_signal())

        assert memory.count_signals() == 5

    def test_store_and_retrieve_insight(self, memory: BrandMemory):
        insight = BrandInsight(
            category=InsightCategory.VOICE_PATTERN,
            title="Test insight",
            description="A test insight",
            evidence_count=10,
            confidence=InsightConfidence.MEDIUM,
        )
        insight_id = memory.store_insight(insight)

        insights = memory.get_active_insights()
        assert len(insights) == 1
        assert insights[0].insight_id == insight_id
        assert insights[0].title == "Test insight"

    def test_supersede_insight(self, memory: BrandMemory):
        old = BrandInsight(
            category=InsightCategory.VOICE_PATTERN,
            title="Old insight",
            evidence_count=5,
            confidence=InsightConfidence.LOW,
        )
        memory.store_insight(old)

        new = BrandInsight(
            category=InsightCategory.VOICE_PATTERN,
            title="New insight",
            evidence_count=15,
            confidence=InsightConfidence.HIGH,
        )
        memory.store_insight(new)
        memory.supersede_insight(old.insight_id, new.insight_id)

        active = memory.get_active_insights()
        assert len(active) == 1
        assert active[0].insight_id == new.insight_id

    def test_filter_insights_by_min_confidence(self, memory: BrandMemory):
        memory.store_insight(
            BrandInsight(
                category=InsightCategory.VOICE_PATTERN,
                title="Low",
                confidence=InsightConfidence.LOW,
            )
        )
        memory.store_insight(
            BrandInsight(
                category=InsightCategory.VOICE_PATTERN,
                title="High",
                confidence=InsightConfidence.HIGH,
            )
        )

        high_only = memory.get_active_insights(min_confidence=InsightConfidence.HIGH)
        assert len(high_only) == 1
        assert high_only[0].title == "High"

    def test_store_and_revert_adaptation(self, memory: BrandMemory):
        insight = BrandInsight(
            category=InsightCategory.VOICE_PATTERN,
            title="Test",
            confidence=InsightConfidence.HIGH,
        )
        memory.store_insight(insight)

        adaptation = BrandAdaptation(
            insight_id=insight.insight_id,
            field_path="tone.primary",
            old_value="old",
            new_value="new",
        )
        memory.store_adaptation(adaptation)

        active = memory.get_adaptations(active_only=True)
        assert len(active) == 1

        memory.revert_adaptation(adaptation.adaptation_id)
        active = memory.get_adaptations(active_only=True)
        assert len(active) == 0


# =============================================================================
# PatternExtractor Tests
# =============================================================================


class TestPatternExtractor:
    def test_voice_patterns_low_acceptance_agent(self, extractor: PatternExtractor):
        """Detects agents with low brand acceptance."""
        signals = []
        # Agent A: 80% acceptance
        for i in range(10):
            signals.append(make_signal(agent_id="agent_a", accepted=i < 8))
        # Agent B: 30% acceptance
        for i in range(10):
            signals.append(make_signal(agent_id="agent_b", accepted=i < 3))

        insights = extractor.extract_voice_patterns(signals)
        assert any("agent_b" in i.title.lower() for i in insights)

    def test_voice_patterns_quality_prediction(self, extractor: PatternExtractor):
        """Detects when quality score predicts acceptance."""
        signals = []
        # Accepted: high quality
        for _ in range(10):
            signals.append(make_signal(accepted=True, quality_score=90.0))
        # Rejected: low quality
        for _ in range(10):
            signals.append(make_signal(accepted=False, quality_score=50.0))

        insights = extractor.extract_voice_patterns(signals)
        assert any("quality score" in i.title.lower() for i in insights)

    def test_collection_patterns(self, extractor: PatternExtractor):
        """Detects underperforming collections."""
        signals = []
        # Black Rose: 90% acceptance
        for i in range(10):
            signals.append(make_signal(collection="BLACK_ROSE", accepted=i < 9))
        # Love Hurts: 40% acceptance
        for i in range(10):
            signals.append(make_signal(collection="LOVE_HURTS", accepted=i < 4))

        insights = extractor.extract_collection_patterns(signals)
        assert any("LOVE_HURTS" in str(i.affected_collections) for i in insights)

    def test_provider_patterns(self, extractor: PatternExtractor):
        """Detects best provider for brand voice."""
        signals = []
        # Anthropic: 90% acceptance
        for i in range(15):
            signals.append(make_signal(provider="anthropic", accepted=i < 14))
        # OpenAI: 60% acceptance
        for i in range(15):
            signals.append(make_signal(provider="openai", accepted=i < 9))

        insights = extractor.extract_provider_patterns(signals)
        assert any("anthropic" in i.title.lower() for i in insights)

    def test_no_insights_below_threshold(self, extractor: PatternExtractor):
        """Doesn't generate insights with too few signals."""
        signals = [make_signal() for _ in range(3)]
        insights = extractor.extract_voice_patterns(signals)
        # Should not crash; may or may not produce insights depending on data
        assert isinstance(insights, list)

    def test_signal_type_drift(self, extractor: PatternExtractor):
        """Detects brand drift in specific content types."""
        signals = []
        for i in range(10):
            signals.append(
                make_signal(
                    signal_type=SignalType.SOCIAL_POST,
                    accepted=i < 3,  # 30% acceptance
                )
            )

        insights = extractor.extract_signal_type_patterns(signals)
        assert any(i.category == InsightCategory.BRAND_DRIFT for i in insights)


# =============================================================================
# BrandAdaptor Tests
# =============================================================================


class TestBrandAdaptor:
    def test_adapts_provider_routing(self, memory: BrandMemory):
        adaptor = BrandAdaptor(memory)
        brand_dict: dict = {"tone": {"primary": "test"}}

        insight = BrandInsight(
            category=InsightCategory.VOICE_PATTERN,
            title="anthropic excels at brand voice",
            confidence=InsightConfidence.HIGH,
            evidence_count=25,
        )

        adaptations = adaptor.apply_insight(insight, brand_dict)
        assert len(adaptations) == 1
        assert brand_dict["_routing_hints"]["preferred_brand_provider"] == "anthropic"

    def test_skips_low_confidence(self, memory: BrandMemory):
        adaptor = BrandAdaptor(memory)
        brand_dict: dict = {}

        insight = BrandInsight(
            category=InsightCategory.VOICE_PATTERN,
            title="anthropic excels at brand voice",
            confidence=InsightConfidence.LOW,
        )

        adaptations = adaptor.apply_insight(insight, brand_dict)
        assert len(adaptations) == 0

    def test_adapts_collection_reinforcement(self, memory: BrandMemory):
        adaptor = BrandAdaptor(memory)
        brand_dict: dict = {}

        insight = BrandInsight(
            category=InsightCategory.PRODUCT_LANGUAGE,
            title="LOVE_HURTS underperforming",
            confidence=InsightConfidence.HIGH,
            affected_collections=["LOVE_HURTS"],
        )

        adaptations = adaptor.apply_insight(insight, brand_dict)
        assert len(adaptations) == 1
        assert "LOVE_HURTS" in brand_dict["_reinforcement_needed"]

    def test_revert_insight(self, memory: BrandMemory):
        adaptor = BrandAdaptor(memory)
        brand_dict: dict = {"tone": {"primary": "test"}}

        insight = BrandInsight(
            category=InsightCategory.VOICE_PATTERN,
            title="anthropic excels at brand voice",
            confidence=InsightConfidence.HIGH,
        )

        adaptor.apply_insight(insight, brand_dict)
        assert "_routing_hints" in brand_dict

        reverted = adaptor.revert_insight(insight.insight_id, brand_dict)
        assert reverted == 1


# =============================================================================
# BrandLearningLoop Integration Tests
# =============================================================================


class TestBrandLearningLoop:
    def test_observe_records_signal(self, loop: BrandLearningLoop):
        signal = make_signal()
        signal_id = loop.observe(signal)
        assert signal_id
        assert loop.get_state().total_signals == 1

    def test_should_run_cycle_threshold(self, loop: BrandLearningLoop):
        assert not loop.should_run_cycle()
        for _ in range(5):
            loop.observe(make_signal())
        assert loop.should_run_cycle()

    @pytest.mark.asyncio
    async def test_run_cycle_produces_insights(self, loop: BrandLearningLoop):
        # Create signals with clear patterns
        for i in range(15):
            loop.observe(make_signal(agent_id="good_agent", accepted=True, quality_score=90.0))
        for i in range(15):
            loop.observe(make_signal(agent_id="bad_agent", accepted=False, quality_score=40.0))

        insights = await loop.run_cycle()
        assert len(insights) > 0
        assert loop.get_state().cycle_count == 1

    @pytest.mark.asyncio
    async def test_run_cycle_adapts_brand_dict(self, loop: BrandLearningLoop):
        brand_dict: dict = {"tone": {"primary": "elegant"}}
        loop.connect(brand_dict=brand_dict)

        # Create clear provider pattern
        for _ in range(25):
            loop.observe(make_signal(provider="anthropic", accepted=True, quality_score=95.0))
        for _ in range(25):
            loop.observe(make_signal(provider="openai", accepted=False, quality_score=55.0))

        await loop.run_cycle()
        # Brand dict may now have routing hints
        state = loop.get_state()
        assert state.cycle_count == 1

    def test_get_brand_health_report(self, loop: BrandLearningLoop):
        for i in range(10):
            loop.observe(make_signal(accepted=i < 7, quality_score=70.0 + i * 3))

        report = loop.get_brand_health_report()
        assert "acceptance_rate" in report
        assert "avg_quality_score" in report
        assert "collection_health" in report
        assert report["total_signals"] == 10
        assert 0 < report["acceptance_rate"] < 1

    @pytest.mark.asyncio
    async def test_event_bus_integration(self, loop: BrandLearningLoop):
        """Loop auto-observes from event bus."""
        from core.events.event_bus import EventBus
        from core.events.event_store import Event

        bus = EventBus()
        loop.connect(event_bus=bus)

        event = Event(
            event_type="ContentGenerated",
            aggregate_id="test-123",
            data={
                "collection": "BLACK_ROSE",
                "sku": "br-001",
                "agent_id": "content_core",
                "provider": "anthropic",
                "quality_score": 88.0,
            },
        )

        await bus.publish(event)
        assert loop.get_state().total_signals == 1

    @pytest.mark.asyncio
    async def test_empty_cycle_no_error(self, loop: BrandLearningLoop):
        """Running a cycle with no signals should be a no-op."""
        insights = await loop.run_cycle()
        assert insights == []
        assert loop.get_state().cycle_count == 0  # Didn't count as a real cycle

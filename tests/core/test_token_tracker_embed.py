"""OBS-wire: TaskType.EMBED + record_embedding_usage() — model-free."""

from core.token_tracker import (
    TaskType,
    TokenUsage,
    get_token_tracker,
    record_embedding_usage,
)


def test_task_type_embed_exists():
    assert TaskType.EMBED.value == "embed"


def test_embedding_model_cost_is_zero_no_warning():
    # Embedding model ids are registered with 0 cost so EMBED rows don't log a
    # spurious unknown_model_cost warning on every encode.
    for model in ("openai/clip-vit-base-patch32", "facebook/dinov2-base"):
        u = TokenUsage(provider="embeddings", model=model, task_type=TaskType.EMBED)
        assert u.calculate_cost() == 0.0


def test_record_embedding_usage_records_one_row():
    tracker = get_token_tracker()
    tracker.clear()
    try:
        record_embedding_usage(
            model="facebook/dinov2-base",
            latency_ms=12.5,
            success=True,
            cache_hit=True,
            dim=768,
            count=1,
        )
        recs = tracker.records()
        assert len(recs) == 1
        r = recs[0]
        assert r.task_type == TaskType.EMBED
        assert r.provider == "embeddings"
        assert r.model == "facebook/dinov2-base"
        assert r.latency_ms == 12.5
        assert r.success is True
        assert r.metadata["cache_hit"] is True
        assert r.metadata["dim"] == 768
        assert r.calculate_cost() == 0.0  # token-free, registered at 0
    finally:
        tracker.clear()


def test_record_embedding_usage_never_raises_on_bad_input():
    # Telemetry must not break the encode path even if something is off.
    tracker = get_token_tracker()
    tracker.clear()
    try:
        record_embedding_usage(model="facebook/dinov2-base", success=False, error="boom")
        recs = tracker.records()
        assert len(recs) == 1 and recs[0].success is False
    finally:
        tracker.clear()

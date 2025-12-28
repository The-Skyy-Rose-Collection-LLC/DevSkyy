"""
Round Table API Endpoints
=========================

Real LLM Round Table competition endpoints.
All 6 LLM providers compete → Top 2 A/B test → Statistical winner.

Author: DevSkyy Platform Team
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from llm.round_table import LLMProvider, LLMRoundTable, create_round_table

logger = logging.getLogger(__name__)

round_table_router = APIRouter(tags=["Round Table"])

# Singleton round table instance
_round_table: LLMRoundTable | None = None


async def get_round_table() -> LLMRoundTable:
    """Get or create the round table instance."""
    global _round_table
    if _round_table is None:
        _round_table = await create_round_table()
    return _round_table


# =============================================================================
# Request/Response Models
# =============================================================================


class ProviderInfo(BaseModel):
    """LLM provider information."""

    name: str
    display_name: str
    enabled: bool = True
    avg_latency_ms: float = 0.0
    win_rate: float = 0.0
    total_competitions: int = 0


class CompetitionRequest(BaseModel):
    """Request to run a round table competition."""

    prompt: str = Field(..., min_length=1, max_length=10000)
    task_id: str | None = None
    providers: list[str] | None = Field(
        default=None,
        description="Specific providers to include. If None, all enabled providers compete.",
    )


class EntryScore(BaseModel):
    """Scores for a single entry."""

    relevance: float = 0.0
    quality: float = 0.0
    completeness: float = 0.0
    efficiency: float = 0.0
    brand_alignment: float = 0.0
    total: float = 0.0


class CompetitionEntry(BaseModel):
    """Single entry in the competition."""

    provider: str
    rank: int
    scores: EntryScore
    latency_ms: float
    cost_usd: float
    response_preview: str = ""


class CompetitionResponse(BaseModel):
    """Response from a round table competition."""

    id: str
    task_id: str
    prompt_preview: str
    status: str
    winner: CompetitionEntry | None
    entries: list[CompetitionEntry]
    ab_test_reasoning: str | None = None
    ab_test_confidence: float | None = None
    total_duration_ms: float
    total_cost_usd: float
    created_at: str


class HistoryEntry(BaseModel):
    """Historical competition entry for list view."""

    id: str
    prompt_preview: str
    winner_provider: str
    winner_score: float
    total_cost_usd: float
    created_at: str


class ProviderStats(BaseModel):
    """Statistics for a provider."""

    provider: str
    total_competitions: int
    wins: int
    win_rate: float
    avg_score: float
    avg_latency_ms: float
    total_cost_usd: float


# =============================================================================
# Endpoints
# =============================================================================


@round_table_router.get("/round-table/providers", response_model=list[ProviderInfo])
async def list_providers() -> list[ProviderInfo]:
    """List all available LLM providers."""
    rt = await get_round_table()
    providers = []

    for provider in LLMProvider:
        stats = await rt.get_provider_stats()
        provider_stats = stats.get(provider.value, {})

        providers.append(
            ProviderInfo(
                name=provider.value,
                display_name=provider.name.replace("_", " ").title(),
                enabled=provider in rt.registered_providers,
                avg_latency_ms=provider_stats.get("avg_latency_ms", 0.0),
                win_rate=provider_stats.get("win_rate", 0.0),
                total_competitions=provider_stats.get("total_competitions", 0),
            )
        )

    return providers


@round_table_router.get("/round-table", response_model=list[HistoryEntry])
async def list_competitions(limit: int = 20, offset: int = 0) -> list[HistoryEntry]:
    """List recent round table competitions."""
    rt = await get_round_table()

    # Get from in-memory history first, then database
    history = rt.get_history(limit=limit)

    # Try database history, gracefully handle if unavailable
    try:
        db_history = await rt.get_database_history(limit=limit, offset=offset)
    except Exception as e:
        logger.warning(f"Database history unavailable: {e}")
        db_history = []

    entries = []

    # Convert in-memory results
    for result in history:
        entries.append(
            HistoryEntry(
                id=result.id,
                prompt_preview=result.prompt[:100] + "..."
                if len(result.prompt) > 100
                else result.prompt,
                winner_provider=result.winner.provider.value,
                winner_score=result.winner.total_score,
                total_cost_usd=result.total_cost_usd,
                created_at=result.created_at.isoformat(),
            )
        )

    # Add database results if not already in memory
    memory_ids = {e.id for e in entries}
    for db_result in db_history:
        if db_result["id"] not in memory_ids:
            entries.append(
                HistoryEntry(
                    id=db_result["id"],
                    prompt_preview=db_result.get("prompt_preview", ""),
                    winner_provider=db_result.get("winner_provider", "unknown"),
                    winner_score=db_result.get("winner_score", 0.0),
                    total_cost_usd=db_result.get("total_cost_usd", 0.0),
                    created_at=db_result.get("created_at", ""),
                )
            )

    # Sort by created_at descending
    entries.sort(key=lambda e: e.created_at, reverse=True)
    return entries[:limit]


@round_table_router.get("/round-table/latest", response_model=CompetitionResponse | None)
async def get_latest_competition() -> CompetitionResponse | None:
    """Get the most recent competition result."""
    rt = await get_round_table()
    history = rt.get_history(limit=1)

    if not history:
        return None

    result = history[0]
    return _result_to_response(result)


@round_table_router.get("/round-table/{competition_id}", response_model=CompetitionResponse)
async def get_competition(competition_id: str) -> CompetitionResponse:
    """Get a specific competition result by ID."""
    rt = await get_round_table()

    # Check in-memory first
    for result in rt.get_history(limit=100):
        if result.id == competition_id:
            return _result_to_response(result)

    # Check database
    db_result = await rt._database.get_result(competition_id)
    if db_result:
        # Return simplified response from DB
        return CompetitionResponse(
            id=db_result["id"],
            task_id=db_result.get("task_id", ""),
            prompt_preview=db_result.get("prompt_preview", ""),
            status=db_result.get("status", "completed"),
            winner=CompetitionEntry(
                provider=db_result.get("winner_provider", "unknown"),
                rank=1,
                scores=EntryScore(total=db_result.get("winner_score", 0.0)),
                latency_ms=0.0,
                cost_usd=0.0,
            ),
            entries=[],  # Full entries not stored in DB summary
            ab_test_reasoning=db_result.get("ab_test_reasoning"),
            ab_test_confidence=db_result.get("ab_test_confidence"),
            total_duration_ms=db_result.get("total_duration_ms", 0.0),
            total_cost_usd=db_result.get("total_cost_usd", 0.0),
            created_at=db_result.get("created_at", ""),
        )

    raise HTTPException(status_code=404, detail=f"Competition {competition_id} not found")


@round_table_router.post("/round-table/compete", response_model=CompetitionResponse)
async def run_competition(request: CompetitionRequest) -> CompetitionResponse:
    """Run a new round table competition."""
    rt = await get_round_table()

    try:
        result = await rt.compete(
            prompt=request.prompt,
            task_id=request.task_id,
        )
        return _result_to_response(result)

    except Exception as e:
        logger.exception("Competition failed")
        raise HTTPException(status_code=500, detail=f"Competition failed: {e!s}")


@round_table_router.get("/round-table/stats", response_model=list[ProviderStats])
async def get_provider_stats() -> list[ProviderStats]:
    """Get aggregated statistics for all providers."""
    rt = await get_round_table()
    stats = await rt.get_provider_stats()

    return [
        ProviderStats(
            provider=provider,
            total_competitions=data.get("total_competitions", 0),
            wins=data.get("wins", 0),
            win_rate=data.get("win_rate", 0.0),
            avg_score=data.get("avg_score", 0.0),
            avg_latency_ms=data.get("avg_latency_ms", 0.0),
            total_cost_usd=data.get("total_cost_usd", 0.0),
        )
        for provider, data in stats.items()
    ]


# =============================================================================
# Helpers
# =============================================================================


def _result_to_response(result: Any) -> CompetitionResponse:
    """Convert RoundTableResult to API response."""
    entries = []
    for entry in result.entries:
        entries.append(
            CompetitionEntry(
                provider=entry.provider.value,
                rank=entry.rank,
                scores=EntryScore(
                    relevance=entry.scores.relevance,
                    quality=entry.scores.quality,
                    completeness=entry.scores.completeness,
                    efficiency=entry.scores.efficiency,
                    brand_alignment=entry.scores.brand_alignment,
                    total=entry.scores.total,
                ),
                latency_ms=entry.response.latency_ms,
                cost_usd=entry.response.cost_usd,
                response_preview=(
                    entry.response.content[:200] + "..."
                    if len(entry.response.content) > 200
                    else entry.response.content
                ),
            )
        )

    winner_entry = None
    if result.winner:
        winner_entry = CompetitionEntry(
            provider=result.winner.provider.value,
            rank=result.winner.rank,
            scores=EntryScore(
                relevance=result.winner.scores.relevance,
                quality=result.winner.scores.quality,
                completeness=result.winner.scores.completeness,
                efficiency=result.winner.scores.efficiency,
                brand_alignment=result.winner.scores.brand_alignment,
                total=result.winner.scores.total,
            ),
            latency_ms=result.winner.response.latency_ms,
            cost_usd=result.winner.response.cost_usd,
            response_preview=(
                result.winner.response.content[:200] + "..."
                if len(result.winner.response.content) > 200
                else result.winner.response.content
            ),
        )

    return CompetitionResponse(
        id=result.id,
        task_id=result.task_id,
        prompt_preview=result.prompt[:100] + "..." if len(result.prompt) > 100 else result.prompt,
        status=result.status.value,
        winner=winner_entry,
        entries=entries,
        ab_test_reasoning=result.ab_test.judge_reasoning if result.ab_test else None,
        ab_test_confidence=result.ab_test.confidence if result.ab_test else None,
        total_duration_ms=result.total_duration_ms,
        total_cost_usd=result.total_cost_usd,
        created_at=result.created_at.isoformat(),
    )

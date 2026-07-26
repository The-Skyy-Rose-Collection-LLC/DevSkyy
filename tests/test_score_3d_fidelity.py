"""Tests for the 3D fidelity scoring CLI (scripts/score_3d_fidelity.py).

Mirrors tests/api/test_qa_router.py's in-memory-sqlite db_manager reset, and
mocks the scorer functions / R2 download / confirmation gate so no real mesh
load, VLM call, or network happens in CI.
"""

from __future__ import annotations

import argparse
import asyncio
import uuid
from datetime import UTC, datetime

import pytest

import scripts.score_3d_fidelity as cli
from agents.models import Base as AgentsBase
from agents.models import Model3DGeneration, Model3DReview
from database.db import DatabaseConfig, DatabaseManager, db_manager
from imagery.model_review_scorer import AnalyticScoreResult, BrandingScoreResult

# =============================================================================
# Fixtures / helpers
# =============================================================================


async def _init_db() -> DatabaseManager:
    """Reset db_manager onto a fresh in-memory sqlite DB with the agents tables.

    Same seam as tests/api/test_qa_router.py: db_manager is a __new__ singleton,
    so this rebinds the module-global object the CLI's run() also uses.
    """
    if db_manager._engine:
        await db_manager.close()

    await db_manager.initialize(DatabaseConfig(url="sqlite+aiosqlite:///:memory:"))
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(
            AgentsBase.metadata.create_all,
            tables=[Model3DGeneration.__table__, Model3DReview.__table__],
        )
    return db_manager


@pytest.fixture
async def initialized_db():
    mgr = await _init_db()
    yield mgr
    await mgr.close()


async def _seed_generation(
    *,
    sku: str,
    model_path: str,
    source_image_path: str,
    rendered_preview_r2_key: str | None = "3d-models/preview.webp",
    created_at: datetime | None = None,
    with_review: bool = False,
    review_status: str = "pending",
    review_score: float | None = 50.0,
    review_breakdown: dict | None = None,
) -> tuple[uuid.UUID, uuid.UUID | None]:
    gen_id = uuid.uuid4()
    review_id: uuid.UUID | None = None
    ts = created_at or datetime(2026, 1, 1, tzinfo=UTC)

    async with db_manager.session() as session:
        session.add(
            Model3DGeneration(
                id=gen_id,
                sku=sku,
                task_id="tripo-task",
                provider="tripo3d",
                format="glb",
                model_path=model_path,
                source_image_path=source_image_path,
                rendered_preview_r2_key=rendered_preview_r2_key,
                created_at=ts,
            )
        )
        if with_review:
            review_id = uuid.uuid4()
            session.add(
                Model3DReview(
                    id=review_id,
                    generation_id=gen_id,
                    fidelity_score=review_score,
                    fidelity_breakdown=review_breakdown,
                    status=review_status,
                    created_at=ts,
                    updated_at=ts,
                )
            )
        await session.commit()

    return gen_id, review_id


def _fake_analytic() -> AnalyticScoreResult:
    # _partial_score = mean(90,80,95,85,70) = 84.0
    return AnalyticScoreResult(
        geometry=90.0,
        materials=80.0,
        colors=95.0,
        proportions=85.0,
        texture_detail_floor=70.0,
        overall_partial=87.5,
    )


def _fake_branding() -> BrandingScoreResult:
    return BrandingScoreResult(
        branding=96.0, visual_analysis="graphic matches", judge_cost_usd=0.05
    )


@pytest.fixture
def local_files(tmp_path):
    """Real on-disk GLB + reference packshot so _require_local() passes."""
    model = tmp_path / "model.glb"
    model.write_bytes(b"glb-bytes")
    reference = tmp_path / "ref.jpg"
    reference.write_bytes(b"jpg-bytes")
    return model, reference


@pytest.fixture
def patch_scorers(monkeypatch):
    """Replace the real scorer functions with deterministic fakes."""
    monkeypatch.setattr(cli, "score_analytic", lambda *a, **k: _fake_analytic())
    monkeypatch.setattr(cli, "score_branding_vlm", lambda *a, **k: _fake_branding())
    monkeypatch.setattr(cli, "_download_preview", lambda *a, **k: None)


async def _get_review_for_sku(sku: str) -> Model3DReview | None:
    from sqlalchemy import select

    async with db_manager.session() as session:
        stmt = (
            select(Model3DReview)
            .join(Model3DGeneration, Model3DReview.generation_id == Model3DGeneration.id)
            .where(Model3DGeneration.sku == sku)
        )
        return (await session.execute(stmt)).scalars().first()


# =============================================================================
# Pure helpers (no DB)
# =============================================================================


class TestScoreAssembly:
    def test_partial_score_is_mean_of_five_free_dims(self):
        assert cli._partial_score(_fake_analytic()) == pytest.approx(84.0)

    def test_full_breakdown_has_six_keys(self):
        breakdown = cli._full_breakdown(_fake_analytic(), _fake_branding())
        assert set(breakdown) == {
            "geometry",
            "materials",
            "colors",
            "proportions",
            "branding",
            "texture_detail",
        }
        assert breakdown["branding"] == 96.0
        assert breakdown["texture_detail"] == 70.0  # analytic floor, not a VLM refinement

    def test_full_score_is_mean_of_six(self):
        breakdown = cli._full_breakdown(_fake_analytic(), _fake_branding())
        assert cli._full_score(breakdown) == pytest.approx((90 + 80 + 95 + 85 + 96 + 70) / 6)

    def test_mean_empty_is_zero(self):
        assert cli._mean([]) == 0.0


class TestValidateArgs:
    def _ns(self, **kw) -> argparse.Namespace:
        base = {"sku": None, "all_pending": False, "with_branding": False}
        base.update(kw)
        return argparse.Namespace(**base)

    def test_branding_with_all_pending_rejected(self):
        assert cli._validate_args(self._ns(all_pending=True, with_branding=True)) is not None

    def test_branding_without_sku_rejected(self):
        assert cli._validate_args(self._ns(with_branding=True)) is not None

    def test_no_target_rejected(self):
        assert cli._validate_args(self._ns()) is not None

    def test_sku_ok(self):
        assert cli._validate_args(self._ns(sku="br-001")) is None

    def test_all_pending_ok(self):
        assert cli._validate_args(self._ns(all_pending=True)) is None


class TestRequireLocal:
    def test_missing_path_raises_skip(self):
        with pytest.raises(cli.ScoringSkip):
            cli._require_local(None, "br-001", "GLB")

    def test_missing_file_raises_skip(self, tmp_path):
        with pytest.raises(cli.ScoringSkip):
            cli._require_local(str(tmp_path / "nope.glb"), "br-001", "GLB")

    def test_existing_file_ok(self, tmp_path):
        f = tmp_path / "x.glb"
        f.write_bytes(b"x")
        assert cli._require_local(str(f), "br-001", "GLB") == f


# =============================================================================
# Analytic pass
# =============================================================================


class TestAnalyticPass:
    async def test_creates_review_with_null_breakdown(
        self, initialized_db, patch_scorers, local_files
    ):
        model, reference = local_files
        await _seed_generation(
            sku="br-001", model_path=str(model), source_image_path=str(reference)
        )

        rc = await cli.run(["--sku", "br-001"])
        assert rc == 0

        review = await _get_review_for_sku("br-001")
        assert review is not None
        assert review.fidelity_score == pytest.approx(84.0)
        assert review.fidelity_breakdown is None  # stays NULL until branding (D4)
        assert review.status == "pending"

    async def test_skips_when_review_already_exists(
        self, initialized_db, patch_scorers, local_files
    ):
        model, reference = local_files
        await _seed_generation(
            sku="br-001",
            model_path=str(model),
            source_image_path=str(reference),
            with_review=True,
            review_score=42.0,
        )

        rc = await cli.run(["--sku", "br-001"])
        assert rc == 1  # nothing scored

        review = await _get_review_for_sku("br-001")
        assert review.fidelity_score == 42.0  # untouched

    async def test_async_bridge_survives_scorer_that_calls_asyncio_run(
        self, initialized_db, local_files, monkeypatch
    ):
        """Regression guard for the async bridge — the crux of the CLI design.

        The real ``score_analytic`` calls ``asyncio.run()`` internally, and
        ``run()`` invokes it via ``asyncio.to_thread`` precisely so that inner
        ``asyncio.run()`` sees no running loop. A future refactor that calls
        ``score_analytic`` directly (dropping ``to_thread``) would make that
        inner ``asyncio.run()`` raise "cannot be called from a running event
        loop". This fake reproduces that exact structure so the seam stays
        locked — the scorer's own numeric logic is covered separately by
        tests/test_model_review_scorer.py.
        """

        async def _inner_async_work() -> None:
            return None

        def scorer_that_calls_asyncio_run(model_path, sku, reference):
            asyncio.run(_inner_async_work())  # only safe with no running loop
            return _fake_analytic()

        monkeypatch.setattr(cli, "score_analytic", scorer_that_calls_asyncio_run)
        model, reference = local_files
        await _seed_generation(
            sku="br-001", model_path=str(model), source_image_path=str(reference)
        )

        rc = await cli.run(["--sku", "br-001"])
        assert rc == 0

        review = await _get_review_for_sku("br-001")
        assert review is not None
        assert review.fidelity_score == pytest.approx(84.0)

    async def test_missing_local_glb_skips(self, initialized_db, patch_scorers, tmp_path):
        reference = tmp_path / "ref.jpg"
        reference.write_bytes(b"jpg")
        await _seed_generation(
            sku="br-001",
            model_path=str(tmp_path / "gone.glb"),  # never created
            source_image_path=str(reference),
        )

        rc = await cli.run(["--sku", "br-001"])
        assert rc == 1
        assert await _get_review_for_sku("br-001") is None


# =============================================================================
# --all-pending
# =============================================================================


class TestAllPending:
    async def test_scores_only_reviewless_generations(
        self, initialized_db, patch_scorers, local_files
    ):
        model, reference = local_files
        await _seed_generation(
            sku="br-001", model_path=str(model), source_image_path=str(reference)
        )
        await _seed_generation(
            sku="br-002",
            model_path=str(model),
            source_image_path=str(reference),
            with_review=True,
            review_score=99.0,
        )

        rc = await cli.run(["--all-pending"])
        assert rc == 0

        br001 = await _get_review_for_sku("br-001")
        assert br001 is not None and br001.fidelity_score == pytest.approx(84.0)

        br002 = await _get_review_for_sku("br-002")
        assert br002.fidelity_score == 99.0  # pre-existing review untouched

    async def test_empty_returns_zero(self, initialized_db, patch_scorers):
        rc = await cli.run(["--all-pending"])
        assert rc == 0


# =============================================================================
# --with-branding (paid pass)
# =============================================================================


class TestBrandingPass:
    async def test_writes_full_breakdown_and_updates_existing_review(
        self, initialized_db, patch_scorers, local_files, monkeypatch
    ):
        monkeypatch.setattr(cli, "_confirm", lambda: True)
        model, reference = local_files
        # Simulate phase-1 already ran: a pending review with NULL breakdown.
        await _seed_generation(
            sku="br-001",
            model_path=str(model),
            source_image_path=str(reference),
            with_review=True,
            review_score=84.0,
            review_breakdown=None,
        )

        rc = await cli.run(["--sku", "br-001", "--with-branding"])
        assert rc == 0

        review = await _get_review_for_sku("br-001")
        assert review.fidelity_breakdown is not None
        assert set(review.fidelity_breakdown) == {
            "geometry",
            "materials",
            "colors",
            "proportions",
            "branding",
            "texture_detail",
        }
        assert review.fidelity_score == pytest.approx((90 + 80 + 95 + 85 + 96 + 70) / 6)

    async def test_aborted_at_gate_writes_nothing(
        self, initialized_db, patch_scorers, local_files, monkeypatch
    ):
        monkeypatch.setattr(cli, "_confirm", lambda: False)
        model, reference = local_files
        await _seed_generation(
            sku="br-001",
            model_path=str(model),
            source_image_path=str(reference),
            with_review=True,
            review_score=84.0,
            review_breakdown=None,
        )

        rc = await cli.run(["--sku", "br-001", "--with-branding"])
        assert rc == 1

        review = await _get_review_for_sku("br-001")
        assert review.fidelity_breakdown is None  # untouched by an aborted paid pass

    async def test_requires_rendered_preview_key(
        self, initialized_db, patch_scorers, local_files, monkeypatch
    ):
        monkeypatch.setattr(cli, "_confirm", lambda: True)
        model, reference = local_files
        await _seed_generation(
            sku="br-001",
            model_path=str(model),
            source_image_path=str(reference),
            rendered_preview_r2_key=None,  # no preview to score branding against
        )

        rc = await cli.run(["--sku", "br-001", "--with-branding"])
        assert rc == 1
        assert await _get_review_for_sku("br-001") is None


# =============================================================================
# Arg-combo / not-found exit codes
# =============================================================================


class TestExitCodes:
    async def test_branding_with_all_pending_is_error(self, initialized_db):
        assert await cli.run(["--all-pending", "--with-branding"]) == 2

    async def test_no_args_is_error(self, initialized_db):
        assert await cli.run([]) == 2

    async def test_sku_not_found_is_one(self, initialized_db, patch_scorers):
        assert await cli.run(["--sku", "zz-999"]) == 1


# =============================================================================
# The REAL _confirm() paid gate (orchestration tests monkeypatch it away)
# =============================================================================


class _FakeStdin:
    """Test seam for _confirm() — avoids mutating pytest's captured stdin."""

    def __init__(self, is_tty: bool) -> None:
        self._is_tty = is_tty

    def isatty(self) -> bool:
        return self._is_tty


class TestConfirmGate:
    """Exercises the ACTUAL cli._confirm() STOP-AND-SHOW gate — not the
    monkeypatched-True/False the TestBrandingPass orchestration tests use. This
    is the layer that must fail closed so a paid VLM call never fires unattended
    (mirrors tests/test_generate_3d_from_catalog.py::TestConfirmGate)."""

    def test_non_interactive_no_auto_confirm_aborts(self, monkeypatch):
        monkeypatch.delenv("SKYYROSE_AUTO_CONFIRM", raising=False)
        monkeypatch.setattr(cli.sys, "stdin", _FakeStdin(False))
        assert cli._confirm() is False

    def test_auto_confirm_env_proceeds_even_without_tty(self, monkeypatch):
        monkeypatch.setenv("SKYYROSE_AUTO_CONFIRM", "1")
        monkeypatch.setattr(cli.sys, "stdin", _FakeStdin(False))
        assert cli._confirm() is True

    def test_interactive_y_proceeds(self, monkeypatch):
        monkeypatch.delenv("SKYYROSE_AUTO_CONFIRM", raising=False)
        monkeypatch.setattr(cli.sys, "stdin", _FakeStdin(True))
        monkeypatch.setattr("builtins.input", lambda: "y")
        assert cli._confirm() is True

    def test_interactive_yes_proceeds(self, monkeypatch):
        monkeypatch.delenv("SKYYROSE_AUTO_CONFIRM", raising=False)
        monkeypatch.setattr(cli.sys, "stdin", _FakeStdin(True))
        monkeypatch.setattr("builtins.input", lambda: "yes")
        assert cli._confirm() is True

    def test_interactive_anything_else_aborts(self, monkeypatch):
        monkeypatch.delenv("SKYYROSE_AUTO_CONFIRM", raising=False)
        monkeypatch.setattr(cli.sys, "stdin", _FakeStdin(True))
        monkeypatch.setattr("builtins.input", lambda: "n")
        assert cli._confirm() is False

    def test_interactive_eof_aborts(self, monkeypatch):
        monkeypatch.delenv("SKYYROSE_AUTO_CONFIRM", raising=False)
        monkeypatch.setattr(cli.sys, "stdin", _FakeStdin(True))

        def _raise_eof() -> str:
            raise EOFError

        monkeypatch.setattr("builtins.input", _raise_eof)
        assert cli._confirm() is False

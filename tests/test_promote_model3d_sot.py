"""Tests for scripts/promote_model3d_sot.py -- the 'promote to SOT' step for 3D models.

Covers: the pure sot.json-mutation logic (promote_model3d, _sku_index,
_to_repo_relative_path), the DB-query function against a fake in-memory SQLite
session (mirrors tests/test_model3d_registry.py's fixture -- no real Postgres,
no real Tripo call), and the write-then-read round-trip against
skyyrose.core.sot_images.resolve_model_3d that proves the two modules agree on
the 'model_3d' key name and dict shape.

No Model3DReview row is APPROVED yet in real data (nothing has been generated),
so the DB-backed tests exercise a self-contained fake session, never the
committed sot.json or a real database.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from agents.models import Base, Model3DGeneration, Model3DReview
from scripts import promote_model3d_sot as promoter
from skyyrose.core import sot_images
from skyyrose.core.paths import REPO_ROOT


@pytest.fixture(autouse=True)
def _clear_sot_cache():
    """Mirror tests/test_sot_images.py's fixture -- drop the lru_cached index
    around every test so a monkeypatched index never leaks across tests."""
    sot_images.refresh()
    yield
    sot_images.refresh()


# =============================================================================
# _to_repo_relative_path
# =============================================================================


def test_to_repo_relative_path_strips_repo_root_prefix():
    absolute = str(REPO_ROOT / "assets" / "3d-models-generated" / "br-011" / "br-011.glb")
    assert (
        promoter._to_repo_relative_path(absolute) == "assets/3d-models-generated/br-011/br-011.glb"
    )


def test_to_repo_relative_path_leaves_relative_path_unchanged():
    rel = "assets/3d-models-generated/br-011/br-011.glb"
    assert promoter._to_repo_relative_path(rel) == rel


def test_to_repo_relative_path_raises_for_path_outside_repo_root():
    with pytest.raises(ValueError, match="not under REPO_ROOT"):
        promoter._to_repo_relative_path("/etc/passwd")


# =============================================================================
# _sku_index
# =============================================================================


def test_sku_index_builds_across_slugs():
    sot_by_slug = {
        "black-rose": {"products": [{"sku": "br-011"}, {"sku": "br-012"}]},
        "love-hurts": {"products": [{"sku": "lh-005"}]},
    }
    index = promoter._sku_index(sot_by_slug)
    assert index == {
        "br-011": ("black-rose", 0),
        "br-012": ("black-rose", 1),
        "lh-005": ("love-hurts", 0),
    }


def test_sku_index_skips_products_with_no_sku():
    sot_by_slug = {"black-rose": {"products": [{"name": "no sku here"}, {"sku": "br-011"}]}}
    assert promoter._sku_index(sot_by_slug) == {"br-011": ("black-rose", 1)}


# =============================================================================
# promote_model3d (pure logic)
# =============================================================================


def _row(sku: str, task_id: str = "task-1", approved_at: str = "2026-07-22T00:00:00+00:00"):
    return promoter.ApprovedModel3D(
        sku=sku,
        model_path=f"assets/3d-models-generated/{sku}/{sku}.glb",
        format="glb",
        task_id=task_id,
        approved_at=approved_at,
    )


def test_promote_model3d_adds_key_to_matched_sku():
    sot_by_slug = {"black-rose": {"products": [{"sku": "br-011", "name": "Thorn Bomber"}]}}
    updated = promoter.promote_model3d(sot_by_slug, [_row("br-011")])
    product = updated["black-rose"]["products"][0]
    assert product["model_3d"] == {
        "path": "assets/3d-models-generated/br-011/br-011.glb",
        "format": "glb",
        "task_id": "task-1",
        "approved_at": "2026-07-22T00:00:00+00:00",
    }
    # Every other field on the product is preserved untouched.
    assert product["name"] == "Thorn Bomber"


def test_promote_model3d_skips_sku_matching_no_collection():
    sot_by_slug = {"black-rose": {"products": [{"sku": "br-011"}]}}
    updated = promoter.promote_model3d(sot_by_slug, [_row("zz-999")])
    assert "model_3d" not in updated["black-rose"]["products"][0]


def test_promote_model3d_last_write_wins_for_duplicate_sku():
    sot_by_slug = {"black-rose": {"products": [{"sku": "br-011"}]}}
    rows = [_row("br-011", task_id="old-task"), _row("br-011", task_id="new-task")]
    updated = promoter.promote_model3d(sot_by_slug, rows)
    assert updated["black-rose"]["products"][0]["model_3d"]["task_id"] == "new-task"


def test_promote_model3d_does_not_mutate_input():
    sot_by_slug = {"black-rose": {"products": [{"sku": "br-011"}]}}
    original_products = sot_by_slug["black-rose"]["products"]
    promoter.promote_model3d(sot_by_slug, [_row("br-011")])
    assert "model_3d" not in sot_by_slug["black-rose"]["products"][0]
    assert sot_by_slug["black-rose"]["products"] is original_products


def test_promote_model3d_leaves_untouched_skus_alone():
    sot_by_slug = {
        "black-rose": {"products": [{"sku": "br-011"}, {"sku": "br-012"}]},
    }
    updated = promoter.promote_model3d(sot_by_slug, [_row("br-011")])
    assert "model_3d" in updated["black-rose"]["products"][0]
    assert "model_3d" not in updated["black-rose"]["products"][1]


def test_promote_model3d_empty_approved_list_is_a_noop():
    sot_by_slug = {"black-rose": {"products": [{"sku": "br-011"}]}}
    updated = promoter.promote_model3d(sot_by_slug, [])
    assert updated == sot_by_slug
    assert updated is not sot_by_slug


# =============================================================================
# _serialize / _load_sot_documents
# =============================================================================


def test_serialize_matches_build_collection_sot_format():
    # Same byte-format contract as build-collection-sot.py's serialize(): 2-space
    # indent, ASCII-escaped em-dash, trailing newline.
    doc = {"note": "em—dash"}
    out = promoter._serialize(doc)
    assert out == '{\n  "note": "em\\u2014dash"\n}\n'


def test_load_sot_documents_reads_every_slug(tmp_path):
    (tmp_path / "black-rose").mkdir()
    (tmp_path / "black-rose" / "sot.json").write_text(json.dumps({"collection": "black-rose"}))
    (tmp_path / "love-hurts").mkdir()
    (tmp_path / "love-hurts" / "sot.json").write_text(json.dumps({"collection": "love-hurts"}))
    docs = promoter._load_sot_documents(tmp_path)
    assert set(docs) == {"black-rose", "love-hurts"}
    assert docs["black-rose"]["collection"] == "black-rose"


# =============================================================================
# fetch_approved_model3d -- fake in-memory SQLite session (mirrors
# tests/test_model3d_registry.py's db_factory fixture; zero real DB/network).
# =============================================================================


@pytest.fixture
async def db_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[Model3DGeneration.__table__, Model3DReview.__table__],
        )

    yield factory

    await engine.dispose()


@pytest.fixture
async def db(db_factory):
    async with db_factory() as session:
        yield session


@pytest.mark.asyncio
async def test_fetch_approved_model3d_returns_only_approved_rows(db):
    approved_gen_id = uuid.uuid4()
    pending_gen_id = uuid.uuid4()
    absolute_model_path = str(
        REPO_ROOT / "assets" / "3d-models-generated" / "br-011" / "br-011.glb"
    )

    db.add_all(
        [
            Model3DGeneration(
                id=approved_gen_id,
                sku="br-011",
                task_id="task-approved",
                provider="tripo3d",
                format="glb",
                model_path=absolute_model_path,
            ),
            Model3DGeneration(
                id=pending_gen_id,
                sku="br-012",
                task_id="task-pending",
                provider="tripo3d",
                format="glb",
                model_path="assets/3d-models-generated/br-012/br-012.glb",
            ),
        ]
    )
    await db.flush()
    db.add_all(
        [
            Model3DReview(id=uuid.uuid4(), generation_id=approved_gen_id, status="approved"),
            Model3DReview(id=uuid.uuid4(), generation_id=pending_gen_id, status="pending"),
        ]
    )
    await db.commit()

    approved = await promoter.fetch_approved_model3d(db)

    assert len(approved) == 1
    assert approved[0].sku == "br-011"
    assert approved[0].task_id == "task-approved"
    # DB stores an absolute path (matches dispatch_sku's real write shape) --
    # fetch_approved_model3d must normalize it before it ever reaches sot.json.
    assert approved[0].model_path == "assets/3d-models-generated/br-011/br-011.glb"


@pytest.mark.asyncio
async def test_fetch_approved_model3d_orders_oldest_approved_first(db):
    gen_a = uuid.uuid4()
    gen_b = uuid.uuid4()
    db.add_all(
        [
            Model3DGeneration(
                id=gen_a, sku="br-011", model_path="assets/3d-models-generated/br-011/br-011.glb"
            ),
            Model3DGeneration(
                id=gen_b, sku="br-012", model_path="assets/3d-models-generated/br-012/br-012.glb"
            ),
        ]
    )
    await db.flush()
    older = datetime(2026, 1, 1, tzinfo=UTC)
    newer = datetime(2026, 7, 1, tzinfo=UTC)
    db.add_all(
        [
            Model3DReview(
                id=uuid.uuid4(), generation_id=gen_b, status="approved", updated_at=newer
            ),
            Model3DReview(
                id=uuid.uuid4(), generation_id=gen_a, status="approved", updated_at=older
            ),
        ]
    )
    await db.commit()

    approved = await promoter.fetch_approved_model3d(db)

    assert [row.sku for row in approved] == ["br-011", "br-012"]


@pytest.mark.asyncio
async def test_fetch_approved_model3d_empty_when_nothing_approved(db):
    gen_id = uuid.uuid4()
    db.add(
        Model3DGeneration(
            id=gen_id, sku="br-011", model_path="assets/3d-models-generated/br-011/br-011.glb"
        )
    )
    await db.flush()
    db.add(Model3DReview(id=uuid.uuid4(), generation_id=gen_id, status="rejected"))
    await db.commit()

    assert await promoter.fetch_approved_model3d(db) == []


# =============================================================================
# Round-trip: promote_model3d() write -> sot_images.resolve_model_3d() read.
#
# The single test that actually proves the writer and reader agree on the
# 'model_3d' key name and dict shape -- two isolated tests could each pass
# while that contract silently drifts (e.g. writer emits 'model_3d', reader
# looks for 'model3d').
# =============================================================================


def test_round_trip_promote_then_resolve(monkeypatch):
    sot_by_slug = {"black-rose": {"products": [{"sku": "br-011", "images": {}}]}}
    updated = promoter.promote_model3d(sot_by_slug, [_row("br-011")])

    synthetic_index = {
        sku: {**prod, "collection": slug}
        for slug, sot in updated.items()
        for sku, prod in ((p["sku"], p) for p in sot["products"])
    }
    monkeypatch.setattr(sot_images, "_index", lambda: synthetic_index)

    resolved = sot_images.resolve_model_3d("br-011")
    assert resolved == {
        "path": "assets/3d-models-generated/br-011/br-011.glb",
        "format": "glb",
        "task_id": "task-1",
        "approved_at": "2026-07-22T00:00:00+00:00",
    }


def test_round_trip_unmatched_sku_resolves_to_none(monkeypatch):
    sot_by_slug = {"black-rose": {"products": [{"sku": "br-011", "images": {}}]}}
    updated = promoter.promote_model3d(sot_by_slug, [])  # nothing approved

    synthetic_index = {
        sku: {**prod, "collection": slug}
        for slug, sot in updated.items()
        for sku, prod in ((p["sku"], p) for p in sot["products"])
    }
    monkeypatch.setattr(sot_images, "_index", lambda: synthetic_index)

    assert sot_images.resolve_model_3d("br-011") is None

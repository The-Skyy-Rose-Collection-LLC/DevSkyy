"""Tests for the Model3DGeneration / Model3DReview ORM registry.

Covers: model instantiation, required-field constraints, JSONB round-trip
for fidelity_breakdown, and the FK relationship between the two tables.

Mirrors the fixture pattern used by tests/test_database_models.py, scoped
to only the two new tables (agents.models.Base carries other tables with
raw postgresql.JSONB columns that don't compile on sqlite).
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from agents.models import Base, Model3DGeneration, Model3DReview

FIDELITY_BREAKDOWN = {
    "geometry": 92.5,
    "materials": 88.0,
    "colors": 95.0,
    "proportions": 90.0,
    "branding": 97.0,
    "texture_detail": 85.5,
}


@pytest.fixture
async def db_factory():
    """In-memory SQLite engine scoped to only the model3d_* tables."""
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


class TestModel3DGeneration:
    """Tests for the Model3DGeneration ORM model."""

    @pytest.mark.asyncio
    async def test_create_generation(self, db):
        generation = Model3DGeneration(
            id=uuid.uuid4(),
            sku="br-011",
            task_id="tripo-task-123",
            provider="tripo3d",
            format="glb",
            model_path="/assets/products/models/br-011.glb",
            source_image_path="/assets/products/references/br-011-front.jpg",
            validation_status="valid",
        )
        db.add(generation)
        await db.flush()

        assert generation.id is not None
        assert generation.sku == "br-011"
        assert generation.task_id == "tripo-task-123"
        assert generation.validation_status == "valid"
        assert generation.generation_cost_credits is None

    @pytest.mark.asyncio
    async def test_sku_is_required(self, db):
        generation = Model3DGeneration(
            id=uuid.uuid4(),
            task_id="tripo-task-missing-sku",
            provider="tripo3d",
        )
        db.add(generation)
        with pytest.raises(IntegrityError):
            await db.flush()

    @pytest.mark.asyncio
    async def test_validation_details_jsonb_roundtrip(self, db_factory):
        gen_id = uuid.uuid4()
        validation_details = {
            "is_valid": True,
            "polycount": 48213,
            "texture_size": "2048x2048",
            "warnings": ["low-poly count on sleeve seam"],
            "errors": [],
        }

        async with db_factory() as write_session:
            generation = Model3DGeneration(
                id=gen_id,
                sku="br-011",
                task_id="tripo-task-456",
                validation_status="warnings",
                validation_details=validation_details,
            )
            write_session.add(generation)
            await write_session.commit()

        async with db_factory() as read_session:
            fetched = await read_session.get(Model3DGeneration, gen_id)

        assert fetched is not None
        assert fetched.validation_details == validation_details
        assert fetched.validation_details["warnings"] == ["low-poly count on sleeve seam"]


class TestModel3DReview:
    """Tests for the Model3DReview ORM model."""

    @pytest.mark.asyncio
    async def test_create_review(self, db):
        generation = Model3DGeneration(id=uuid.uuid4(), sku="br-011")
        db.add(generation)
        await db.flush()

        review = Model3DReview(
            id=uuid.uuid4(),
            generation_id=generation.id,
            fidelity_score=91.2,
            status="approved",
            notes="Matches canonical reference on all six dimensions.",
        )
        db.add(review)
        await db.flush()

        assert review.id is not None
        assert review.status == "approved"
        assert review.fidelity_score == 91.2

    @pytest.mark.asyncio
    async def test_status_defaults_to_pending(self, db):
        generation = Model3DGeneration(id=uuid.uuid4(), sku="br-011")
        db.add(generation)
        await db.flush()

        review = Model3DReview(id=uuid.uuid4(), generation_id=generation.id)
        db.add(review)
        await db.commit()
        await db.refresh(review)

        assert review.status == "pending"

    @pytest.mark.asyncio
    async def test_generation_id_is_required(self, db):
        review = Model3DReview(id=uuid.uuid4(), status="pending")
        db.add(review)
        with pytest.raises(IntegrityError):
            await db.flush()

    @pytest.mark.asyncio
    async def test_fidelity_breakdown_jsonb_roundtrip(self, db_factory):
        gen_id = uuid.uuid4()
        review_id = uuid.uuid4()

        async with db_factory() as write_session:
            generation = Model3DGeneration(id=gen_id, sku="br-011")
            write_session.add(generation)
            await write_session.flush()

            review = Model3DReview(
                id=review_id,
                generation_id=gen_id,
                fidelity_score=91.2,
                fidelity_breakdown=FIDELITY_BREAKDOWN,
                status="approved",
            )
            write_session.add(review)
            await write_session.commit()

        async with db_factory() as read_session:
            fetched = await read_session.get(Model3DReview, review_id)

        assert fetched is not None
        assert fetched.fidelity_breakdown == FIDELITY_BREAKDOWN
        assert set(fetched.fidelity_breakdown.keys()) == {
            "geometry",
            "materials",
            "colors",
            "proportions",
            "branding",
            "texture_detail",
        }


class TestModel3DGenerationReviewRelationship:
    """Tests for the FK relationship between the two tables."""

    @pytest.mark.asyncio
    async def test_generation_reviews_relationship(self, db):
        generation = Model3DGeneration(id=uuid.uuid4(), sku="br-011")
        db.add(generation)
        await db.flush()

        review_one = Model3DReview(id=uuid.uuid4(), generation_id=generation.id, status="rejected")
        review_two = Model3DReview(id=uuid.uuid4(), generation_id=generation.id, status="pending")
        db.add_all([review_one, review_two])
        await db.commit()
        await db.refresh(generation, attribute_names=["reviews"])

        assert len(generation.reviews) == 2
        assert {r.status for r in generation.reviews} == {"rejected", "pending"}

    @pytest.mark.asyncio
    async def test_review_generation_back_populates(self, db):
        generation = Model3DGeneration(id=uuid.uuid4(), sku="br-011")
        db.add(generation)
        await db.flush()

        review = Model3DReview(id=uuid.uuid4(), generation_id=generation.id)
        db.add(review)
        await db.commit()
        await db.refresh(review, attribute_names=["generation"])

        assert review.generation is not None
        assert review.generation.id == generation.id
        assert review.generation.sku == "br-011"

    @pytest.mark.asyncio
    async def test_deleting_generation_cascades_to_reviews(self, db):
        generation = Model3DGeneration(id=uuid.uuid4(), sku="br-011")
        db.add(generation)
        await db.flush()

        review = Model3DReview(id=uuid.uuid4(), generation_id=generation.id)
        db.add(review)
        await db.commit()
        review_id = review.id

        await db.delete(generation)
        await db.commit()

        remaining = await db.get(Model3DReview, review_id)
        assert remaining is None

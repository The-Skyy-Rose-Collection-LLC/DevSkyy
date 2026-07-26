"""Tests for the 3D QA Review API (api/v1/qa.py).

Mirrors tests/api/test_brand_assets.py's isolated-app + sqlite db_manager
pattern, and tests/test_model3d_registry.py's Model3DGeneration/Model3DReview
fixture shapes.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

import api.v1.qa as qa_module
from agents.models import Base as AgentsBase
from agents.models import Model3DGeneration, Model3DReview
from api.v1.qa import require_developer, router
from database.db import DatabaseConfig, DatabaseManager, db_manager

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def _wp_site_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every route resolving reference_image_url needs WP_SITE_URL set."""
    monkeypatch.setenv("WP_SITE_URL", "https://skyyrose.test")


@pytest.fixture
def mock_user() -> MagicMock:
    """Authenticated user for both get_current_user and require_developer overrides."""
    from security.jwt_oauth2_auth import TokenPayload, TokenType

    return TokenPayload(
        sub=str(uuid.uuid4()),
        jti="test_jti_qa",
        type=TokenType.ACCESS,
        roles=["developer", "admin"],
        exp=datetime.now(UTC),
        iat=datetime.now(UTC),
    )


async def _init_db() -> DatabaseManager:
    """Reset the db_manager singleton onto a fresh in-memory sqlite DB.

    database.db.Base and agents.models.Base are separate SQLAlchemy
    declarative bases sharing the same engine — db_manager.initialize() only
    creates database.db's tables, so model3d_generations/model3d_reviews must
    be created explicitly on the same engine (mirrors
    tests/test_model3d_registry.py's tables= scoping).
    """
    if db_manager._engine:
        await db_manager.close()
        db_manager._instance = None

    mgr = DatabaseManager()
    await mgr.initialize(DatabaseConfig(url="sqlite+aiosqlite:///:memory:"))

    async with mgr.engine.begin() as conn:
        await conn.run_sync(
            AgentsBase.metadata.create_all,
            tables=[Model3DGeneration.__table__, Model3DReview.__table__],
        )
    return mgr


@pytest.fixture
async def client(mock_user: MagicMock):
    """ASGI test client backed by a fresh in-memory DB, isolated per test.

    Auth dependencies are overridden with an authenticated developer/admin
    user — see unauth_client for the real-dependency 401 paths.
    """
    from security.jwt_oauth2_auth import get_current_user

    mgr = await _init_db()

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[require_developer] = lambda: mock_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    await mgr.close()
    mgr._instance = None


@pytest.fixture
async def unauth_client():
    """Same app/DB, but with NO auth overrides — exercises the real
    get_current_user / require_developer 401 paths (no Authorization header
    sent, matching an unauthenticated caller)."""
    mgr = await _init_db()

    app = FastAPI()
    app.include_router(router)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    await mgr.close()
    mgr._instance = None


async def _seed(
    *,
    sku: str = "br-011",
    model_r2_key: str | None = "3d-models/br-011/model.glb",
    status: str = "pending",
    fidelity_score: float | None = 91.2,
    fidelity_breakdown: dict | None = None,
    notes: str | None = None,
    reviewed_by: uuid.UUID | None = None,
    created_at: datetime | None = None,
) -> tuple[uuid.UUID, uuid.UUID]:
    """Persist a Model3DGeneration + Model3DReview pair directly (test setup only)."""
    gen_id = uuid.uuid4()
    review_id = uuid.uuid4()
    ts = created_at or datetime(2026, 1, 1, tzinfo=UTC)

    async with db_manager.session() as session:
        generation = Model3DGeneration(
            id=gen_id,
            sku=sku,
            task_id="tripo-task-abc",
            provider="tripo3d",
            format="glb",
            model_r2_key=model_r2_key,
        )
        session.add(generation)
        await session.flush()

        review = Model3DReview(
            id=review_id,
            generation_id=gen_id,
            fidelity_score=fidelity_score,
            fidelity_breakdown=fidelity_breakdown,
            status=status,
            notes=notes,
            reviewed_by=reviewed_by,
            created_at=ts,
            updated_at=ts,
        )
        session.add(review)

    return gen_id, review_id


def _pin_resolvers(
    monkeypatch: pytest.MonkeyPatch,
    *,
    image_path: str | None = "assets/images/products/br-011-front.jpg",
    r2_url: str | None = "https://r2.example.com/presigned-model-url",
) -> MagicMock:
    """Pin resolve_image + the R2 client to deterministic, assertable outputs.

    Mirrors tests/api/test_brand_assets.py's _pin_pipeline: the real
    resolve_image() depends on generated SOT data not present in this sparse
    worktree, and generate_presigned_url() needs real R2 credentials — both
    must be pinned for any test that isn't specifically exercising the
    missing-data fallback paths.
    """
    monkeypatch.setattr(qa_module, "resolve_image", lambda sku, role="front": image_path)

    fake_client = MagicMock()
    fake_client.generate_presigned_url.return_value = r2_url
    monkeypatch.setattr(qa_module, "_get_r2_client", lambda: fake_client)
    return fake_client


def _bearer_headers(*, sub: str, roles: list[str]) -> dict[str, str]:
    """Real, signed JWT headers — for exercising the actual get_current_user /
    require_developer dependencies (unauth_client has no overrides)."""
    from security.jwt_oauth2_auth import jwt_manager

    tokens = jwt_manager.create_token_pair(user_id=sub, roles=roles)
    return {"Authorization": f"Bearer {tokens.access_token}"}


# =============================================================================
# GET /qa/reviews
# =============================================================================


class TestListReviews:
    async def test_list_empty(self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
        _pin_resolvers(monkeypatch)
        response = await client.get("/qa/reviews")
        assert response.status_code == 200
        body = response.json()
        assert body == {
            "reviews": [],
            "total": 0,
            "pending_count": 0,
            "approved_count": 0,
            "rejected_count": 0,
        }

    async def test_list_returns_seeded_review(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ):
        fake_client = _pin_resolvers(monkeypatch)
        gen_id, review_id = await _seed(sku="br-011", status="pending")

        response = await client.get("/qa/reviews")
        assert response.status_code == 200
        body = response.json()

        assert body["total"] == 1
        assert body["pending_count"] == 1
        assert body["approved_count"] == 0
        assert body["rejected_count"] == 0

        review = body["reviews"][0]
        assert review["id"] == str(review_id)
        assert review["asset_id"] == "br-011"
        assert review["job_id"] == "tripo-task-abc"
        assert review["status"] == "pending"
        assert review["reference_image_url"] == (
            "https://skyyrose.test/wp-content/themes/skyyrose-flagship/"
            "assets/images/products/br-011-front.jpg"
        )
        assert review["generated_model_url"] == "https://r2.example.com/presigned-model-url"
        assert "reviewed_at" not in review
        assert "notes" not in review
        assert "reviewed_by" not in review
        assert "fidelity_breakdown" not in review

        fake_client.generate_presigned_url.assert_called_once_with(key="3d-models/br-011/model.glb")

    async def test_list_filters_by_status(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ):
        _pin_resolvers(monkeypatch)
        await _seed(sku="br-001", status="pending")
        await _seed(sku="br-002", status="approved")
        await _seed(sku="br-003", status="rejected")

        response = await client.get("/qa/reviews", params={"status": "approved"})
        assert response.status_code == 200
        body = response.json()

        assert body["total"] == 1
        assert body["reviews"][0]["asset_id"] == "br-002"
        # Counts describe the whole table, not just the filtered slice.
        assert body["pending_count"] == 1
        assert body["approved_count"] == 1
        assert body["rejected_count"] == 1

    async def test_list_omits_row_with_no_reference_image(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ):
        _pin_resolvers(monkeypatch, image_path=None)
        await _seed(sku="br-099")

        response = await client.get("/qa/reviews")
        assert response.status_code == 200
        body = response.json()

        assert body["reviews"] == []
        assert body["total"] == 0
        # Row still counts toward status totals even though it's unrenderable.
        assert body["pending_count"] == 1

    async def test_list_omits_row_with_no_r2_key(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ):
        _pin_resolvers(monkeypatch)
        await _seed(sku="br-098", model_r2_key=None)

        response = await client.get("/qa/reviews")
        assert response.status_code == 200
        body = response.json()

        assert body["reviews"] == []
        assert body["total"] == 0

    async def test_list_includes_fidelity_breakdown_when_present(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ):
        _pin_resolvers(monkeypatch)
        breakdown = {
            "geometry": 92.5,
            "materials": 88.0,
            "colors": 95.0,
            "proportions": 90.0,
            "branding": 97.0,
            "texture_detail": 85.5,
        }
        await _seed(sku="br-011", fidelity_breakdown=breakdown, status="approved")

        response = await client.get("/qa/reviews")
        body = response.json()
        assert body["reviews"][0]["fidelity_breakdown"] == breakdown

    async def test_list_requires_auth(self, unauth_client: AsyncClient):
        response = await unauth_client.get("/qa/reviews")
        assert response.status_code == 401

    async def test_list_insufficient_role_is_403(self, unauth_client: AsyncClient):
        # Reads expose presigned R2 URLs to unreleased models — gated to
        # ADMIN/DEVELOPER like the mutations, not any authenticated account.
        headers = _bearer_headers(sub=str(uuid.uuid4()), roles=["api_user"])
        response = await unauth_client.get("/qa/reviews", headers=headers)
        assert response.status_code == 403

    async def test_list_fails_closed_when_wp_site_url_unset(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ):
        """bug-230 fail-closed: an unset WP_SITE_URL must hard-fail, never
        silently emit a broken empty-host reference URL. _reference_image_url
        reads os.environ["WP_SITE_URL"] (not .get(...)), so it raises rather
        than fabricating a host-less URL — guards a future silent-default swap.
        resolve_image is pinned to a real path so the env read is reached."""
        _pin_resolvers(monkeypatch)
        await _seed(sku="br-011", status="pending")
        monkeypatch.delenv("WP_SITE_URL", raising=False)
        with pytest.raises(KeyError):
            await client.get("/qa/reviews")


# =============================================================================
# GET /qa/reviews/{id}
# =============================================================================


class TestGetReview:
    async def test_get_found(self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
        _pin_resolvers(monkeypatch)
        _, review_id = await _seed(sku="br-011")

        response = await client.get(f"/qa/reviews/{review_id}")
        assert response.status_code == 200
        assert response.json()["id"] == str(review_id)

    async def test_get_not_found(self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
        _pin_resolvers(monkeypatch)
        response = await client.get(f"/qa/reviews/{uuid.uuid4()}")
        assert response.status_code == 404

    async def test_get_malformed_id_is_422(self, client: AsyncClient):
        response = await client.get("/qa/reviews/not-a-uuid")
        assert response.status_code == 422

    async def test_get_insufficient_role_is_403(self, unauth_client: AsyncClient):
        # Role check runs before the 404 lookup, so a wrong-role caller gets
        # 403 even for a nonexistent id (mirrors test_patch_insufficient_role).
        headers = _bearer_headers(sub=str(uuid.uuid4()), roles=["api_user"])
        response = await unauth_client.get(f"/qa/reviews/{uuid.uuid4()}", headers=headers)
        assert response.status_code == 403

    async def test_regenerating_row_omits_stale_reviewer_and_timestamp(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ):
        """A row that was approved (reviewed_by=alice) then queued for
        regeneration must expose NEITHER the stale reviewer nor a review
        timestamp — attributing a queued re-run to a prior reviewer is wrong.
        Guards reviewed_by against drifting back to unconditional (reviewed_at
        is already gated; both must move together)."""
        _pin_resolvers(monkeypatch)
        prior_reviewer = uuid.uuid4()
        _, review_id = await _seed(sku="br-011", status="regenerating", reviewed_by=prior_reviewer)

        response = await client.get(f"/qa/reviews/{review_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "regenerating"
        assert "reviewed_by" not in body  # stale reviewer hidden
        assert "reviewed_at" not in body  # no review timestamp

    async def test_approved_row_surfaces_reviewer_and_timestamp(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ):
        """Positive counterpart: an actual approve decision DOES surface both
        reviewed_by and reviewed_at (so the gate isn't over-hiding)."""
        _pin_resolvers(monkeypatch)
        reviewer = uuid.uuid4()
        _, review_id = await _seed(sku="br-011", status="approved", reviewed_by=reviewer)

        body = (await client.get(f"/qa/reviews/{review_id}")).json()
        assert body["reviewed_by"] == str(reviewer)
        assert "reviewed_at" in body


# =============================================================================
# PATCH /qa/reviews/{id}
# =============================================================================


class TestPatchReview:
    async def test_approve_sets_status_reviewer_and_updated_at(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch, mock_user: MagicMock
    ):
        _pin_resolvers(monkeypatch)
        old_ts = datetime(2020, 1, 1, tzinfo=UTC)
        _, review_id = await _seed(sku="br-011", status="pending", created_at=old_ts)

        response = await client.patch(
            f"/qa/reviews/{review_id}",
            json={"status": "approved", "notes": "Matches reference on all axes."},
        )
        assert response.status_code == 200
        body = response.json()

        assert body["status"] == "approved"
        assert body["notes"] == "Matches reference on all axes."
        assert body["reviewed_by"] == mock_user.sub
        assert "reviewed_at" in body

        async with db_manager.session() as session:
            row = await session.get(Model3DReview, review_id)
            # sqlite's TIMESTAMP(timezone=True) round-trips as naive — compare
            # on a common (naive) footing rather than assuming tz-awareness.
            updated_naive = row.updated_at.replace(tzinfo=None)
            created_naive = row.created_at.replace(tzinfo=None)
            old_naive = old_ts.replace(tzinfo=None)

            assert row.status == "approved"
            assert updated_naive > old_naive
            assert created_naive == old_naive  # created_at must not be touched

    async def test_reject_sets_status(self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
        _pin_resolvers(monkeypatch)
        _, review_id = await _seed(sku="br-011", status="pending")

        response = await client.patch(
            f"/qa/reviews/{review_id}",
            json={"status": "rejected", "notes": "Color desaturation vs reference."},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "rejected"

    async def test_patch_not_found(self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
        _pin_resolvers(monkeypatch)
        response = await client.patch(
            f"/qa/reviews/{uuid.uuid4()}",
            json={"status": "approved"},
        )
        assert response.status_code == 404

    async def test_patch_requires_auth(self, unauth_client: AsyncClient):
        response = await unauth_client.patch(
            f"/qa/reviews/{uuid.uuid4()}",
            json={"status": "approved"},
        )
        assert response.status_code == 401

    async def test_patch_insufficient_role_is_403(self, unauth_client: AsyncClient):
        headers = _bearer_headers(sub=str(uuid.uuid4()), roles=["api_user"])
        response = await unauth_client.patch(
            f"/qa/reviews/{uuid.uuid4()}",
            json={"status": "approved"},
            headers=headers,
        )
        assert response.status_code == 403

    async def test_patch_with_non_uuid_reviewer_sub_is_a_clean_500(
        self, unauth_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ):
        """security/jwt_oauth2_auth.py's dev-mode login fallback sets sub to
        the raw username (not a UUID) — this must not surface as a raw,
        unhandled ValueError/stack trace to the client."""
        _pin_resolvers(monkeypatch)
        _, review_id = await _seed(sku="br-011", status="pending")

        headers = _bearer_headers(sub="dev-mode-username", roles=["developer"])
        response = await unauth_client.patch(
            f"/qa/reviews/{review_id}",
            json={"status": "approved"},
            headers=headers,
        )
        assert response.status_code == 500
        assert "Traceback" not in response.text

    async def test_patch_rejects_invalid_status(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ):
        _pin_resolvers(monkeypatch)
        _, review_id = await _seed(sku="br-011")

        response = await client.patch(
            f"/qa/reviews/{review_id}",
            json={"status": "pending"},  # not a valid PATCH target
        )
        assert response.status_code == 422


# =============================================================================
# POST /qa/reviews/{id}/regenerate
# =============================================================================


class TestRegenerateReview:
    async def test_regenerate_sets_status(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ):
        _pin_resolvers(monkeypatch)
        _, review_id = await _seed(sku="br-011", status="rejected")

        response = await client.post(f"/qa/reviews/{review_id}/regenerate")
        assert response.status_code == 200
        assert response.json()["status"] == "regenerating"

        async with db_manager.session() as session:
            row = await session.get(Model3DReview, review_id)
            assert row.status == "regenerating"

    async def test_regenerate_not_found(self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
        _pin_resolvers(monkeypatch)
        response = await client.post(f"/qa/reviews/{uuid.uuid4()}/regenerate")
        assert response.status_code == 404

    async def test_regenerate_handler_makes_no_outbound_dispatch_calls(self):
        """Regression guard for the STOP-AND-SHOW boundary: the regenerate
        handler's own source must never reference an HTTP client or a Tripo
        dispatch entrypoint. A functional test using the real ASGI test
        client can't distinguish "no outbound call" from "call happened to
        a mocked transport" (the test client itself is an httpx.AsyncClient
        talking over ASGITransport) — static inspection of the handler body
        is the precise way to prove this invariant.
        """
        import inspect

        source = inspect.getsource(qa_module.regenerate_review)
        forbidden_tokens = (
            "httpx",
            "requests.",
            "TripoClient",
            "dispatch_sku",
            "tripo_agent",
            "aiohttp",
        )
        found = [token for token in forbidden_tokens if token in source]
        assert not found, f"regenerate_review references outbound-call tokens: {found}"

    async def test_regenerate_requires_auth(self, unauth_client: AsyncClient):
        response = await unauth_client.post(f"/qa/reviews/{uuid.uuid4()}/regenerate")
        assert response.status_code == 401

    async def test_regenerate_insufficient_role_is_403(self, unauth_client: AsyncClient):
        headers = _bearer_headers(sub=str(uuid.uuid4()), roles=["api_user"])
        response = await unauth_client.post(
            f"/qa/reviews/{uuid.uuid4()}/regenerate", headers=headers
        )
        assert response.status_code == 403

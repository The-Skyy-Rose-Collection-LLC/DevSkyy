"""
Enterprise API v2 — Character Management

CRUD for SkyyRose brand characters. Persists character data in Redis
with a 30-day TTL. Wraps CharacterCreationAgent.create_sheet().

Prefix: /api/v2/characters
Auth:   X-API-Key header (matches v1 pattern)
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/characters", tags=["Characters v2"])

# Module-level imports for mockability in tests
try:
    from skyyrose.elite_studio.character.agent import CharacterCreationAgent
    from skyyrose.elite_studio.character.models import CharacterSpec
except ImportError:  # pragma: no cover
    CharacterCreationAgent = None  # type: ignore[assignment,misc]
    CharacterSpec = None  # type: ignore[assignment,misc]

# ---------------------------------------------------------------------------
# Redis key constants
# ---------------------------------------------------------------------------

_CHAR_KEY_PREFIX = "elite_studio:characters:"
_CHAR_TTL = 86_400 * 30  # 30-day TTL


# ---------------------------------------------------------------------------
# Auth dependency (mirrors v1)
# ---------------------------------------------------------------------------


def _get_api_key_dependency():
    async def _check_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
        expected = os.getenv("API_KEY", "")
        if not expected:
            return None
        if x_api_key != expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing X-API-Key header",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        return x_api_key

    return _check_api_key


_api_key_dep = _get_api_key_dependency()


# ---------------------------------------------------------------------------
# Pydantic V2 models
# ---------------------------------------------------------------------------


class CreateCharacterRequest(BaseModel):
    model_config = {"str_strip_whitespace": True}

    name: str
    style: str = "pixar-chibi"
    body_description: str = ""
    face_features: str = ""
    outfit_base: str = ""
    brand_elements: list[str] = Field(default_factory=list)

    @classmethod
    def _validate_style(cls, v: str) -> str:
        valid = {"pixar-chibi", "realistic", "illustration"}
        if v not in valid:
            raise ValueError(f"style must be one of {sorted(valid)}, got: {v!r}")
        return v


class UpdateCharacterRequest(BaseModel):
    model_config = {"str_strip_whitespace": True}

    style: str | None = None
    body_description: str | None = None
    face_features: str | None = None
    outfit_base: str | None = None
    brand_elements: list[str] | None = None


class CharacterResponse(BaseModel):
    character_id: str
    name: str
    style: str
    front_view_prompt: str
    expression_grid_prompt: str
    sprite_description: str
    created_at: str


class CharacterListResponse(BaseModel):
    characters: list[CharacterResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Redis helpers
# ---------------------------------------------------------------------------


def _get_redis() -> Any | None:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        import redis as redis_lib

        r = redis_lib.from_url(redis_url, decode_responses=True, socket_timeout=3)
        r.ping()
        return r
    except Exception as exc:
        logger.warning("characters v2: Redis unavailable — %s", exc)
        return None


def _require_redis() -> Any:
    r = _get_redis()
    if r is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis unavailable — cannot process request",
        )
    return r


def _store_character(r: Any, character: CharacterResponse) -> None:
    key = f"{_CHAR_KEY_PREFIX}{character.character_id}"
    try:
        r.setex(key, _CHAR_TTL, character.model_dump_json())
    except Exception as exc:
        logger.warning("Failed to store character %s: %s", character.character_id, exc)


def _fetch_character(r: Any, character_id: str) -> CharacterResponse | None:
    key = f"{_CHAR_KEY_PREFIX}{character_id}"
    raw = r.get(key)
    if not raw:
        return None
    try:
        return CharacterResponse.model_validate_json(raw)
    except Exception as exc:
        logger.warning("Failed to deserialise character %s: %s", character_id, exc)
        return None


# ---------------------------------------------------------------------------
# Internal: build CharacterResponse from spec + sheet
# ---------------------------------------------------------------------------


def _build_character_response(
    character_id: str,
    request: CreateCharacterRequest,
    created_at: str,
) -> CharacterResponse:
    """Invoke CharacterCreationAgent and map result to CharacterResponse."""
    spec = CharacterSpec(
        name=request.name,
        style=request.style,
        body_description=request.body_description,
        face_features=request.face_features,
        outfit_base=request.outfit_base,
        brand_elements=tuple(request.brand_elements),
        reference_paths=(),
    )
    agent = CharacterCreationAgent()
    sheet = agent.create_sheet(spec)

    if not sheet.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Character creation failed: {sheet.error}",
        )

    return CharacterResponse(
        character_id=character_id,
        name=request.name,
        style=request.style,
        front_view_prompt=sheet.front_view_prompt,
        expression_grid_prompt=sheet.expression_grid_prompt,
        sprite_description=sheet.sprite_description,
        created_at=created_at,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=CharacterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new character",
)
async def create_character(
    body: CreateCharacterRequest,
    _auth=Depends(_api_key_dep),
):
    """Create a new SkyyRose brand character.

    Calls ``CharacterCreationAgent.create_sheet()`` to generate prompts,
    then persists the character in Redis with a 30-day TTL.
    """
    character_id = uuid.uuid4().hex
    created_at = datetime.now(UTC).isoformat()

    character = _build_character_response(character_id, body, created_at)

    r = _get_redis()
    if r is not None:
        _store_character(r, character)

    return character


@router.get(
    "/rosie",
    response_model=CharacterResponse,
    summary="Get the canonical SkyyRose mascot character",
)
async def get_rosie(
    _auth=Depends(_api_key_dep),
):
    """Return the canonical Rosie character spec.

    Generates fresh prompts from the built-in Rosie spec on each call
    (or returns cached version if Redis is available and warm).
    """
    r = _get_redis()
    canonical_id = "rosie_canonical"

    if r is not None:
        cached = _fetch_character(r, canonical_id)
        if cached is not None:
            return cached

    agent = CharacterCreationAgent()
    sheet = agent.create_skyyrose_rosie()

    if not sheet.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rosie character generation failed: {sheet.error}",
        )

    rosie = CharacterResponse(
        character_id=canonical_id,
        name="Rosie",
        style="pixar-chibi",
        front_view_prompt=sheet.front_view_prompt,
        expression_grid_prompt=sheet.expression_grid_prompt,
        sprite_description=sheet.sprite_description,
        created_at=datetime.now(UTC).isoformat(),
    )
    if r is not None:
        _store_character(r, rosie)

    return rosie


@router.get(
    "/{character_id}",
    response_model=CharacterResponse,
    summary="Get a character by ID",
)
async def get_character(
    character_id: str,
    _auth=Depends(_api_key_dep),
):
    """Retrieve a previously created character by its ID."""
    r = _require_redis()
    character = _fetch_character(r, character_id)
    if character is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character not found: {character_id}",
        )
    return character


@router.get(
    "",
    response_model=CharacterListResponse,
    summary="List characters (paginated)",
)
async def list_characters(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _auth=Depends(_api_key_dep),
):
    """List all stored characters with pagination."""
    r = _require_redis()
    try:
        keys = r.keys(f"{_CHAR_KEY_PREFIX}*")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis error: {exc}",
        ) from exc

    characters: list[CharacterResponse] = []
    for key in keys:
        raw = r.get(key)
        if not raw:
            continue
        try:
            characters.append(CharacterResponse.model_validate_json(raw))
        except Exception:
            continue

    characters.sort(key=lambda c: c.created_at, reverse=True)
    total = len(characters)
    start = (page - 1) * page_size
    paginated = characters[start : start + page_size]

    return CharacterListResponse(
        characters=paginated,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch(
    "/{character_id}",
    response_model=CharacterResponse,
    summary="Update a character spec (regenerates sheet)",
)
async def update_character(
    character_id: str,
    body: UpdateCharacterRequest,
    _auth=Depends(_api_key_dep),
):
    """Update a character's spec fields and regenerate its sheet prompts.

    Only provided fields are updated; omitted fields retain their current values.
    """
    r = _require_redis()
    existing = _fetch_character(r, character_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character not found: {character_id}",
        )

    # Reconstruct a CreateCharacterRequest with merged values
    updated_request = CreateCharacterRequest(
        name=existing.name,
        style=body.style if body.style is not None else existing.style,
        body_description=body.body_description or "",
        face_features=body.face_features or "",
        outfit_base=body.outfit_base or "",
        brand_elements=body.brand_elements if body.brand_elements is not None else [],
    )

    updated = _build_character_response(character_id, updated_request, existing.created_at)
    _store_character(r, updated)
    return updated

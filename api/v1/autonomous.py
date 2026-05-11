import json
import logging
import uuid
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from security.jwt_oauth2_auth import TokenPayload, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["autonomous"])

_HISTORY_PATH = Path("tasks/autonomous-history.json")
_history: deque[dict[str, Any]] = deque(maxlen=200)
_history_loaded = False

_OPERATIONS: dict[str, dict[str, Any]] = {
    "round_table": {
        "id": "round_table",
        "name": "Round Table Orchestration",
        "description": "Multi-provider LLM competition for quality content generation",
        "status": "stopped",
        "critical": False,
    },
    "self_healing": {
        "id": "self_healing",
        "name": "Self-Healing Monitor",
        "description": "Continuous health monitoring and automatic service recovery",
        "status": "stopped",
        "critical": True,
    },
    "content_generation": {
        "id": "content_generation",
        "name": "Content Generation Agent",
        "description": "Autonomous product description and marketing content generation",
        "status": "stopped",
        "critical": False,
    },
    "scene_builder": {
        "id": "scene_builder",
        "name": "3D Scene Builder",
        "description": "Autonomous 3D environment generation for luxury product visualization",
        "status": "stopped",
        "critical": False,
    },
}


class AutonomousOperation(BaseModel):
    id: str
    name: str
    description: str
    status: Literal["running", "stopped", "error"]
    critical: bool
    last_event: str | None = None
    last_event_at: str | None = None


class AutonomousHistoryEntry(BaseModel):
    id: str
    operation_id: str
    operation_name: str
    action: Literal["start", "stop", "error"]
    timestamp: str
    message: str


class AutonomousOperationsResponse(BaseModel):
    operations: list[AutonomousOperation]
    total: int


def _load_history() -> None:
    global _history_loaded
    if _history_loaded:
        return
    _history_loaded = True
    if _HISTORY_PATH.exists():
        try:
            data = json.loads(_HISTORY_PATH.read_text())
            for entry in data[-200:]:
                _history.append(entry)
        except (json.JSONDecodeError, KeyError):
            logger.warning("Failed to load autonomous history — starting fresh")


def _persist_history() -> None:
    try:
        _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        _HISTORY_PATH.write_text(json.dumps(list(_history), indent=2))
    except OSError:
        logger.warning("Failed to persist autonomous history")


def _log_event(operation_id: str, action: Literal["start", "stop", "error"], message: str) -> None:
    op = _OPERATIONS.get(operation_id)
    entry: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "operation_id": operation_id,
        "operation_name": op["name"] if op else operation_id,
        "action": action,
        "timestamp": datetime.now(UTC).isoformat(),
        "message": message,
    }
    _history.appendleft(entry)
    _persist_history()


def _build_operation(op: dict[str, Any]) -> AutonomousOperation:
    last_entry = next((e for e in _history if e["operation_id"] == op["id"]), None)
    return AutonomousOperation(
        id=op["id"],
        name=op["name"],
        description=op["description"],
        status=op["status"],
        critical=op["critical"],
        last_event=last_entry["action"] if last_entry else None,
        last_event_at=last_entry["timestamp"] if last_entry else None,
    )


@router.get(
    "/autonomous/operations",
    response_model=AutonomousOperationsResponse,
    status_code=status.HTTP_200_OK,
)
async def list_operations(
    user: TokenPayload = Depends(get_current_user),
) -> AutonomousOperationsResponse:
    _load_history()
    ops = [_build_operation(op) for op in _OPERATIONS.values()]
    return AutonomousOperationsResponse(operations=ops, total=len(ops))


@router.post(
    "/autonomous/operations/{operation_id}/start",
    response_model=AutonomousOperation,
    status_code=status.HTTP_200_OK,
)
async def start_operation(
    operation_id: str,
    user: TokenPayload = Depends(get_current_user),
) -> AutonomousOperation:
    _load_history()
    op = _OPERATIONS.get(operation_id)
    if op is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Operation '{operation_id}' not found"
        )
    if op["status"] == "running":
        return _build_operation(op)
    op["status"] = "running"
    _log_event(operation_id, "start", f"{op['name']} started")
    logger.info("Autonomous operation started: %s", operation_id)
    return _build_operation(op)


@router.post(
    "/autonomous/operations/{operation_id}/stop",
    response_model=AutonomousOperation,
    status_code=status.HTTP_200_OK,
)
async def stop_operation(
    operation_id: str,
    user: TokenPayload = Depends(get_current_user),
) -> AutonomousOperation:
    _load_history()
    op = _OPERATIONS.get(operation_id)
    if op is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Operation '{operation_id}' not found"
        )
    if op["status"] == "stopped":
        return _build_operation(op)
    op["status"] = "stopped"
    _log_event(operation_id, "stop", f"{op['name']} stopped")
    logger.info("Autonomous operation stopped: %s", operation_id)
    return _build_operation(op)


@router.get(
    "/autonomous/operations/{operation_id}/history",
    response_model=list[AutonomousHistoryEntry],
    status_code=status.HTTP_200_OK,
)
async def get_operation_history(
    operation_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    user: TokenPayload = Depends(get_current_user),
) -> list[AutonomousHistoryEntry]:
    _load_history()
    if operation_id not in _OPERATIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Operation '{operation_id}' not found"
        )
    entries = [e for e in _history if e["operation_id"] == operation_id][:limit]
    return [AutonomousHistoryEntry(**e) for e in entries]

"""
Stdlib Logging Utility
======================

Lightweight, dependency-free logger for scripts, CLIs, and standalone tools
that should not pull the structlog stack used by ``utils/logging_utils.py``
and ``core/structured_logging.py``.

Features:
- Console + rotating file handlers
- Optional JSON formatter for machine ingestion
- Env-driven level (``LOG_LEVEL``) with explicit override
- Child-logger factory once root is configured
- Context manager for temporary level changes
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

_DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DEFAULT_DATEFMT = "%Y-%m-%dT%H:%M:%S%z"
_MAX_BYTES = 10 * 1024 * 1024
_BACKUP_COUNT = 5
_RESERVED_RECORD_ATTRS = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }
)


class JsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON for log shippers."""

    def __init__(self, *, datefmt: str = _DEFAULT_DATEFMT) -> None:
        super().__init__(datefmt=datefmt)

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)
        for key, value in record.__dict__.items():
            if key in _RESERVED_RECORD_ATTRS or key.startswith("_"):
                continue
            payload[key] = _safe_json_value(value)
        return json.dumps(payload, default=str, separators=(",", ":"))


def _safe_json_value(value: object) -> object:
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        return repr(value)
    return value


@dataclass(frozen=True)
class LoggerConfig:
    """Immutable logger configuration."""

    name: str
    level: int = logging.INFO
    log_file: Path | None = None
    json_output: bool = False
    max_bytes: int = _MAX_BYTES
    backup_count: int = _BACKUP_COUNT
    propagate: bool = False
    stream: object = field(default=None)


def _resolve_level(explicit: int | str | None) -> int:
    if explicit is None:
        explicit = os.environ.get("LOG_LEVEL", "INFO")
    if isinstance(explicit, int):
        return explicit
    level = logging.getLevelName(explicit.upper())
    if not isinstance(level, int):
        raise ValueError(f"invalid LOG_LEVEL value: {explicit!r}")
    return level


def _build_formatter(json_output: bool) -> logging.Formatter:
    if json_output:
        return JsonFormatter()
    return logging.Formatter(fmt=_DEFAULT_FORMAT, datefmt=_DEFAULT_DATEFMT)


def setup_logger(
    name: str,
    *,
    level: int | str | None = None,
    log_file: str | Path | None = None,
    json_output: bool = False,
    max_bytes: int = _MAX_BYTES,
    backup_count: int = _BACKUP_COUNT,
    propagate: bool = False,
    stream: object = None,
) -> logging.Logger:
    """Configure and return a logger.

    Replaces any prior handlers attached by this function so repeat calls are
    idempotent. ``log_file`` parent directories are created if missing.
    """
    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive")
    if backup_count < 0:
        raise ValueError("backup_count must be non-negative")

    resolved_level = _resolve_level(level)
    logger = logging.getLogger(name)
    logger.setLevel(resolved_level)
    logger.propagate = propagate

    for handler in list(logger.handlers):
        if getattr(handler, "_devskyy_managed", False):
            logger.removeHandler(handler)
            handler.close()

    formatter = _build_formatter(json_output)

    console = logging.StreamHandler(stream or sys.stderr)
    console.setLevel(resolved_level)
    console.setFormatter(formatter)
    console._devskyy_managed = True  # type: ignore[attr-defined]
    logger.addHandler(console)

    if log_file is not None:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        rotating = logging.handlers.RotatingFileHandler(
            filename=path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        rotating.setLevel(resolved_level)
        rotating.setFormatter(formatter)
        rotating._devskyy_managed = True  # type: ignore[attr-defined]
        logger.addHandler(rotating)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a logger by name. Call ``setup_logger`` first for root config."""
    return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    context: Mapping[str, object] | None = None,
    *,
    exc_info: bool = False,
) -> None:
    """Emit a record with ``extra`` populated from ``context``.

    Keys colliding with reserved ``LogRecord`` attributes are prefixed with
    ``ctx_`` to avoid the ``KeyError`` the stdlib raises on collision.
    """
    extra: dict[str, object] = {}
    if context:
        for key, value in context.items():
            target = f"ctx_{key}" if key in _RESERVED_RECORD_ATTRS else key
            extra[target] = value
    logger.log(level, message, extra=extra, exc_info=exc_info)


@contextmanager
def temporary_level(logger: logging.Logger, level: int | str) -> Iterator[logging.Logger]:
    """Temporarily change ``logger`` level inside a ``with`` block."""
    resolved = _resolve_level(level)
    previous = logger.level
    logger.setLevel(resolved)
    try:
        yield logger
    finally:
        logger.setLevel(previous)


__all__ = [
    "JsonFormatter",
    "LoggerConfig",
    "get_logger",
    "log_with_context",
    "setup_logger",
    "temporary_level",
]

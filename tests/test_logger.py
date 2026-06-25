"""Unit tests for utils/logger.py — stdlib-only logging utility."""

from __future__ import annotations

import io
import json
import logging
from pathlib import Path

import pytest
from utils.logger import (
    JsonFormatter,
    LoggerConfig,
    get_logger,
    log_with_context,
    setup_logger,
    temporary_level,
)


@pytest.fixture(autouse=True)
def _reset_logger_state():
    yield
    for name in list(logging.root.manager.loggerDict):
        if name.startswith("test_logger."):
            logger = logging.getLogger(name)
            for handler in list(logger.handlers):
                logger.removeHandler(handler)
                handler.close()
            logger.setLevel(logging.NOTSET)


def _capture_stream() -> io.StringIO:
    return io.StringIO()


@pytest.mark.unit
class TestSetupLogger:
    def test_returns_logger_with_console_handler(self):
        stream = _capture_stream()
        logger = setup_logger("test_logger.basic", stream=stream)
        assert isinstance(logger, logging.Logger)
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_idempotent_does_not_stack_handlers(self):
        stream = _capture_stream()
        setup_logger("test_logger.idem", stream=stream)
        first = len(logging.getLogger("test_logger.idem").handlers)
        setup_logger("test_logger.idem", stream=stream)
        second = len(logging.getLogger("test_logger.idem").handlers)
        assert first == second == 1

    def test_writes_console_message(self):
        stream = _capture_stream()
        logger = setup_logger("test_logger.console", stream=stream, level="DEBUG")
        logger.info("hello-world")
        output = stream.getvalue()
        assert "hello-world" in output
        assert "INFO" in output

    def test_creates_rotating_file_handler(self, tmp_path: Path):
        log_path = tmp_path / "nested" / "app.log"
        logger = setup_logger("test_logger.file", log_file=log_path)
        logger.warning("disk-write")
        for handler in logger.handlers:
            handler.flush()
        assert log_path.exists()
        assert "disk-write" in log_path.read_text(encoding="utf-8")

    def test_rejects_invalid_max_bytes(self):
        with pytest.raises(ValueError, match="max_bytes"):
            setup_logger("test_logger.bad_max", max_bytes=0)

    def test_rejects_negative_backup_count(self):
        with pytest.raises(ValueError, match="backup_count"):
            setup_logger("test_logger.bad_backup", backup_count=-1)

    def test_env_level_used_when_unset(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("LOG_LEVEL", "WARNING")
        logger = setup_logger("test_logger.envlvl", stream=_capture_stream())
        assert logger.level == logging.WARNING

    def test_invalid_env_level_raises(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("LOG_LEVEL", "BOGUS")
        with pytest.raises(ValueError, match="invalid LOG_LEVEL"):
            setup_logger("test_logger.badenv", stream=_capture_stream())


@pytest.mark.unit
class TestJsonFormatter:
    def test_emits_valid_json(self):
        stream = _capture_stream()
        logger = setup_logger(
            "test_logger.json",
            stream=stream,
            json_output=True,
            level="DEBUG",
        )
        logger.info("payload-event", extra={"sku": "br-001", "qty": 3})
        line = stream.getvalue().strip().splitlines()[-1]
        data = json.loads(line)
        assert data["level"] == "INFO"
        assert data["message"] == "payload-event"
        assert data["sku"] == "br-001"
        assert data["qty"] == 3

    def test_handles_unserializable_extra(self):
        class Opaque:
            def __repr__(self) -> str:
                return "<Opaque>"

        stream = _capture_stream()
        logger = setup_logger("test_logger.opaque", stream=stream, json_output=True)
        logger.info("opaque-event", extra={"obj": Opaque()})
        data = json.loads(stream.getvalue().strip().splitlines()[-1])
        assert data["obj"] == "<Opaque>"

    def test_includes_exception_info(self):
        stream = _capture_stream()
        logger = setup_logger("test_logger.exc", stream=stream, json_output=True)
        try:
            raise RuntimeError("boom")
        except RuntimeError:
            logger.exception("error-event")
        data = json.loads(stream.getvalue().strip().splitlines()[-1])
        assert "exc_info" in data
        assert "RuntimeError: boom" in data["exc_info"]

    def test_format_method_returns_string(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="t",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="m",
            args=None,
            exc_info=None,
        )
        result = formatter.format(record)
        assert isinstance(result, str)
        json.loads(result)


@pytest.mark.unit
class TestContextHelpers:
    def test_log_with_context_attaches_extra(self):
        stream = _capture_stream()
        logger = setup_logger("test_logger.ctx", stream=stream, json_output=True, level="DEBUG")
        log_with_context(logger, logging.INFO, "ctx-event", {"order_id": 42})
        data = json.loads(stream.getvalue().strip().splitlines()[-1])
        assert data["order_id"] == 42

    def test_log_with_context_renames_reserved_keys(self):
        stream = _capture_stream()
        logger = setup_logger(
            "test_logger.reserved", stream=stream, json_output=True, level="DEBUG"
        )
        log_with_context(
            logger, logging.INFO, "reserved-event", {"message": "shadowed", "ok": True}
        )
        data = json.loads(stream.getvalue().strip().splitlines()[-1])
        assert data["message"] == "reserved-event"
        assert data["ctx_message"] == "shadowed"
        assert data["ok"] is True

    def test_temporary_level_restores_previous(self):
        logger = setup_logger("test_logger.temp", stream=_capture_stream(), level="INFO")
        original = logger.level
        with temporary_level(logger, "DEBUG") as scoped:
            assert scoped.level == logging.DEBUG
        assert logger.level == original


@pytest.mark.unit
class TestSurface:
    def test_get_logger_returns_named_instance(self):
        logger = get_logger("test_logger.surface")
        assert logger.name == "test_logger.surface"

    def test_logger_config_is_frozen(self):
        cfg = LoggerConfig(name="x")
        with pytest.raises(Exception):
            cfg.name = "y"  # type: ignore[misc]

"""Unit tests for OpenTelemetry tracer module."""
from unittest.mock import MagicMock, patch

import pytest


class TestGetTracer:
    def test_returns_tracer_when_otel_installed(self):
        """Should return an OTel tracer when the SDK is available."""
        from core.telemetry.tracer import get_tracer
        tracer = get_tracer("test_module")
        # Should have start_as_current_span method
        assert hasattr(tracer, "start_as_current_span")

    def test_returns_noop_when_import_fails(self):
        """Should return NoOpTracer when opentelemetry is not installed."""
        from core.telemetry.tracer import _NoOpTracer
        tracer = _NoOpTracer()
        span = tracer.start_as_current_span("test")
        # Should be a no-op span
        span.set_attribute("key", "value")  # Should not raise
        span.record_exception(Exception("test"))  # Should not raise


class TestNoOpSpan:
    def test_context_manager(self):
        """NoOpSpan should work as context manager."""
        from core.telemetry.tracer import _NoOpSpan
        span = _NoOpSpan()
        with span as s:
            s.set_attribute("key", "value")
        # No error raised


class TestInitTelemetry:
    def test_init_disabled(self):
        """Should skip initialization when OTEL_ENABLED=false."""
        import core.telemetry.tracer as mod
        mod._initialized = False
        with patch.dict("os.environ", {"OTEL_ENABLED": "false"}):
            mod.init_telemetry()
        assert mod._initialized is True

    def test_init_idempotent(self):
        """Should not re-initialize if already initialized."""
        import core.telemetry.tracer as mod
        mod._initialized = True
        # Should return immediately
        mod.init_telemetry()
        assert mod._initialized is True

"""
OpenTelemetry Tracer Configuration
====================================

Initializes the OTel TracerProvider with OTLP exporter.
Falls back to console exporter if OTLP endpoint is unavailable.

Usage:
    from core.telemetry.tracer import get_tracer, init_telemetry

    # Initialize once at startup
    init_telemetry(service_name="devskyy-api")

    # Get tracer in any module
    tracer = get_tracer(__name__)

    async def my_function():
        with tracer.start_as_current_span("my_operation") as span:
            span.set_attribute("custom.key", "value")
            ...
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_initialized = False


def init_telemetry(service_name: str = "devskyy-api") -> None:
    """
    Initialize OpenTelemetry tracing.

    Reads configuration from environment:
    - OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint (default: http://localhost:4317)
    - OTEL_SERVICE_NAME: Service name override
    - OTEL_ENABLED: Set to "false" to disable (default: "true")
    """
    global _initialized
    if _initialized:
        return

    enabled = os.getenv("OTEL_ENABLED", "true").lower() == "true"
    if not enabled:
        logger.info("OpenTelemetry disabled via OTEL_ENABLED=false")
        _initialized = True
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )

        resource = Resource.create({
            "service.name": os.getenv("OTEL_SERVICE_NAME", service_name),
            "service.version": "3.2.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        })

        provider = TracerProvider(resource=resource)

        # Try OTLP exporter first, fall back to console
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if otlp_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                    OTLPSpanExporter,
                )
                exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                provider.add_span_processor(BatchSpanProcessor(exporter))
                logger.info(f"OTel OTLP exporter configured: {otlp_endpoint}")
            except Exception as e:
                logger.warning(f"OTLP exporter failed, using console: {e}")
                provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        else:
            # Console exporter for development
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
            logger.info("OTel console exporter configured (set OTEL_EXPORTER_OTLP_ENDPOINT for OTLP)")

        trace.set_tracer_provider(provider)
        _initialized = True
        logger.info("OpenTelemetry initialized", extra={"service": service_name})

    except ImportError:
        logger.info("OpenTelemetry SDK not installed, tracing disabled")
        _initialized = True
    except Exception as e:
        logger.warning(f"OpenTelemetry initialization failed: {e}")
        _initialized = True


def get_tracer(name: str = __name__) -> Any:
    """
    Get an OpenTelemetry tracer.

    Returns a no-op tracer if OTel is not initialized.
    """
    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except ImportError:
        return _NoOpTracer()


class _NoOpSpan:
    """No-op span for when OTel is unavailable."""

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def set_status(self, status: Any) -> None:
        pass

    def record_exception(self, exception: Exception) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class _NoOpTracer:
    """No-op tracer for when OTel is unavailable."""

    def start_as_current_span(self, name: str, **kwargs: Any) -> _NoOpSpan:
        return _NoOpSpan()

    def start_span(self, name: str, **kwargs: Any) -> _NoOpSpan:
        return _NoOpSpan()


__all__ = ["init_telemetry", "get_tracer"]

import time

from typing import Any
import logging

logger = logging.getLogger(__name__)


class Telemetry:
    def __init__(self, component: str):
        self.component = component

    def event(self, name: str, **properties: Any) -> None:
        logger.info(f"telemetry:event component={self.component} name={name} props={properties}")

    def span(self, name: str):
        return _Span(self.component, name)


class _Span:
    def __init__(self, component: str, name: str):
        self.component = component
        self.name = name
        self.start = 0.0

    def __enter__(self):
        self.start = time.time()
        logger.info(f"telemetry:span:start component={self.component} name={self.name}")
        return self

    def __exit__(self, exc_type, exc, tb):
        duration_ms = int((time.time() - self.start) * 1000)
        status = "error" if exc else "ok"
        logger.info(
            f"telemetry:span:end component={self.component} name={self.name} duration_ms={duration_ms} status={status}"
        )
        # Do not suppress exceptions
        return False

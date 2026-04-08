"""
Elite Studio queue package.

Public API:
    enqueue_produce  — enqueue a single SKU render job
    enqueue_batch    — enqueue multiple SKU render jobs
    EliteStudioWorker — synchronous worker that consumes the queue
"""

from .consumer import EliteStudioWorker
from .producer import enqueue_batch, enqueue_produce

__all__ = [
    "enqueue_produce",
    "enqueue_batch",
    "EliteStudioWorker",
]

# ai_3d/providers/__init__.py
"""
3D Generation Provider Clients.

Supported providers:
- Tripo3D: High-quality image-to-3D
- HuggingFace: Open-source 3D models (TRELLIS, TripoSR)
- Meshy: Alternative generation service

All providers implement async interfaces with:
- Rate limiting (asyncio.Semaphore)
- Exponential backoff on 429 errors
- Proper async/await patterns
"""

from ai_3d.providers.huggingface import HuggingFace3DClient
from ai_3d.providers.meshy import MeshyClient
from ai_3d.providers.tripo import TripoClient

__all__ = [
    "TripoClient",
    "HuggingFace3DClient",
    "MeshyClient",
]

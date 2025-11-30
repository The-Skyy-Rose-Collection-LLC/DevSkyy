"""
API Clients for 3D Clothing Asset Automation

Provides async clients for:
- Tripo3D: Text-to-3D and image-to-3D generation
- FASHN: Virtual try-on processing
- WordPress: Media upload to WooCommerce

All clients follow enterprise patterns:
- Async/await for all I/O
- Structured error handling
- Rate limiting and retry logic
- PII sanitization in logs
"""

from agent.modules.clothing.clients.fashn_client import FASHNClient
from agent.modules.clothing.clients.tripo3d_client import Tripo3DClient
from agent.modules.clothing.clients.wordpress_media import WordPressMediaClient

__all__ = [
    "Tripo3DClient",
    "FASHNClient",
    "WordPressMediaClient",
]

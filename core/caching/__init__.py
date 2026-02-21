"""
Multi-Tier Caching System
==========================

L1 (in-memory LRU) → L2 (Redis) → L3 (CDN, static assets)
"""

from core.caching.multi_tier_cache import MultiTierCache, cached

__all__ = ["MultiTierCache", "cached"]

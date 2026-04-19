"""
Core Middleware
==============

FastAPI ASGI middleware stack for the DevSkyy enterprise platform.
"""

from .tenant import tenant_middleware

__all__ = ["tenant_middleware"]

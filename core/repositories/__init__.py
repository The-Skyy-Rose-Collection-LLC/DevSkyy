"""Core repository interfaces."""

from core.repositories.interfaces import (
    IOrderRepository,
    IProductRepository,
    IRepository,
    IUserRepository,
)

__all__ = [
    "IRepository",
    "IUserRepository",
    "IProductRepository",
    "IOrderRepository",
]

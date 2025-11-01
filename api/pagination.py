from pydantic import BaseModel, Field

from typing import Generic, List, Optional, TypeVar

"""
API Pagination Utilities for Grade A+ API Score
Implements cursor-based and offset-based pagination
"""


T = TypeVar("T")


class PaginationParams(BaseModel):
    """Standard pagination parameters"""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")

    @property
    def offset(self) -> int:
        """Calculate offset from page and page_size"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit (alias for page_size)"""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response with metadata"""

    items: List[T] = Field(description="List of items for current page")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_previous: bool = Field(description="Whether there is a previous page")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5,
                "has_next": True,
                "has_previous": False,
            }
        }


def create_paginated_response(items: List[T], total: int, page: int, page_size: int) -> PaginatedResponse[T]:
    """
    Create paginated response from items and metadata

    Args:
        items: List of items for current page
        total: Total number of items
        page: Current page number
        page_size: Items per page

    Returns:
        PaginatedResponse with metadata
    """
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters (better for large datasets)"""

    cursor: Optional[str] = Field(default=None, description="Cursor for next page")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """Cursor-based paginated response"""

    items: List[T] = Field(description="List of items for current page")
    next_cursor: Optional[str] = Field(default=None, description="Cursor for next page")
    has_more: bool = Field(description="Whether there are more items")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "next_cursor": "eyJpZCI6MTAwfQ==",
                "has_more": True,
            }
        }

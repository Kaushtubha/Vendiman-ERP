"""
app/utils/pagination.py — Pagination Utilities

WHY centralized pagination utilities:
    Every list endpoint needs LIMIT/OFFSET calculation and consistent
    query parameter parsing. Centralizing prevents magic numbers and
    ensures consistent behavior across all 20+ list endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PageResult:
    """
    Typed container for paginated query results.

    Passed between repository and service layers — richer than a plain tuple,
    but lighter than a Pydantic model (no serialization overhead at this layer).
    """

    items: list
    total: int
    page: int
    limit: int

    @property
    def total_pages(self) -> int:
        if self.limit <= 0:
            return 0
        return max(1, (self.total + self.limit - 1) // self.limit)

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        return self.page > 1

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit

    def to_meta(self) -> dict:
        """Convert to metadata dict for API response envelope."""
        return {
            "page": self.page,
            "limit": self.limit,
            "total": self.total,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_previous": self.has_previous,
        }

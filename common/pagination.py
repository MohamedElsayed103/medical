"""
Custom DRF pagination classes.
"""
from rest_framework.pagination import CursorPagination, PageNumberPagination


class StandardResultsPagination(PageNumberPagination):
    """Default page-number pagination for list endpoints."""

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


class CursorResultsPagination(CursorPagination):
    """Cursor-based pagination for real-time feeds (e.g., notifications)."""

    page_size = 25
    ordering = "-created_at"
    cursor_query_param = "cursor"

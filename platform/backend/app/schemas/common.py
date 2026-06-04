"""Shared Pydantic schemas used across all API responses."""
from typing import TypeVar, Generic, Any
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response envelope for all endpoints."""
    success: bool = True
    data: T | None = None
    message: str = ""


def ok(data: Any, message: str = "") -> dict:
    """Helper to build a success response dict."""
    return {"success": True, "data": data, "message": message}


def err(message: str, data: Any = None) -> dict:
    """Helper to build an error response dict."""
    return {"success": False, "data": data, "message": message}

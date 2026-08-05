"""Shared response envelope + global exception handlers.

Every API response follows:
    {"success": true,  "data": ..., "message": "..."}
    {"success": false, "error": "CODE", "message": "human readable"}
"""
from __future__ import annotations

from typing import Any

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def envelope(data: Any = None, message: str | None = None) -> dict:
    return {"success": True, "data": data, "message": message}


def error_envelope(error: str, message: str, ) -> dict:
    return {"success": False, "error": error, "message": message}


class AppError(Exception):
    """Raise inside a route/service to produce a well-formed error envelope.

    Example: raise AppError("NOT_FOUND", "Job xyz does not exist", 404)
    """

    def __init__(self, error: str, message: str, status_code: int = 400):
        self.error = error
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def register_exception_handlers(app) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=error_envelope(exc.error, exc.message),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        error_code = _status_to_error_code(exc.status_code)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_envelope(error_code, detail),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_envelope(
                "VALIDATION_ERROR",
                "Request validation failed.",
            )
            | {"details": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_envelope(
                "INTERNAL_SERVER_ERROR",
                "An unexpected error occurred.",
            ),
        )


def _status_to_error_code(status_code: int) -> str:
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
    }
    return mapping.get(status_code, "HTTP_ERROR")

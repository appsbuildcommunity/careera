from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Application error carrying the documented standard error response shape.

    See docs/API_REFERENCE.md -> "Standard Error Response".
    """

    def __init__(self, *, code: str, message: str, status_code: int) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)

    def to_response(self) -> dict[str, Any]:
        return {
            "error": self.code,
            "message": self.message,
            "status_code": self.status_code,
        }


def api_error(*, code: str, message: str, status_code: int) -> None:
    """Raise an :class:`AppError` with the documented error shape."""
    raise AppError(code=code, message=message, status_code=status_code)


def register_error_handler(app: FastAPI) -> None:
    """Register the :class:`AppError` handler on the FastAPI application."""

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.to_response())

"""RFC 9457 Problem Details exception handling (TASK-INF-002 stub)."""

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

PROBLEM_BASE = "https://api.ai-tool-tracker.example/problems"


def problem_response(
    *,
    status: int,
    title: str,
    detail: str | None = None,
    type_suffix: str = "error",
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    """Build a Problem Details JSON response."""
    body: dict[str, Any] = {
        "type": f"{PROBLEM_BASE}/{type_suffix}",
        "title": title,
        "status": status,
    }
    if detail is not None:
        body["detail"] = detail
    if extra:
        body.update(extra)
    return JSONResponse(status_code=status, content=body, media_type="application/problem+json")


def register_exception_handlers(app: FastAPI) -> None:
    """Register Problem Details handlers on the FastAPI app."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        _request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        type_suffix = {
            401: "unauthorized",
            403: "forbidden",
            404: "not-found",
            429: "rate-limit-exceeded",
        }.get(exc.status_code, "error")
        return problem_response(
            status=exc.status_code,
            title=detail or "Error",
            detail=detail,
            type_suffix=type_suffix,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return problem_response(
            status=422,
            title="Validation Error",
            detail="One or more fields failed validation.",
            type_suffix="validation-error",
            extra={"errors": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        _request: Request,
        _exc: Exception,
    ) -> JSONResponse:
        return problem_response(
            status=HTTP_500_INTERNAL_SERVER_ERROR,
            title="Internal Server Error",
            detail="An unexpected error occurred.",
            type_suffix="internal-error",
        )

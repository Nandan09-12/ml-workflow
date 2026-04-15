from enum import StrEnum
import uuid

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.responses import error_envelope


class ErrorCode(StrEnum):
    BAD_REQUEST = "BAD_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    ACCOUNT_NOT_APPROVED = "ACCOUNT_NOT_APPROVED"
    ADMIN_ONLY = "ADMIN_ONLY"
    SUBMISSION_ALREADY_EXISTS = "SUBMISSION_ALREADY_EXISTS"
    INVALID_GRID_MATH = "INVALID_GRID_MATH"
    VERSION_CONFLICT = "VERSION_CONFLICT"
    INVALID_ACCOUNT_STATE = "INVALID_ACCOUNT_STATE"
    PENDING_GRIDS_MUST_BE_ZERO = "PENDING_GRIDS_MUST_BE_ZERO"
    SUBMISSION_ALREADY_COMPLETED = "SUBMISSION_ALREADY_COMPLETED"
    SUBMISSION_NOT_COMPLETED = "SUBMISSION_NOT_COMPLETED"
    NOT_OWNER = "NOT_OWNER"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"


class AppError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        status_code: int = 400,
        details: object | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", uuid.uuid4().hex)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_envelope(
            code=exc.code.value,
            message=exc.message,
            details=exc.details,
            request_id=_request_id(request),
        ),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code_map = {
        400: ErrorCode.BAD_REQUEST,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.CONFLICT,
        422: ErrorCode.VALIDATION_ERROR,
        501: ErrorCode.NOT_IMPLEMENTED,
    }
    code = code_map.get(exc.status_code, ErrorCode.INTERNAL_SERVER_ERROR)
    detail = exc.detail
    if isinstance(detail, str):
        message = detail
        details = None
    else:
        message = "Request failed."
        details = detail
    return JSONResponse(
        status_code=exc.status_code,
        content=error_envelope(
            code=code.value,
            message=message,
            details=details,
            request_id=_request_id(request),
        ),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_envelope(
            code=ErrorCode.VALIDATION_ERROR.value,
            message="Request validation failed.",
            details=exc.errors(),
            request_id=_request_id(request),
        ),
    )


async def unhandled_exception_handler(request: Request, _: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=error_envelope(
            code=ErrorCode.INTERNAL_SERVER_ERROR.value,
            message="Internal server error.",
            details=None,
            request_id=_request_id(request),
        ),
    )

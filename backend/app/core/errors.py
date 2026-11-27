from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

AUTH_ERROR_METRIC_MAP = {
    "INVALID_CREDENTIALS": "login_failed",
    "RATE_LIMITED": "rate_limited",
    "FORBIDDEN": "forbidden",
    "UNAUTHENTICATED": "unauthenticated",
    "INVALID_RESET": "invalid_reset",
    "INVALID_CURRENT_PASSWORD": "invalid_current_password",
}


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


def _error_response(request: Request, status: int, code: str, message: str) -> JSONResponse:
    from app.core.observability import active_metrics, current_correlation_id

    metric_code = AUTH_ERROR_METRIC_MAP.get(code)
    if metric_code is not None:
        active_metrics(request.app).record_auth_event(metric_code)
    cid = current_correlation_id()
    body = {"code": code, "message": message}
    if status >= 500:
        body["correlation_id"] = cid
    return JSONResponse(
        {"error": body},
        status_code=status,
        headers={"X-Correlation-ID": cid},
    )


def register_handlers(app):
    @app.exception_handler(ApiError)
    async def api_error(request: Request, error: ApiError):
        return _error_response(request, error.status, error.code, error.message)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, __: RequestValidationError):
        # Validation input can contain passwords; never reflect it to the caller.
        return _error_response(request, 422, "VALIDATION_ERROR", "Sprawdź parametry żądania")

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, __: SQLAlchemyError):
        return _error_response(request, 503, "DATABASE_UNAVAILABLE", "Baza jest niedostępna")

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException):
        return _error_response(
            request, error.status_code, "HTTP_ERROR", "Żądanie nie może być obsłużone"
        )

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


def register_handlers(app):
    @app.exception_handler(ApiError)
    async def api_error(_: Request, error: ApiError):
        return JSONResponse(
            {"error": {"code": error.code, "message": error.message}},
            status_code=error.status,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, __: RequestValidationError):
        # Validation input can contain passwords; never reflect it to the caller.
        return JSONResponse(
            {"error": {"code": "VALIDATION_ERROR", "message": "Sprawdź parametry żądania"}},
            status_code=422,
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_error(_: Request, __: SQLAlchemyError):
        return JSONResponse(
            {"error": {"code": "DATABASE_UNAVAILABLE", "message": "Baza jest niedostępna"}},
            status_code=503,
        )

    @app.exception_handler(HTTPException)
    async def http_error(_: Request, error: HTTPException):
        return JSONResponse(
            {"error": {"code": "HTTP_ERROR", "message": "Żądanie nie może być obsłużone"}},
            status_code=error.status_code,
        )

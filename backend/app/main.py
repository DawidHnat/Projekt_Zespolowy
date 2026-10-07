from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings, get_settings
from app.db.session import make_engine
from app.modules.analytics.router import router as analytics_router
from app.modules.fleet.router import router as fleet_router
from app.modules.trips.router import router as trips_router


def create_app(settings: Settings | None = None, engine: Engine | None = None) -> FastAPI:
    settings = settings or get_settings()
    application = FastAPI(
        title="Fleet-Flow API",
        version="0.1.0",
        description=(
            "Local development foundation. Reads one explicit source without demo fallback."
        ),
    )
    application.state.settings = settings
    application.state.engine = engine if engine is not None else make_engine(settings.database_url)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "PATCH"],
        allow_headers=["Content-Type"],
    )

    @application.exception_handler(SQLAlchemyError)
    def database_error(request: Request, exception: SQLAlchemyError) -> JSONResponse:
        # Database exceptions can include connection credentials; never return them.
        return JSONResponse(status_code=503, content={"detail": "Database unavailable."})

    @application.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/ready", tags=["system"])
    def ready() -> dict[str, str]:
        with application.state.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready"}

    application.include_router(fleet_router, prefix="/api/v1")
    application.include_router(trips_router, prefix="/api/v1")
    application.include_router(analytics_router, prefix="/api/v1")
    return application


app = create_app()

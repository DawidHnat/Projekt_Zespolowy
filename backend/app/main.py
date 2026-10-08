import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import WebfleetSettings, load_environment
from app.core.database import make_engine, make_sessions
from app.core.errors import register_handlers
from app.core.settings import Settings
from app.modules.auth.router import router as auth_router
from app.modules.fleet.router import router as fleet_router
from app.modules.fleet.sync import sync_worker


def create_app(settings: Settings | None = None, *, engine=None) -> FastAPI:
    settings = settings or Settings.from_environment()
    engine = engine or make_engine(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        worker = None
        if settings.sync_enabled:
            webfleet = WebfleetSettings.from_environment(load_environment())
            worker = asyncio.create_task(
                sync_worker(engine, webfleet, settings.sync_interval_seconds)
            )
        try:
            yield
        finally:
            if worker:
                worker.cancel()
                with suppress(asyncio.CancelledError):
                    await worker
            engine.dispose()

    app = FastAPI(title="Fleet-Flow", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.sessions = make_sessions(engine)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type"],
    )
    register_handlers(app)
    app.include_router(auth_router)
    app.include_router(fleet_router)

    @app.middleware("http")
    async def private_responses(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/api/health/live")
    def live():
        return {"status": "ok"}

    @app.get("/api/health/ready")
    def ready():
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return JSONResponse({"status": "unavailable"}, status_code=503)
        return {"status": "ok"}

    return app

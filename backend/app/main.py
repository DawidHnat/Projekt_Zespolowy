import asyncio
import time
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import WebfleetSettings, load_environment
from app.core.database import make_engine, make_sessions
from app.core.errors import register_handlers
from app.core.observability import (
    CORRELATION_HEADER,
    MetricsRegistry,
    bind_correlation_id,
    bind_metrics,
    log_http_server_error,
    route_template,
)
from app.core.observability import router as observability_router
from app.core.settings import Settings
from app.modules.analytics.router import router as analytics_router
from app.modules.auth.profile import router as profile_router
from app.modules.auth.reset import router as reset_router
from app.modules.auth.router import router as auth_router
from app.modules.drivers.access_logs import protect_driver_access_logs
from app.modules.drivers.router import router as drivers_router
from app.modules.fleet.documents import PrivateAttachmentStore, UnconfiguredMalwareScanner
from app.modules.fleet.router import router as fleet_router
from app.modules.fleet.sync import sync_worker
from app.modules.preferences.router import router as preferences_router
from app.modules.trips.router import router as trips_router


def create_app(settings: Settings | None = None, *, engine=None) -> FastAPI:
    settings = settings or Settings.from_environment()
    engine = engine or make_engine(settings)
    metrics = MetricsRegistry()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        worker = None
        if settings.sync_enabled:
            webfleet = WebfleetSettings.from_environment(load_environment())
            app.state.webfleet_settings = webfleet
            worker = asyncio.create_task(
                sync_worker(
                    engine,
                    webfleet,
                    settings.sync_interval_seconds,
                    stale_seconds=settings.stale_seconds,
                    metrics=metrics,
                )
            )
        try:
            yield
        finally:
            if worker:
                worker.cancel()
                with suppress(asyncio.CancelledError):
                    await worker
            engine.dispose()

    app = FastAPI(
        title="Fleet-Flow",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.local_api_docs else None,
        redoc_url="/redoc" if settings.local_api_docs else None,
        openapi_url="/openapi.json" if settings.local_api_docs else None,
        swagger_ui_oauth2_redirect_url="/docs/oauth2-redirect" if settings.local_api_docs else None,
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.sessions = make_sessions(engine)
    app.state.webfleet_settings = None
    app.state.attachment_store = PrivateAttachmentStore(settings.upload_storage_dir)
    app.state.malware_scanner = UnconfiguredMalwareScanner()
    app.state.metrics = metrics
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
        allow_headers=["Content-Type", "X-Upload-Filename", CORRELATION_HEADER],
        expose_headers=[CORRELATION_HEADER],
    )
    register_handlers(app)
    app.include_router(auth_router)
    protect_driver_access_logs()
    app.include_router(drivers_router)
    app.include_router(reset_router)
    app.include_router(profile_router)
    app.include_router(fleet_router)
    app.include_router(analytics_router)
    app.include_router(trips_router)
    app.include_router(preferences_router)
    app.include_router(observability_router)

    @app.middleware("http")
    async def private_responses(request: Request, call_next):
        started = time.perf_counter()
        with (
            bind_correlation_id(request.headers.get(CORRELATION_HEADER)) as cid,
            bind_metrics(metrics),
        ):
            request.state.correlation_id = cid
            try:
                response = await call_next(request)
            except Exception:
                duration_ms = (time.perf_counter() - started) * 1000.0
                matched = route_template(request)
                metrics.record_http(request.method, matched, 500, duration_ms)
                log_http_server_error(request.method, matched, 500, cid)
                return JSONResponse(
                    {
                        "error": {
                            "code": "INTERNAL_ERROR",
                            "message": "Wystąpił błąd serwera",
                            "correlation_id": cid,
                        }
                    },
                    status_code=500,
                    headers={
                        CORRELATION_HEADER: cid,
                        "Cache-Control": "no-store",
                        "X-Content-Type-Options": "nosniff",
                    },
                )
            duration_ms = (time.perf_counter() - started) * 1000.0
            matched = route_template(request)
            metrics.record_http(request.method, matched, response.status_code, duration_ms)
            if response.status_code >= 500:
                log_http_server_error(request.method, matched, response.status_code, cid)
            response.headers[CORRELATION_HEADER] = cid
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

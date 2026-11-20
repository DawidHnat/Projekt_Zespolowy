"""Redact driver query strings at the Uvicorn access logger."""

import logging


class DriverQueryFilter(logging.Filter):
    def filter(self, event: logging.LogRecord) -> bool:
        args = event.args
        if not isinstance(args, tuple) or len(args) != 5 or not isinstance(args[2], str):
            return True
        path, _, _ = args[2].partition("?")
        if path == "/api/v1/drivers" or path.startswith("/api/v1/drivers/"):
            event.args = (*args[:2], path, *args[3:])
        return True


def protect_driver_access_logs() -> None:
    access = logging.getLogger("uvicorn.access")
    if not any(isinstance(item, DriverQueryFilter) for item in access.filters):
        access.addFilter(DriverQueryFilter())

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session


def make_engine(database_url: str) -> Engine:
    options = (
        {"connect_args": {"check_same_thread": False}} if database_url.startswith("sqlite") else {}
    )
    return create_engine(database_url, pool_pre_ping=True, **options)


def get_session(request: Request) -> Iterator[Session]:
    with Session(request.app.state.engine) as session:
        yield session

from collections.abc import Generator

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.settings import Settings


def make_engine(settings: Settings):
    return create_engine(settings.database_url, pool_pre_ping=True, echo=False)


def get_session(request: Request) -> Generator[Session]:
    with request.app.state.sessions() as session:
        yield session


def make_sessions(engine):
    return sessionmaker(engine, expire_on_commit=False)

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


def _engine_options(url: str) -> dict:
    if url.startswith("sqlite"):
        path = url.removeprefix("sqlite:///")
        if path and path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True, "pool_size": 5, "max_overflow": 10}


settings = get_settings()
engine = create_engine(settings.database_url, **_engine_options(settings.database_url))
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

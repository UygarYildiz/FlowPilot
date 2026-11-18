from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from flowpilot.config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().database_url)


@contextmanager
def session_scope(engine: Engine | None = None) -> Iterator[Session]:
    """Bir iş birimi: başarılıysa commit, hata olursa rollback."""
    factory = sessionmaker(bind=engine or get_engine(), expire_on_commit=False)
    with factory() as session, session.begin():
        yield session

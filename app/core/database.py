from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# Stable naming convention keeps generated constraint names migration-friendly.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    metadata = metadata


_engine = None
_session_local = None


def _get_session_factory():
    global _engine, _session_local
    if _session_local is None:
        _engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        _session_local = async_sessionmaker(
            bind=_engine, class_=AsyncSession, expire_on_commit=False
        )
    return _session_local


async def get_db_session():
    session_factory = _get_session_factory()
    async with session_factory() as session:
        yield session

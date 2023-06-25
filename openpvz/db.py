from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker, AsyncSession
from consts import DB_CONNECTION_STRING


_engine = create_async_engine(DB_CONNECTION_STRING)
SessionMaker = async_sessionmaker(_engine)


def get_engine() -> AsyncEngine:
    return _engine


async def begin() -> AsyncSession:
    return await SessionMaker.begin()

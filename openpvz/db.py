from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker, AsyncSession
import os
import logging


_logger = logging.getLogger(__name__)


def db_connection_string():
    database = os.getenv('DB_NAME')
    if database is None:
        raise Exception("Please provide 'DB_NAME'")
    user = os.getenv('DB_USER')
    if user is None:
        raise Exception("Please provide 'DB_USER'")
    password = os.getenv('DB_PASSWORD')
    if password is None:
        raise Exception("Please provide 'DB_PASSWORD'")
    host = os.getenv('DB_HOST', 'localhost')
    # host = 'localhost'
    port = os.getenv('DB_PORT', 5432)
    connection_string = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"
    print(connection_string)
    return connection_string


DB_CONNECTION_STRING = db_connection_string()
_engine = create_async_engine(DB_CONNECTION_STRING)
SessionMaker = async_sessionmaker(_engine)


def get_engine() -> AsyncEngine:
    return _engine


def begin() -> AsyncSession:
    return SessionMaker.begin()

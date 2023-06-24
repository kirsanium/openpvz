from sqlalchemy.engine import create_engine, Engine
from consts import DB_CONNECTION_STRING


_engine = create_engine(DB_CONNECTION_STRING)


def get_engine() -> Engine:
    return _engine


def begin():
    return _engine.begin()

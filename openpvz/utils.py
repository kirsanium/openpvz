from pydantic import BaseModel
from typing import List, TypeVar, Callable


T = TypeVar("T")


def first(li: List[T], rule: Callable[[T], bool] | None = None) -> T | None:
    for item in li:
        if rule is None:
            return item
        if rule is not None and rule(item):
            return item


class Location(BaseModel):
    latitude: float
    longitude: float

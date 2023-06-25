from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2 import func, Geography
from openpvz.models import User, UserRole, Office, WorkingHours
from utils import Location
from typing import List


def create_user(user: User, session: AsyncSession) -> User:
    session.add(user)
    return user


def create_office(
    name: str,
    location: Location,
    working_hours: List[WorkingHours],
    session: AsyncSession
) -> Office:
    office = Office(
        name=name,
        location = func.ST_Point(location.longitude, location.latitude),
        working_hours=working_hours
    )
    session.add(office)
    return office


async def get_user(id: int, session: AsyncSession) -> User:
    return await session.get(User, id)


def update_role(user: User, role: UserRole):
    user.role = role


async def get_closest_office(location: Location, session: AsyncSession) -> Office:
    max_distance = 100 # METERS OR DEGEREES??
    target_point = f'POINT({location.longitude} {location.latitude})'
    offices = await session.execute(
        select(Office).order_by(func.ST_DWithin(Office.location, target_point, max_distance)))
    return offices.one_or_none()

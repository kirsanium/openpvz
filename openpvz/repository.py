from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
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
    owner: User,
    session: AsyncSession
) -> Office:
    office = Office(
        name=name,
        location=func.ST_Point(location.latitude, location.longitude),
        working_hours=working_hours,
        owner_id=owner.id
    )
    session.add(office)
    return office


async def get_user(id: int, session: AsyncSession) -> User | None:
    return await session.get(User, id)


async def get_office(id: int, session: AsyncSession) -> Office | None:
    return await session.get(Office, id)


async def get_user_by_chat_id(chat_id: int, session: AsyncSession) -> User | None:
    result = await session.execute(select(User).where(User.chat_id == chat_id))
    return result.scalar_one_or_none()


def update_role(user: User, role: UserRole):
    user.role = role


async def get_closest_office(location: Location, session: AsyncSession) -> Office | None:
    max_distance = 100  # meters
    offices = await session.execute(
        select(Office)
        .where(func.ST_DWithin(
            Office.location, func.ST_Point(location.latitude, location.longitude), max_distance) == True)
        .order_by(func.ST_Distance(Office.location, func.ST_Point(location.latitude, location.longitude))))
    all_offices = offices.scalars().all()
    return all_offices[0] if len(offices) > 0 else None

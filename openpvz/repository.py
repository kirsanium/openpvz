from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from openpvz.models import User, UserRole, Office, WorkingHours, Notification
from openpvz.utils import Location
from openpvz.consts import OfficeStatus, NotificationCodes
from typing import List, Tuple
from datetime import datetime, timedelta
import pytz
from openpvz.time_utils import tz_today, date_to_tz_datetime


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


async def all_offices_with_working_hours(session: AsyncSession) -> List[Office]:
    result = await session.execute(select(Office).options(joinedload(Office.working_hours)))
    return result.unique().scalars().all()


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
    all_offices = list(offices.scalars().all())
    return all_offices[0] if len(all_offices) > 0 else None


def office_doors_event(office: Office, office_status: OfficeStatus, user_id: int | None, session: AsyncSession):
    match office_status:
        case OfficeStatus.CLOSING:
            code = NotificationCodes.office_closed
        case OfficeStatus.OPENING:
            code = NotificationCodes.office_opened
        case _:
            raise Exception(f"Unknown office status: {office_status}")
    session.add(Notification(
        code=code,
        office_id=office.id,
        source_user_id=user_id
    ))


async def check_not_open_notification_today(office: Office, session: AsyncSession) -> bool:
    return await already_notified(office, NotificationCodes.office_not_opened_late, session)


async def check_not_closed_notification_today(office: Office, session: AsyncSession) -> bool:
    return await already_notified(office, NotificationCodes.office_not_closed_late, session)


async def already_notified(
    office: Office,
    code: NotificationCodes,
    session: AsyncSession
) -> bool:
    start_time, end_time = _get_utc_date_border(pytz.timezone(office.timezone))
    result = await session.execute(
        select(Notification)
            .where(Notification.office_id == office.id)
            .where(Notification.code == code)
            .where(Notification.created_at >= start_time)
            .where(Notification.created_at < end_time))
    return result.first() is not None


def _get_utc_date_border(timezone: pytz.BaseTzInfo) -> Tuple[datetime, datetime]:
    today = tz_today(timezone)
    today_datetime = date_to_tz_datetime(today, timezone)
    start_time = today_datetime.astimezone(pytz.utc)
    end_time = start_time + timedelta(days=1)
    return (start_time, end_time)

from openpvz.context import BotContext
from openpvz import db
from openpvz import repository
from openpvz.utils import first
from openpvz.time_utils import tz_now, tz_today
from openpvz.models import Office, User, Notification
from openpvz.consts import NotificationCodes
import openpvz.strings as s
from datetime import timedelta, datetime
from sqlalchemy.ext.asyncio import AsyncSession
import telegram


async def check_for_being_late(context: BotContext):
    async with db.begin() as session:
        offices = await repository.all_offices_with_working_hours(session)
        for office in offices:
            today = tz_today(office.timezone)
            weekday = today.isoweekday()
            hours_today = first(office.working_hours, lambda w: w.day_of_week == weekday)
            now = tz_now(office.timezone)
            tz = now.tzinfo

            late_for_open_time = datetime.combine(today, hours_today.opening_time, tz) + timedelta(minutes=15)
            late_for_close_time = datetime.combine(today, hours_today.closing_time, tz) + timedelta(minutes=15)
            operator_late_for_open = now > late_for_open_time and now <= late_for_open_time + timedelta(minutes=15)
            operator_late_for_close = now > late_for_close_time and now <= late_for_close_time + timedelta(minutes=15)

            if operator_late_for_close and not office.is_open:
                continue

            if operator_late_for_open and office.is_open:
                continue

            if operator_late_for_open:
                already_notified_not_open = await repository.check_not_open_notification_today(office, session)
                if not already_notified_not_open:
                    await _notify_not_opened_late(office, context, session)
                    continue

            if operator_late_for_close:
                already_notified_not_closed = await repository.check_not_closed_notification_today(office, session)
                if not already_notified_not_closed:
                    await _notify_not_closed_late(office, context, session)
                    continue


async def _notify_not_opened_late(office: Office, context: BotContext, session: AsyncSession):
    owner: User = await office.awaitable_attrs.owner
    session.add(Notification(
        code=NotificationCodes.office_not_opened_late,
        office_id=office.id
    ))
    try:
        await context.bot.send_message(chat_id=owner.chat_id, text=f"{office.name}: {s.OFFICE_NOT_OPEN_INTIME}")
    except telegram.error.Forbidden:
        pass


async def _notify_not_closed_late(office: Office, context: BotContext, session: AsyncSession):
    owner: User = await office.awaitable_attrs.owner
    session.add(Notification(
        code=NotificationCodes.office_not_closed_late,
        office_id=office.id
    ))
    try:
        await context.bot.send_message(chat_id=owner.chat_id, text=f"{office.name}: {s.OFFICE_NOT_CLOSED_INTIME}")
    except telegram.error.Forbidden:
        pass
    
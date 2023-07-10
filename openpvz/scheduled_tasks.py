from openpvz.context import BotContext
from openpvz import db
from openpvz import repository
from openpvz.utils import first
from openpvz.time_utils import tz_now, tz_today
from openpvz.models import Office, User, Notification
from openpvz.consts import NotificationCodes
import openpvz.strings as s
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession


async def check_for_being_late(context: BotContext):
    async with db.begin() as session:
        offices = await repository.all_offices_with_working_hours(session)
        for office in offices:
            weekday = tz_today(office.timezone).isoweekday()
            hours_today = first(office.working_hours, lambda w: w.day_of_week == weekday)
            now = tz_now(office.timezone)

            late_for_open_time = hours_today.opening_time - timedelta(minutes=30)
            late_for_close_time = hours_today.closing_time + timedelta(minutes=30)
            operator_late_for_open = now > late_for_open_time and now <= late_for_close_time
            operator_late_for_close = now > late_for_close_time

            if operator_late_for_close and not office.is_open:
                continue

            if operator_late_for_open and office.is_open:
                continue

            if operator_late_for_open:
                already_notified_not_open = repository.check_not_open_notification_today(session)
                if not already_notified_not_open:
                    await _notify_not_opened_late(office, context, session)
                    continue

            if operator_late_for_close:
                already_notified_not_closed = repository.check_not_closed_notification_today(session)
                if not already_notified_not_closed:
                    await _notify_not_closed_late(office, context, session)
                    continue


async def _notify_not_opened_late(office: Office, context: BotContext, session: AsyncSession):
    owner: User = await office.awaitable_attrs.owner
    session.add(Notification(
        code=NotificationCodes.office_not_opened_late,
        office_id=office.id
    ))
    context.bot.send_message(chat_id=owner.chat_id, text=f"{office.name}: {s.OFFICE_NOT_OPEN_INTIME}")


async def _notify_not_closed_late(office: Office, context: BotContext, session: AsyncSession):
    owner: User = await office.awaitable_attrs.owner
    session.add(Notification(
        code=NotificationCodes.office_not_closed_late,
        office_id=office.id
    ))
    context.bot.send_message(chat_id=owner.chat_id, text=f"{office.name}: {s.OFFICE_NOT_CLOSED_INTIME}")
    
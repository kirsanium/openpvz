import tempfile
from models import Office, User
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from repository import get_report_notifications
from datetime import datetime, timedelta
from telegram import Update
from context import BotContext
from io import TextIOWrapper
from keyboards import main_menu
from logging import getLogger


_logger = getLogger(__name__)


async def create_and_send_watches_report(office: Office, update: Update, context: BotContext):
    to = datetime.utcnow()
    since = to - timedelta(days=30)
    with tempfile.TemporaryFile("r+", prefix=f'{office.name}{to.strftime("%Y%m%d")}', suffix=".csv") as fpw:
        await create_report(fpw, office, since, to, context.session)
        _logger.info("Report created")
        fpw.seek(0)
        await context.bot.send_document(update.effective_chat.id, fpw, reply_markup=main_menu(context.user.role))
        _logger.info("Document sent")


async def create_report(file: TextIOWrapper, office: Office, since: datetime, to: datetime, session: AsyncSession):
    owner = await office.awaitable_attrs.owner
    employees: List[User] = list(await owner.awaitable_attrs.employees)
    notifications = list(await get_report_notifications(office, to, since, session))
    d = since
    dates: List[datetime] = []
    while d <= to:
        dates.append(d.date())
        d += timedelta(days=1)
    header = ','.join(['Дата', *list(map(lambda e: e.name, employees))])
    slot_dict = {e.id: i + 1 for i, e in enumerate(employees)}
    file.write(header)
    for d in dates:
        d_notifications = list(filter(lambda n: n.created_at.date() == d, notifications))
        row = [d.strftime("%m.%d"), *["" for _ in range(len(employees))]]
        for n in d_notifications:
            slot = slot_dict[n.source_user_id]
            row[slot] = 1 if row[slot] == "" else row[slot] + 1
        file.write(','.join(row))

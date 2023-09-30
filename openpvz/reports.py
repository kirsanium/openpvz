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
from utils import first
from openpyxl import Workbook
import csv
import uuid
import os


_logger = getLogger(__name__)


async def create_and_send_watches_report(office: Office, update: Update, context: BotContext):
    to = datetime.utcnow()
    since = to - timedelta(days=30)
    prefix = f'{office.name}{to.strftime("%Y%m%d")}'
    xlsx_path = str(uuid.uuid4())
    with tempfile.TemporaryFile("r+", prefix=prefix, suffix=".csv", encoding='utf-8') as fcsv:
        await create_report(fcsv, office, since, to, context.session)
        _logger.info("Report created")
        fcsv.seek(0)
        wb = Workbook()
        ws = wb.active
        for row in csv.reader(fcsv):
            ws.append(row)
        wb.save(xlsx_path)
    try:
        with open(xlsx_path, 'r', encoding='utf-8') as fxlsx:
            await context.bot.send_document(
                update.effective_chat.id,
                fxlsx,
                filename=f'{prefix}.csv',
                reply_markup=main_menu(context.user.role)
            )
            _logger.info("Document sent")
    finally:
        try:
            os.remove(xlsx_path)
        except Exception():
            pass


async def create_report(file: TextIOWrapper, office: Office, since: datetime, to: datetime, session: AsyncSession):
    owner = await office.awaitable_attrs.owner
    employees: List[User] = list(await owner.awaitable_attrs.employees)
    notifications = list(await get_report_notifications(office, since, to, session))
    d = since
    dates: List[datetime] = []
    while d <= to:
        dates.append(d.date())
        d += timedelta(days=1)

    header = ','.join(['Дата', *list(map(lambda d: d.strftime("%m.%d"), dates))])
    file.write(f"{header}\n")

    rows = {e.id: {d.strftime("%m.%d"): 0 for d in dates} for e in employees}
    for n in notifications:
        rows[n.source_user_id][n.created_at.strftime("%m.%d")] += 1 #TODO timezone
    
    keys_to_delete = []
    for key, _row in list(rows.items()):
        if not any(list(_row.values())):
            keys_to_delete.append(key)
    for k in keys_to_delete:
        del rows[k]
    
    for key, _row in list(rows.items()):
        row = [first(employees, lambda e: e.id == key).name, *list(map(lambda v: str(v) if v > 0 else "", list(_row.values())))]
        file.write(f"{','.join(row)}\n")

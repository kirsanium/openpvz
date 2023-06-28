from telegram.ext import ContextTypes, Application
from telegram import Update
import db
from openpvz.models import User, WorkingHours
from openpvz.consts import OfficeStatus
from openpvz import repository
from openpvz.utils import Location
import functools
from sqlalchemy.ext.asyncio import AsyncSession


USER_ROLE = "USER_ROLE"
USER_OWNER_ID = "USER_OWNER"
OFFICE_STATUS = "OFFICE_STATUS"
LOCATION = "LOCATION"
WORKING_HOURS = "WORKING_HOURS"


class BotContext(ContextTypes.DEFAULT_TYPE):
    def __init__(self, application, chat_id=None, user_id=None):
        super().__init__(application, chat_id, user_id)
        self._current_user: User | None = None
        self._current_session: AsyncSession | None = None

    def set_user_role(self, role: str):
        self.user_data[USER_ROLE] = role

    def unset_user_role(self):
        del self.user_data[USER_ROLE]

    def get_user_role(self) -> str | None:
        return self.user_data.get(USER_ROLE)

    def set_user_owner_id(self, owner_id: int):
        self.user_data[USER_OWNER_ID] = owner_id

    def unset_user_owner_id(self):
        del self.user_data[USER_OWNER_ID]

    def get_user_owner_id(self) -> int | None:
        return self.user_data.get(USER_OWNER_ID)

    def set_office_status(self, office_status: OfficeStatus):
        self.user_data[OFFICE_STATUS] = office_status

    def unset_office_status(self):
        del self.user_data[OFFICE_STATUS]

    def get_office_status(self) -> OfficeStatus | None:
        return self.user_data.get(OFFICE_STATUS)

    def set_location(self, location: Location):
        self.user_data[LOCATION] = location

    def unset_location(self):
        del self.user_data[LOCATION]

    def get_location(self) -> Location | None:
        return self.user_data.get(LOCATION)

    def set_working_hours(self, working_hours: WorkingHours):
        self.user_data[LOCATION] = working_hours

    def unset_working_hours(self):
        del self.user_data[LOCATION]

    def get_working_hours(self) -> WorkingHours | None:
        return self.user_data.get(LOCATION)

    @property
    def user(self) -> User | None:
        return self._current_user

    @user.setter
    def user(self, value: User) -> None:
        self._current_user = value

    @property
    def session(self) -> User | None:
        return self._current_session

    @session.setter
    def session(self, value: User) -> None:
        self._current_session = value


async def _fetch_current_user(update: Update, context: BotContext, session: AsyncSession):
    context._current_user = await repository.get_user_by_chat_id(update.effective_chat.id, session)


def with_session(func):
    @functools.wraps(func)
    async def wrapped(update: Update, context: BotContext):
        async with db.begin() as session:
            await _fetch_current_user(update, context, session)
            context._current_session = session
            return await func(update, context)
    return wrapped

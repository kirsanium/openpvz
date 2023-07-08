from telegram.ext import ContextTypes
from telegram import Update
import db
from openpvz.models import User, WorkingHours
from openpvz.consts import OfficeStatus
from openpvz import repository
from openpvz.utils import Location
import functools
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List


USER_ROLE = "USER_ROLE"
USER_OWNER_ID = "USER_OWNER"
OFFICE_STATUS = "OFFICE_STATUS"
LOCATION = "LOCATION"
WORKING_HOURS = "WORKING_HOURS"
CURRENT_LIST = "CURRENT_LIST"
LIST_PAGE = "LIST_PAGE"
CURRENT_SIZE = "CURRENT_SIZE"
CHOSEN_ID = "CHOSEN_ID"


class BotContext(ContextTypes.DEFAULT_TYPE):
    def __init__(self, application, chat_id=None, user_id=None):
        super().__init__(application, chat_id, user_id)
        self._current_user: User | None = None
        self._current_session: AsyncSession | None = None

    @property
    def user(self) -> User | None:
        return self._current_user

    @user.setter
    def user(self, value: User) -> None:
        self._current_user = value

    @property
    def session(self) -> AsyncSession | None:
        return self._current_session

    @session.setter
    def session(self, value: AsyncSession) -> None:
        self._current_session = value

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
        self.user_data[LOCATION] = (location.latitude, location.longitude)

    def unset_location(self):
        del self.user_data[LOCATION]

    def get_location(self) -> Location | None:
        latitude, longitude = self.user_data.get(LOCATION)
        return Location(latitude=latitude, longitude=longitude)

    def set_working_hours(self, working_hours: List[WorkingHours]):
        self.user_data[WORKING_HOURS] = working_hours

    def unset_working_hours(self):
        del self.user_data[WORKING_HOURS]

    def get_working_hours(self) -> List[WorkingHours] | None:
        return self.user_data.get(WORKING_HOURS)

    def set_current_page(self, page: int):
        self.user_data[LIST_PAGE] = page

    def unset_current_page(self):
        del self.user_data[LIST_PAGE]

    def get_current_page(self) -> int | None:
        return self.user_data.get(LIST_PAGE)

    def set_current_list(self, _list: List[str]):
        self.user_data[CURRENT_LIST] = _list.copy()

    def unset_current_list(self):
        del self.user_data[CURRENT_LIST]

    def get_current_list(self) -> List[str] | None:
        return self.user_data.get(CURRENT_LIST)

    def set_current_size(self, size: int):
        self.user_data[CURRENT_SIZE] = size

    def unset_current_size(self):
        del self.user_data[CURRENT_SIZE]

    def get_current_size(self) -> int | None:
        return self.user_data.get(CURRENT_SIZE)

    def set_chosen_id(self, id: int):
        self.user_data[CHOSEN_ID] = id

    def unset_chosen_id(self):
        del self.user_data[CHOSEN_ID]

    def get_chosen_id(self) -> int | None:
        return self.user_data.get(CHOSEN_ID)
    
    def unset_all(self):
        unset_func = [
            self.unset_user_role,
            self.unset_user_owner_id,
            self.unset_office_status,
            self.unset_location,
            self.unset_working_hours,
            self.unset_current_page,
            self.unset_current_list,
            self.unset_current_size,
            self.unset_chosen_id,
        ]
        for f in unset_func:
            self.__unset_wo_exc(f)
    
    def __unset_wo_exc(self, func):
        try:
            func(self)
        except KeyError:
            pass


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

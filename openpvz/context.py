from typing import Any
from telegram.ext import ContextTypes, Application
from telegram import Update
import db
from models import User
from consts import OfficeStatus
import repository
import asyncio
from utils import Location


USER_ROLE = "USER_ROLE"
USER_OWNER_ID = "USER_OWNER"
OFFICE_STATUS = "OFFICE_STATUS"
LOCATION = "LOCATION"


class BotContext(ContextTypes.DEFAULT_TYPE):
    def __init__(self, application, chat_id = None, user_id = None):
        super().__init__(application, chat_id, user_id)
        self._current_user: User | None = None

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
    
    @property
    def user(self) -> User | None:
        return self._current_user
    
    @user.setter
    def user(self, value: User) -> None:
        self._current_user = value
    
    @classmethod
    def from_update(cls, update: Update, application: Application) -> 'BotContext':
        context = super().from_update(update, application)

        if context.user_data and isinstance(update, Update):
            asyncio.run(_fetch_current_user(update, context))

        return context
    

async def _fetch_current_user(update: Update, context: 'BotContext') -> User:
    async with db.begin() as session:
        context._current_user = await repository.get_user(update.effective_chat.id, session)

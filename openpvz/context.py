from typing import Any
from telegram.ext import ContextTypes, Application
from telegram import Update
import db
from models import User
from consts import OfficeStatus


USER_ROLE = "USER_ROLE"
USER_OWNER = "USER_OWNER"
OFFICE_STATUS = "OFFICE_STATUS"


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

    def set_user_owner(self, owner: int):
        self.user_data[USER_OWNER] = owner
    
    def unset_user_owner(self):
        del self.user_data[USER_OWNER]
    
    def get_user_owner(self) -> int | None:
        return self.user_data.get(USER_OWNER)
    
    def set_office_status(self, office_status: OfficeStatus):
        self.user_data[OFFICE_STATUS] = office_status
    
    def unset_office_status(self):
        del self.user_data[OFFICE_STATUS]
    
    def get_office_status(self) -> OfficeStatus | None:
        return self.user_data.get(OFFICE_STATUS)
    
    @property
    def user(self) -> User | None:
        return self._current_user
    
    @user.setter
    def user(self, value: User) -> None:
        self._current_user = value
    
    @classmethod
    def from_update(cls, update: object, application: Application) -> "BotContext":
        context = super().from_update(update, application)

        if context.user_data and isinstance(update, Update):
            with db.begin():
                context._current_user = Repository.get_user(update.effective_chat.id)

        return context

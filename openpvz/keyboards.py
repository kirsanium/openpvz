from telegram import ReplyKeyboardMarkup
import strings as s
from openpvz.models import UserRole


def main_menu(role: UserRole) -> ReplyKeyboardMarkup:
    match role:
        case UserRole.SUPEROWNER | UserRole.OWNER:
            return ReplyKeyboardMarkup([
                    [s.ADD_OFFICE, s.ADD_OPERATOR],
                    # [s.OFFICES_SETTINGS, s.DELETE_OPERATOR]
                ], resize_keyboard=True
            )
        case UserRole.MANAGER:
            return ReplyKeyboardMarkup([
                    [s.ADD_OPERATOR, s.DELETE_OPERATOR]
                ], resize_keyboard=True
            )
        case UserRole.OPERATOR:
            return ReplyKeyboardMarkup([
                    [s.OPEN_OFFICE, s.CLOSE_OFFICE]
                ], resize_keyboard=True
            )
        case _:
            raise Exception("Unknown user role")

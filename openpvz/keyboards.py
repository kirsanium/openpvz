from telegram import ReplyKeyboardMarkup
import strings as s
from openpvz.models import UserRole
from typing import TypeVar, Iterable


T = TypeVar("T")


PREV_PAGE_BUTTON = '⬅️'
NEXT_PAGE_BUTTON = '➡️'


def _default_keyboard(*args, **kwargs) -> ReplyKeyboardMarkup:
    # request_contact=True disables sending of a message?
    return ReplyKeyboardMarkup(*args, **kwargs, resize_keyboard=True, one_time_keyboard=True)


def main_menu(role: UserRole) -> ReplyKeyboardMarkup:
    match role:
        case UserRole.SUPEROWNER | UserRole.OWNER:
            return _default_keyboard([
                [s.ADD_OFFICE, s.ADD_OPERATOR],
                [s.DELETE_OPERATOR]
                # [s.OFFICES_SETTINGS, s.DELETE_OPERATOR]
            ])
        case UserRole.MANAGER:
            return _default_keyboard([
                [s.ADD_OFFICE, s.ADD_OPERATOR],
            ])
        case UserRole.OPERATOR:
            return _default_keyboard([
                [s.OPEN_OFFICE, s.CLOSE_OFFICE],
            ])
        case _:
            raise Exception("Unknown user role")


def paged_list(button_titles: Iterable[str], page: int, size: int) -> ReplyKeyboardMarkup:
    max_page = (len(button_titles) - 1) // size
    if page > max_page:
        page = max_page

    if max_page == 0:
        lower_row = []
    elif page == 0:
        lower_row = [NEXT_PAGE_BUTTON]
    elif page < max_page:
        lower_row = [PREV_PAGE_BUTTON, NEXT_PAGE_BUTTON]
    elif page == max_page:
        lower_row = [PREV_PAGE_BUTTON]
    
    first_title_i = page * size
    last_title_i = (page + 1) * size
    if last_title_i > len(button_titles):
        last_title_i = len(button_titles)
    keyboard = [[title] for title in button_titles[first_title_i:last_title_i]]
    if len(lower_row) > 0:
        keyboard.append(lower_row)
    return _default_keyboard(keyboard)


def yes_no() -> ReplyKeyboardMarkup:
    return _default_keyboard([[s.YES, s.NO]])

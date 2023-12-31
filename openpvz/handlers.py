from telegram import Update, error
import strings as s
from openpvz.consts import BotState, OfficeStatus
import openpvz.keyboards as k
from openpvz.utils import Location, first
from context import BotContext, with_session
from openpvz.sender import reply
from openpvz.models import UserRole, User, WorkingHours, Office
from openpvz import repository
from openpvz.auth import create_link, parse_token
from datetime import time, timedelta, datetime
from typing import List
from openpvz.time_utils import tz_now, tz_today
from logging import getLogger
from openpvz.exceptions import HandlerException, FormatException
from tz_service import get_timezone
from reports import create_and_send_watches_report


_logger = getLogger(__name__)


@with_session
async def start(update: Update, context: BotContext) -> BotState:
    if context.args is not None and len(context.args) > 0:
        return await _start_with_token(update, context)

    return await _start_logged_in(update, context)


async def _start_with_token(update: Update, context: BotContext) -> BotState:
    token = context.args[0]
    role, owner_id, expired = parse_token(token)
    if role is None:
        await reply(
            update, context,
            text=s.INVALID_TOKEN
        )
        return BotState.END
    if expired:
        await reply(
            update, context,
            text=s.TOKEN_EXPIRED,
        )
        return BotState.END

    if owner_id != 0:
        owner = await repository.get_user(owner_id, context.session)
        if owner is None:
            await reply(
                update, context,
                text=s.INVALID_TOKEN
            )
            return BotState.END

    user = await repository.get_user_by_chat_id(update.effective_chat.id, context.session)
    if user is not None:
        if user.role == UserRole.SUPEROWNER or user.role == UserRole.OWNER or user.id == owner_id:
            return await _start_logged_in(update, context)
        old_owner_id = user.owner_id
        repository.update_role(user, role)
        repository.update_owner_id(user, owner_id)
        await reply(
            update, context,
            text=s.YOUR_ROLE_NOW + f' {role.title()}',
        )
        if old_owner_id != owner_id:
            await reply(
                update, context,
                text=s.YOUR_OWNER_NOW,
            )
        return await _start_logged_in(update, context)

    context.set_user_role(role)
    if owner_id == 0:
        owner_id = None
    context.set_user_owner_id(owner_id)
    await reply(update, context, text=s.ASK_FOR_NAME)
    return BotState.ASKING_FOR_NAME


@with_session
async def handle_name(update: Update, context: BotContext) -> BotState:
    name = update.message.text.strip()
    role = context.get_user_role()
    owner_id = context.get_user_owner_id()
    user = repository.create_user(User(
        chat_id=update.effective_chat.id,
        name=name,
        role=role,
        owner_id=owner_id
    ), context.session)
    context.user = user
    context.unset_user_role()
    context.unset_user_owner_id()
    return await _start_logged_in(update, context)


async def _start_logged_in(update: Update, context: BotContext) -> BotState:
    if context.user is None:
        await reply(update, context, text='You have to log in.')
        return BotState.END

    await reply(update, context, text=s.CHOOSE_ACTION, reply_markup=k.main_menu(context.user.role))
    return BotState.MAIN_MENU


@with_session
async def open_office(update: Update, context: BotContext) -> BotState:
    context.set_office_status(OfficeStatus.OPENING)
    return await ask_for_current_geo(update, context)


@with_session
async def close_office(update: Update, context: BotContext) -> BotState:
    context.set_office_status(OfficeStatus.CLOSING)
    return await ask_for_current_geo(update, context)


@with_session
async def ask_for_current_geo(update: Update, context: BotContext) -> BotState:
    await reply(update, context, text=s.SEND_YOUR_GEO)
    return BotState.OPERATOR_GEO


@with_session
async def handle_current_geo(update: Update, context: BotContext) -> BotState:
    location = update.message.location
    if location is None or location.live_period is None:
        return await ask_for_current_geo(update, context)
    office = await repository.get_closest_office(location, context.user.owner_id, context.session)
    if office is not None:
        office_status = context.get_office_status()
        if office_status == OfficeStatus.OPENING and not office.is_open:
            repository.office_doors_event(office, office_status, context.user.id, context.session)
            reply_text = _get_office_text(office, s.OFFICE_OPENED)
            if await _owner_notification_needed(office, office_status):
                notification_text = _get_office_text(office, s.OFFICE_OPENED_NOTIFICATION)
                await _notify_owner(context, text=notification_text)
            office.is_open = True
        elif office_status == OfficeStatus.OPENING and office.is_open:
            reply_text = _get_office_text(office, s.OFFICE_ALREADY_OPENED)
        elif office_status == OfficeStatus.CLOSING and office.is_open:
            office.is_open = False
            repository.office_doors_event(office, office_status, context.user.id, context.session)
            reply_text = _get_office_text(office, s.OFFICE_CLOSED)
            if await _owner_notification_needed(office, office_status):
                notification_text = _get_office_text(office, s.OFFICE_CLOSED_NOTIFICATION)
                await _notify_owner(context, text=notification_text)
        elif office_status == OfficeStatus.CLOSING and not office.is_open:
            reply_text = _get_office_text(office, s.OFFICE_ALREADY_CLOSED)
        else:
            raise HandlerException(f"Unknown office status: {office_status}")
        await reply(update, context, text=reply_text, reply_markup=k.main_menu(context.user.role))
    else:
        await reply(update, context, text=s.OUT_OF_RANGE, reply_markup=k.main_menu(context.user.role))
    context.unset_office_status()
    return BotState.MAIN_MENU


def _get_office_text(office: Office, text: str) -> str:
    return f"{office.name}: {text}"


async def _owner_notification_needed(office: Office, office_status: OfficeStatus) -> bool:
    now = tz_now(office.timezone)
    today = tz_today(office.timezone)
    weekday = now.isoweekday()
    working_hours: List[WorkingHours] = await office.awaitable_attrs.working_hours
    today_wh = first(working_hours, lambda w: w.day_of_week == weekday)
    if today_wh is None:
        _logger.warn(f"Missing WorkingHours: weekday = '{weekday}', office = '{office.id}'")
        return False
    opening_time = datetime.combine(today, today_wh.opening_time)
    opened_late = now.replace(tzinfo=None) - opening_time > timedelta(minutes=15)
    if office_status == OfficeStatus.OPENING and opened_late:
        return True
    closing_time = datetime.combine(today, today_wh.closing_time)
    closed_early = closing_time - timedelta(minutes=10) > now.replace(tzinfo=None)
    closed_late = closing_time + timedelta(minutes=15) < now.replace(tzinfo=None)
    if office_status == OfficeStatus.CLOSING and (closed_early or closed_late):
        return True
    return False


async def _notify_owner(context: BotContext, *args, **kwargs):
    chat_id = (await context.user.awaitable_attrs.owner).chat_id
    try:
        await context.bot.send_message(chat_id=chat_id, *args, **kwargs)
    except error.Forbidden:
        _logger.warn(f"Owner blocked the bot, chat_id: {chat_id}")


@with_session
async def add_office(update: Update, context: BotContext) -> BotState:
    await reply(update, context, text=s.SEND_OFFICE_GEO)
    return BotState.OWNER_OFFICE_GEO


@with_session
async def handle_office_geo(update: Update, context: BotContext) -> BotState:
    location = update.message.location
    if location is None:
        return await add_office(update, context)
    context.set_location(Location(latitude=location.latitude, longitude=location.longitude))
    await reply(update, context, text=s.ENTER_WORKING_HOURS)
    return BotState.OWNER_OFFICE_WORKING_HOURS


@with_session
async def handle_working_hours(update: Update, context: BotContext) -> BotState:
    try:
        working_hours = _parse_working_hours(update.message.text)
    except ValueError:
        await reply(update, context, text=s.ENTER_WORKING_HOURS)
        return BotState.OWNER_OFFICE_WORKING_HOURS
    except FormatException:
        await reply(update, context, text=s.CLOSING_LESS_THAN_OPENING)
        return BotState.OWNER_OFFICE_WORKING_HOURS

    context.set_working_hours(working_hours)
    await reply(update, context, text=s.ENTER_OFFICE_NAME)
    return BotState.OWNER_OFFICE_NAME


def _parse_working_hours(text: str) -> List[WorkingHours]:
    # HH:MM-HH:MM every day for now
    # TODO: more options
    text = text.strip()
    opening = time(hour=int(text[0:2]), minute=int(text[3:5]))
    closing = time(hour=int(text[6:8]), minute=int(text[9:11]))
    if closing <= opening:
        raise FormatException(f"Closing ({closing}) can't be less than opening ({opening})")
    return [WorkingHours(
        opening_time=opening,
        closing_time=closing,
        day_of_week=d
    ) for d in range(1, 8)]


@with_session
async def handle_office_name(update: Update, context: BotContext) -> BotState:
    name = update.message.text.strip()
    location = context.get_location()
    working_hours = context.get_working_hours()
    timezone = get_timezone(location.longitude, location.latitude)
    repository.create_office(name, location, timezone, working_hours, context.user, context.session)
    context.unset_location()
    context.unset_working_hours()
    await reply(update, context, text=s.OFFICE_CREATED, reply_markup=k.main_menu(context.user.role))
    return BotState.MAIN_MENU


@with_session
async def add_operator(update: Update, context: BotContext) -> BotState:
    return await _add_user(update, context, UserRole.OPERATOR)


@with_session
async def add_owner(update: Update, context: BotContext) -> BotState:
    return await _add_user(update, context, UserRole.OWNER)


async def _add_user(update: Update, context: BotContext, role: UserRole) -> BotState:
    link = create_link(context.user, role)
    await reply(update, context, text=s.SEND_THIS_LINK + f' {link}', reply_markup=k.main_menu(context.user.role))
    return BotState.MAIN_MENU


@with_session
async def delete_operator(update: Update, context: BotContext) -> BotState:
    employees = await context.user.awaitable_attrs.employees
    operators = list(filter(lambda e: e.role == UserRole.OPERATOR, employees))
    if len(operators) == 0:
        await reply(update, context, text=s.NO_OPERATORS, reply_markup=k.main_menu(context.user.role))
        return BotState.MAIN_MENU
    await reply(update, context, text=s.CHOOSE_OPERATOR)
    operator_names = list(map(lambda o: o.name, operators))
    await _send_paged_list(update, context, operator_names)
    return BotState.OWNER_DELETE_OPERATOR


async def _send_paged_list(
    update: Update,
    context: BotContext,
    button_titles: List[str],
    page: int = 0,
    size: int = 5
):
    page_amount = (len(button_titles) - 1) // size + 1
    text = f"{s.PAGE} {page+1}/{page_amount}"
    await reply(update, context, text=text, reply_markup=k.paged_list(button_titles, page, size))
    context.set_current_list(button_titles)
    context.set_current_page(page)
    context.set_current_size(size)


@with_session
async def handle_delete_operator(update: Update, context: BotContext) -> BotState:
    employees = await context.user.awaitable_attrs.employees
    operators = list(filter(lambda e: e.role == UserRole.OPERATOR, employees))
    operator = first(operators, lambda e: e.name == update.message.text)
    if operator is None:
        await reply(update, context, text=s.NO_SUCH_OPERATOR)
        return await delete_operator(update, context)

    context.set_chosen_id(operator.id)
    await reply(update, context, text=f"{s.REALLY_DELETE_OPERATOR} {operator.name}?", reply_markup=k.yes_no())
    return BotState.REALLY_DELETE_OPERATOR


@with_session
async def really_delete_operator(update: Update, context: BotContext) -> BotState:
    if update.message.text == s.YES:
        user_to_delete = await repository.get_user(context.get_chosen_id(), context.session)
        await context.session.delete(user_to_delete)
        await reply(update, context, text=s.OPERATOR_DELETED, reply_markup=k.main_menu(context.user.role))
        return BotState.MAIN_MENU
    elif update.message.text == s.NO:
        return await delete_operator(update, context)
    else:
        raise HandlerException("Unknown reply")


@with_session
async def offices_settings(update: Update, context: BotContext) -> BotState:
    offices = await context.user.awaitable_attrs.offices
    if len(offices) == 0:
        await reply(update, context, text=s.NO_OFFICES, reply_markup=k.main_menu(context.user.role))
        return BotState.MAIN_MENU
    office_names = list(map(lambda o: o.name, offices))
    await _send_paged_list(update, context, office_names)
    return BotState.OWNER_OFFICES


@with_session
async def show_office_settings(update: Update, context: BotContext) -> BotState:
    offices = await context.user.awaitable_attrs.offices
    office = first(offices, lambda e: e.name == update.message.text)
    if office is None:
        await reply(update, context, text=s.NO_SUCH_OFFICE)
        return await offices_settings(update, context)

    # TODO: добавить инфу по офису
    context.set_chosen_id(office.id)
    await reply(update, context, text=s.CHOOSE_ACTION, reply_markup=k.office_actions())
    return BotState.OWNER_OFFICE_SETTINGS


@with_session
async def delete_office(update: Update, context: BotContext) -> BotState:
    office = await repository.get_office(context.get_chosen_id(), context.session)
    await reply(update, context, text=f"{s.REALLY_DELETE_OFFICE} {office.name}?", reply_markup=k.yes_no())
    return BotState.REALLY_DELETE_OFFICE


@with_session
async def watches_report(update: Update, context: BotContext) -> BotState:
    office = await repository.get_office(context.get_chosen_id(), context.session)
    await create_and_send_watches_report(office, update, context)
    return BotState.MAIN_MENU


@with_session
async def really_delete_office(update: Update, context: BotContext) -> BotState:
    if update.message.text == s.YES:
        office_to_delete = await repository.get_office(context.get_chosen_id(), context.session)
        await context.session.delete(office_to_delete)
        await reply(update, context, text=s.OFFICE_DELETED, reply_markup=k.main_menu(context.user.role))
        return BotState.MAIN_MENU
    elif update.message.text == s.NO:
        return await offices_settings(update, context)
    else:
        raise HandlerException("Unknown reply")


class PageException(HandlerException):
    pass


@with_session
async def prev_page(update: Update, context: BotContext) -> BotState:
    current_page = context.get_current_page()
    if current_page is None:
        raise PageException("You are not in a paged list")
    p_page = current_page - 1
    if p_page < 0:
        raise PageException("Page number out of bounds")
    current_list = context.get_current_list()
    size = context.get_current_size()
    await _send_paged_list(update, context, current_list, p_page, size)
    context.set_current_page(p_page)


@with_session
async def next_page(update: Update, context: BotContext) -> BotState:
    current_page = context.get_current_page()
    if current_page is None:
        raise PageException("You are not in a paged list")
    size = context.get_current_size()
    next_page = current_page + 1
    if next_page >= size:
        raise PageException("Page number out of bounds")
    current_list = context.get_current_list()
    await _send_paged_list(update, context, current_list, next_page, size)
    context.set_current_page(next_page)

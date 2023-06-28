from telegram import Update
import strings as s
from openpvz.consts import BotState, OfficeStatus
import openpvz.keyboards as k
from openpvz import db
from context import BotContext, with_user
from openpvz.sender import reply
from openpvz.models import UserRole, User, WorkingHours, Office
from openpvz import repository
from openpvz.auth import create_link, parse_token
from datetime import time
from typing import List


class HandlerException(Exception):
    pass


@with_user
async def start(update: Update, context: BotContext) -> BotState:
    if len(context.args) > 0:
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
    if expired:
        await reply(
            update, context,
            text=s.TOKEN_EXPIRED,
        )
        return

    async with db.begin() as conn:
        user = await repository.get_user(update.effective_chat.id, conn)
        if user is not None:
            repository.update_role(user, role, conn)
            await reply(
                update, context,
                text=s.YOUR_ROLE_NOW + f' {role.title()}',
            )
            return await _start_logged_in(update, context)

    context.set_user_role(role)
    if owner_id == 0:
        owner_id = None
    context.set_user_owner_id(owner_id)
    await reply(update, context, text=s.ASK_FOR_NAME)
    return BotState.ASKING_FOR_NAME


@with_user
async def handle_name(update: Update, context: BotContext) -> BotState:
    name = update.message.text.strip()
    role = context.get_user_role()
    owner_id = context.get_user_owner_id()
    async with db.begin() as session:
        user = repository.create_user(User(
            chat_id=update.effective_chat.id,
            name=name,
            role=role,
            owner_id=owner_id
        ), session)
    context.user = user
    context.unset_user_role()
    context.unset_user_owner_id()
    return await _start_logged_in(update, context)


async def _start_logged_in(update: Update, context: BotContext) -> BotState:
    if context.user is None:
        await reply(update, context, text='You have to log in.')
        return BotState.END

    await reply(update, context, text=s.WELCOME_TEXT, reply_markup=k.main_menu(context.user.role))
    return BotState.MAIN_MENU


@with_user
async def open_office(update: Update, context: BotContext) -> BotState:
    context.set_office_status(OfficeStatus.OPENING)
    return await ask_for_current_geo(update, context)


@with_user
async def close_office(update: Update, context: BotContext) -> BotState:
    context.set_office_status(OfficeStatus.CLOSING)
    return await ask_for_current_geo(update, context)


@with_user
async def ask_for_current_geo(update: Update, context: BotContext) -> BotState:
    await reply(update, context, text=s.SEND_YOUR_GEO)
    return BotState.OPERATOR_GEO


@with_user
async def handle_current_geo(update: Update, context: BotContext) -> BotState:
    location = update.message.location
    if location is None or location.live_period is None:
        return await ask_for_current_geo(update, context)
    async with db.begin() as session:
        office = await repository.get_closest_office(location, session)
        if office is not None:
            office_status = context.get_office_status()
            if office_status == OfficeStatus.OPENING and not office.is_open:
                text = s.OFFICE_OPENED
                notification_text = _get_office_text(s.OFFICE_OPENED_NOTIFICATION)
                office.is_open = True
            elif office_status == OfficeStatus.OPENING and office.is_open:
                text = s.OFFICE_ALREADY_OPENED
                notification_text = None
            elif office_status == OfficeStatus.CLOSING and office.is_open:
                office.is_open = False
                text = _get_office_text(s.OFFICE_CLOSED)
                notification_text = s.OFFICE_CLOSED_NOTIFICATION
            elif office_status == OfficeStatus.CLOSING and not office.is_open:
                text = s.OFFICE_ALREADY_CLOSED
                notification_text = None
            else:
                raise HandlerException(f"Unknown office status: {office_status}")
            reply(update, context, text=text, reply_markup=k.main_menu())
            if notification_text is not None:
                _notify_owner(context, text=notification_text)
        else:
            reply(update, context, text=s.OUT_OF_RANGE, reply_markup=k.main_menu())
    context.unset_office_status()
    return BotState.MAIN_MENU


def _get_office_text(office: Office, text: str) -> str:
    return f"{office.name}: {text}"


@with_user
async def add_office(update: Update, context: BotContext) -> BotState:
    reply(update, context, text=s.SEND_OFFICE_GEO)
    return BotState.OWNER_OFFICE_GEO


@with_user
async def handle_office_geo(update: Update, context: BotContext) -> BotState:
    location = update.message.location
    if location is None:
        return await add_office(update, context)
    context.set_location(location.latitude, location.longitude)
    reply(update, context, text=s.ENTER_WORKING_HOURS)
    return BotState.OWNER_OFFICE_WORKING_HOURS


@with_user
async def handle_working_hours(update: Update, context: BotContext) -> BotState:
    try:
        working_hours = _parse_working_hours(update.message.text)
    except Exception:
        reply(update, context, text=s.ENTER_WORKING_HOURS)
        return BotState.OWNER_OFFICE_WORKING_HOURS

    context.set_working_hours(working_hours)
    return BotState.OWNER_OFFICE_NAME


def _parse_working_hours(text: str) -> List[WorkingHours]:
    # 09:00-21:00 every day
    # TODO: more options
    text = text.strip()
    opening = time(hour=int(text[0:2]), minute=int(text[3:5]))
    closing = time(hour=int(text[6:8]), minute=int(text[9:11]))
    return [WorkingHours(
        opening_time=opening,
        closing_time=closing,
        day_of_week=d
    ) for d in range(7)]


@with_user
async def handle_office_name(update: Update, context: BotContext) -> BotState:
    name = update.message.text.strip()
    location = context.get_location()
    working_hours = context.get_working_hours()
    async with db.begin() as session:
        repository.create_office(name, location, working_hours, session)
    context.unset_location()
    context.unset_working_hours()
    reply(update, context, text=s.OFFICE_CREATED, reply_markup=k.main_menu())
    return BotState.MAIN_MENU


@with_user
async def add_operator(update: Update, context: BotContext) -> BotState:
    link = create_link(context.user.id, UserRole.OPERATOR)
    reply(update, context, text=s.SEND_THIS_LINK + f' {link}', reply_markup=k.main_menu())
    return BotState.MAIN_MENU


@with_user
async def delete_operator(update: Update, context: BotContext) -> BotState:
    # TODO
    ...


@with_user
async def handle_delete_operator(update: Update, context: BotContext) -> BotState:
    # TODO
    ...


@with_user
async def offices_settings(update: Update, context: BotContext) -> BotState:
    # TODO
    ...


@with_user
async def show_office_settings(update: Update, context: BotContext) -> BotState:
    # TODO
    ...


@with_user
async def delete_office(update: Update, context: BotContext) -> BotState:
    # TODO
    ...


def _notify_owner(context: BotContext, *args, **kwargs):
    context.bot.send_message(chat_id=context.user.owner.chat_id, *args, **kwargs)

from telegram import Update
import strings as s
from openpvz.consts import BotState, OfficeStatus
import openpvz.keyboards as k
from openpvz import db
from context import BotContext
from openpvz.sender import reply
from openpvz.models import UserRole, User
from openpvz import repository
from openpvz.auth import create_link, parse_token


async def start(update: Update, context: BotContext) -> BotState:
    if len(context.args) > 0:
        return await start_with_token(update, context)

    return await start_logged_in(update, context)


async def start_with_token(update: Update, context: BotContext) -> BotState:
    token = context.args[0]
    role, owner_id, expired = parse_token(token)
    if expired:
        await reply(
            update, context,
            text=s.TOKEN_EXPIRED,
        )
        return
        
    user = context.user
    if user is not None:
        async with db.begin() as conn:
            repository.update_role(user, role, conn)
        await reply(
            update, context,
            text=s.YOUR_ROLE_NOW,
        )
        return await start_logged_in(update, context)
        
    context.set_user_role(role)
    context.set_user_owner_id(owner_id)
    await reply(update, context, text=s.ASK_FOR_NAME)
    return BotState.ASKING_FOR_NAME


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
    return await start_logged_in(update, context)


async def start_logged_in(update: Update, context: BotContext) -> BotState:
    await reply(update, context, text=s.WELCOME_TEXT, reply_markup=k.main_menu(context.user.role))
    return BotState.MAIN_MENU


async def open_office(update: Update, context: BotContext) -> BotState:
    context.set_office_status(OfficeStatus.OPENING)
    return await ask_for_current_geo(update, context)


async def close_office(update: Update, context: BotContext) -> BotState:
    context.set_office_status(OfficeStatus.CLOSING)
    return await ask_for_current_geo(update, context)


async def ask_for_current_geo(update: Update, context: BotContext) -> BotState:
    await reply(update, context, text=s.SEND_YOUR_GEO)
    return BotState.OPERATOR_GEO


async def handle_current_geo(update: Update, context: BotContext) -> BotState:
    location = update.message.location
    if location is None or location.live_period is None:
        return await ask_for_current_geo(update, context)
    async with db.begin() as session:
        office = repository.get_closest_office(location, session)
    if office is not None:
        reply(update, context, text=s.OFFICE_OPENED, reply_markup=k.main_menu())
        _notify_owner(context, text=s.OFFICE_OPENED_NOTIFICATION)
    else:
        reply(update, context, text=s.OUT_OF_RANGE, reply_markup=k.main_menu())
    context.unset_office_status()
    return BotState.MAIN_MENU


async def add_office(update: Update, context: BotContext) -> BotState:
    reply(update, context, text=s.SEND_OFFICE_GEO)
    return BotState.OWNER_OFFICE_GEO


async def handle_office_geo(update: Update, context: BotContext) -> BotState:
    location = update.message.location
    if location is None:
        return await add_office(update, context)
    context.set_location(location.latitude, location.longitude)
    reply(update, context, text=s.ENTER_WORKING_HOURS)
    return BotState.OWNER_OFFICE_WORKING_HOURS


async def handle_working_hours(update: Update, context: BotContext) -> BotState:
    working_hours = parse_working_hours(update.message.text)
    context.set_working_hours(working_hours)
    return BotState.OWNER_OFFICE_NAME


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


async def add_operator(update: Update, context: BotContext) -> BotState:
    link = create_link(context.user.id, UserRole.OPERATOR)
    reply(update, context, text=s.SEND_THIS_LINK + f' {link}', reply_markup=k.main_menu())
    return BotState.MAIN_MENU


async def delete_operator(update: Update, context: BotContext) -> BotState:
    ...


async def handle_delete_operator(update: Update, context: BotContext) -> BotState:
    ...


async def offices_settings(update: Update, context: BotContext) -> BotState:
    ...


async def show_office_settings(update: Update, context: BotContext) -> BotState:
    ...


async def delete_office(update: Update, context: BotContext) -> BotState:
    ...


def _notify_owner(context: BotContext, *args, **kwargs):
    context.bot.send_message(chat_id=context.user.owner.chat_id, *args, **kwargs)

from telegram import Update
import strings as s
from consts import BotState, OfficeStatus
import keyboards as k
import db
from context import BotContext
from sender import reply
from models import UserRole


async def start(update: Update, context: BotContext) -> BotState:
    if len(context.args) > 0:
        return await start_with_token(update, context)

    return await start_logged_in(update, context)


async def start_with_token(update: Update, context: BotContext) -> BotState:
    token = context.args[0]
    role, owner, expired = parse_secret_code(token)
    if expired:
        await reply(
            update, context,
            text=s.TOKEN_EXPIRED,
        )
        return
        
    user = context.user
    if user is not None:
        with db.begin() as conn:
            Repository.update_role(user, role, conn)
        await reply(
            update, context,
            text=s.YOUR_ROLE_NOW,
        )
        return await start_logged_in(update, context)
        
    context.set_user_role(role)
    context.set_user_owner(owner)
    await reply(update, context, text=s.ASK_FOR_NAME)
    return BotState.ASKING_FOR_NAME


async def handle_name(update: Update, context: BotContext) -> BotState:
    name = update.message.text.strip()
    role = context.get_user_role()
    owner = context.get_user_owner()
    with db.begin() as conn:
        user = Repository.create_user(
            update.effective_chat.id,
            role,
            name,
            owner,
            conn
        )
    context.user = user
    context.unset_user_role()
    context.unset_user_owner()
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
    office = get_closest_office(location.latitude, location.longitude)
    if in_range(office):
        reply(update, context, text=s.OFFICE_OPENED, reply_markup=k.main_menu())
        notify_owner(context.user, text=s.OFFICE_OPENED_NOTIFICATION)
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
    office_name = update.message.text.strip()
    office_geo = context.get_location()
    office_geo = context.get_working_hours()
    with db.begin() as conn:
        Repository.create_office(context.user, ...)
    context.unset_location()
    context.unset_working_hours()
    reply(update, context, text=s.OFFICE_CREATED, reply_markup=k.main_menu())
    return BotState.MAIN_MENU


async def add_operator(update: Update, context: BotContext) -> BotState:
    link = link_generator.create_link(context.user.chat_id, UserRole.OPERATOR)
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


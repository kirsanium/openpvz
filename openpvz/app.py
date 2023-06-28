from telegram.ext import Application, ConversationHandler, CommandHandler, MessageHandler
from telegram.ext import filters
from openpvz import handlers
from openpvz import strings
from openpvz.consts import BotState, TELEGRAM_TOKEN
# from openpvz.db import DB_CONNECTION_STRING
# from openpvz.persistence import PostgresPersistence
import logging
import sys
from context import BotContext, ContextTypes


def set_stdout_logging(log_level: int = logging.DEBUG):
    root = logging.getLogger()
    root.setLevel(log_level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(module)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)


set_stdout_logging(logging.INFO)


def run_bot():
    app: Application = Application.builder()\
        .token(TELEGRAM_TOKEN)\
        .context_types(ContextTypes(context=BotContext))\
        .build()
    # TODO: .persistence(PostgresPersistence(DB_CONNECTION_STRING))\
    main_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', handlers.start)
        ],
        states={
            BotState.ASKING_FOR_NAME: [
                MessageHandler(filters.TEXT, handlers.handle_name)
            ],
            BotState.MAIN_MENU: [
                MessageHandler(strings.OPEN_OFFICE, handlers.open_office),
                MessageHandler(strings.CLOSE_OFFICE, handlers.close_office),
                MessageHandler(strings.ADD_OFFICE, handlers.add_office),
                MessageHandler(strings.OFFICES_SETTINGS, handlers.offices_settings),
                MessageHandler(strings.ADD_OPERATOR, handlers.add_operator),
                MessageHandler(strings.DELETE_OPERATOR, handlers.delete_operator),
            ],
            BotState.OPERATOR_GEO: [
                MessageHandler(filters.LOCATION, handlers.handle_current_geo),
                MessageHandler(~filters.LOCATION, handlers.ask_for_current_geo),
            ],
            BotState.OWNER_OFFICE_GEO: [
                MessageHandler(filters.LOCATION, handlers.handle_office_geo),
            ],
            BotState.OWNER_OFFICE_WORKING_HOURS: [
                MessageHandler(filters.TEXT, handlers.handle_working_hours)
            ],
            BotState.OWNER_OFFICE_NAME: [
                MessageHandler(filters.TEXT, handlers.handle_office_name)
            ],
            BotState.OWNER_DELETE_OPERATOR: [
                MessageHandler(filters.TEXT, handlers.handle_delete_operator)
            ],
            BotState.OWNER_OFFICES: [
                MessageHandler(filters.TEXT, handlers.show_office_settings)
            ],
            BotState.OWNER_OFFICE_SETTINGS: [
                MessageHandler(strings.DELETE_OFFICE, handlers.delete_office)
            ],
        },
        fallbacks=[],
        allow_reentry=False,
    )
    app.add_handler(main_handler)
    app.run_polling()


if __name__ == '__main__':
    run_bot()

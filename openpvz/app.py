from telegram.ext import Application, ConversationHandler, CommandHandler, MessageHandler
from telegram.ext import filters, JobQueue
from openpvz import handlers
from openpvz import strings as s
from openpvz import keyboards as k
from openpvz.consts import BotState, TELEGRAM_TOKEN
from openpvz.db import db_connection_string
from openpvz.persistence import PostgresPersistence
from openpvz.scheduled_tasks import check_for_being_late
import logging
import sys
from context import BotContext, ContextTypes
from typing import List
from datetime import timedelta


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
        .persistence(PostgresPersistence(db_connection_string("postgresql"), update_interval=10))\
        .job_queue(JobQueue())\
        .build()
    to_main_handler = MessageHandler(_build_handler_regex(s.TO_MAIN_MENU), handlers.start)
    paged_list_handlers = [
        to_main_handler,
        MessageHandler(_build_handler_regex(k.PREV_PAGE_BUTTON), handlers.prev_page),
        MessageHandler(_build_handler_regex(k.NEXT_PAGE_BUTTON), handlers.next_page),
    ]
    main_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', handlers.start)
        ],
        states={
            BotState.ASKING_FOR_NAME: [
                MessageHandler(filters.TEXT, handlers.handle_name)
            ],
            BotState.MAIN_MENU: [
                MessageHandler(_build_handler_regex(s.OPEN_OFFICE), handlers.open_office),
                MessageHandler(_build_handler_regex(s.CLOSE_OFFICE), handlers.close_office),
                MessageHandler(_build_handler_regex(s.ADD_OFFICE), handlers.add_office),
                MessageHandler(_build_handler_regex(s.OFFICES_SETTINGS), handlers.offices_settings),
                MessageHandler(_build_handler_regex(s.ADD_OPERATOR), handlers.add_operator),
                MessageHandler(_build_handler_regex(s.DELETE_OPERATOR), handlers.delete_operator),
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
                *paged_list_handlers,
                MessageHandler(filters.TEXT, handlers.handle_delete_operator)
            ],
            BotState.REALLY_DELETE_OPERATOR: [
                MessageHandler(_build_handler_regex(s.YES, s.NO), handlers.really_delete_operator)
            ],
            BotState.OWNER_OFFICES: [
                *paged_list_handlers,
                MessageHandler(filters.TEXT, handlers.show_office_settings)
            ],
            BotState.OWNER_OFFICE_SETTINGS: [
                MessageHandler(_build_handler_regex(s.DELETE_OFFICE), handlers.delete_office),
                to_main_handler
            ],
            BotState.REALLY_DELETE_OFFICE: [
                MessageHandler(_build_handler_regex(s.YES, s.NO), handlers.really_delete_office)
            ],
        },
        fallbacks=[
            # TODO: обработка ошибок
        ],
        allow_reentry=True,
        persistent=True,
        name="main_handler"
    )
    app.add_handler(main_handler)
    app.job_queue.run_custom(check_for_being_late, timedelta(minutes=1))
    app.run_polling(
        allowed_updates=["message", "inline_query", "chosen_inline_result", "callback_query"]
    )


def _build_handler_regex(*options: List[str]) -> filters.Regex:
    return filters.Regex(rf"^{'|'.join(options)}$")


if __name__ == '__main__':
    run_bot()

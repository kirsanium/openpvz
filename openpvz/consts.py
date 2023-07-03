from enum import IntEnum, StrEnum, auto
import os
from telegram.ext import ConversationHandler


TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
if TELEGRAM_TOKEN is None:
    raise Exception("Please specify 'TELEGRAM_TOKEN'")

# TELEGRAM_WEBHOOK_URL = os.getenv('TELEGRAM_WEBHOOK_URL')
# if TELEGRAM_WEBHOOK_URL is None:
#     raise Exception("Please specify 'TELEGRAM_WEBHOOK_URL'")

TELEGRAM_BOT_NAME = os.getenv('TELEGRAM_BOT_NAME')
if TELEGRAM_BOT_NAME is None:
    raise Exception("Please specify 'TELEGRAM_BOT_NAME'")


class BotState(IntEnum):
    END = ConversationHandler.END
    ASKING_FOR_NAME = auto()
    MAIN_MENU = auto()
    OPERATOR_GEO = auto()
    OWNER_OFFICE_GEO = auto()
    OWNER_OFFICE_WORKING_HOURS = auto()
    OWNER_OFFICE_NAME = auto()
    OWNER_DELETE_OPERATOR = auto()
    OWNER_OFFICES = auto()
    OWNER_OFFICE_SETTINGS = auto()
    REALLY_DELETE_OPERATOR = auto()
    REALLY_DELETE_OFFICE = auto()


class OfficeStatus(StrEnum):
    CLOSING = 'closing'
    OPENING = 'opening'

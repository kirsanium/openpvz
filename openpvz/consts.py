from enum import IntEnum, StrEnum
import os


TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
if TELEGRAM_TOKEN is None:
    raise Exception("Please specify 'TELEGRAM_TOKEN'")

TELEGRAM_WEBHOOK_URL = os.getenv('TELEGRAM_WEBHOOK_URL')
if TELEGRAM_WEBHOOK_URL is None:
    raise Exception("Please specify 'TELEGRAM_WEBHOOK_URL'")

TELEGRAM_BOT_NAME = os.getenv('TELEGRAM_BOT_NAME')
if TELEGRAM_BOT_NAME is None:
    raise Exception("Please specify 'TELEGRAM_BOT_NAME'")


class BotState(IntEnum):
    ASKING_FOR_NAME = 1
    MAIN_MENU = 2
    OPERATOR_GEO = 3
    OWNER_OFFICE_GEO = 4
    OWNER_OFFICE_WORKING_HOURS = 5
    OWNER_OFFICE_NAME = 6
    OWNER_DELETE_OPERATOR = 7
    OWNER_OFFICES = 8
    OWNER_OFFICE_SETTINGS = 9


class OfficeStatus(StrEnum):
    CLOSING = 'closing'
    OPENING = 'opening'

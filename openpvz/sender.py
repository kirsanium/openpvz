from telegram import Update
from telegram.ext import CallbackContext


async def reply(update: Update, context: CallbackContext, *args, **kwargs):
    await context.bot.send_message(chat_id=update.effective_chat.id, *args, **kwargs)

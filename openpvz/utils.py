# from core.utilities.gettext import GetText
# from functools import wraps
# import core.db as db
# from consts import USER_ID
# from core.settings.repository import get_settings
# from contextlib import closing


# gettext = GetText("messages", "locale")


# def user_language(func):
#     @wraps(func)
#     def wrapped(update, context):
#         user_id = context.user_data.get(USER_ID)
#         if user_id is not None:
#             with closing(db.db_connection()) as conn:
#                 gettext.set_language(get_settings(user_id, conn).language_code)
#         result = func(update, context)
#         return result
#     return wrapped

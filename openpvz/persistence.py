import json
from logging import getLogger
from typing import Any, Dict, List, Optional, Tuple, Callable
from telegram.ext import DictPersistence
from openpvz import db
import psycopg


CDCData = Tuple[List[Tuple[str, float, Dict[str, Any]]], Dict[str, str]]


def db_connection():
    return psycopg.connect(db.db_connection_string("postgresql"))


class PersistentDbConnection:
    def __init__(self, db_connection_factory: Callable) -> None:
        self.db_connection_factory = db_connection_factory
        db_connection = db_connection_factory()
        if not callable(getattr(db_connection, 'close', None)):
            raise ValueError("This connection is a non-closable!")
        self.db_connection = db_connection

    def __del__(self):
        self.db_connection.close()

    def acquire(self):
        if self.db_connection.closed:
            self.db_connection = self.db_connection_factory()
        return self.db_connection


class PostgresPersistence(DictPersistence):
    """Using Postgresql database to make user/chat/bot data persistent across reboots.

    Args:
        url (:obj:`str`) the postgresql database url.
        on_flush (:obj:`bool`, optional): if set to :obj:`True` :class:`PostgresPersistence`
            will only update bot/chat/user data when :meth:flush is called.
        **kwargs (:obj:`dict`): Arbitrary keyword Arguments to be passed to
            the DictPersistence constructor.

    Attributes:
        store_data (:class:`PersistenceInput`): Specifies which kinds of data will be saved by this
            persistence instance.
    """

    def __init__(
        self,
        url: str,
        on_flush: bool = False,
        **kwargs: Any,
    ) -> None:
        if url is None:
            raise TypeError("You must need to provide either url or session.")

        if not url.startswith("postgresql://"):
            raise TypeError(f"{url} isn't a valid PostgreSQL database URL.")

        self._connection = PersistentDbConnection(db_connection)

        self.logger = getLogger(__name__)

        self.on_flush = on_flush
        self.logger.info("Loading persisted data...")
        with self._acquire_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT data FROM telegram_bot_persistence")
                data_ = cur.fetchone()
                data = data_[0] if data_ is not None else {}

                chat_data_json = data.get("chat_data", "")
                user_data_json = data.get("user_data", "")
                bot_data_json = data.get("bot_data", "")
                conversations_json = data.get("conversations", "{}")
                callback_data_json = data.get("callback_data_json", "")

                self.logger.info("Persisted data loaded successfully!")

                # if it is a fresh setup we'll add some placeholder data so we
                # can perform `UPDATE` operations on it, cause SQL only allows
                # `UPDATE` operations if column have some data already present inside it.
                if not data:
                    cur.execute("""
                        INSERT INTO telegram_bot_persistence (data) VALUES (%s)
                    """, ("{}",))

                super().__init__(
                    **kwargs,
                    chat_data_json=chat_data_json,
                    user_data_json=user_data_json,
                    bot_data_json=bot_data_json,
                    callback_data_json=callback_data_json,
                    conversations_json=conversations_json,
                )

    def _dump_into_json(self) -> Any:
        """Dumps data into json format for inserting in db."""

        to_dump = {
            "chat_data": self.chat_data_json,
            "user_data": self.user_data_json,
            "bot_data": self.bot_data_json,
            "conversations": self.conversations_json,
            "callback_data": self.callback_data_json,
        }
        self.logger.debug("Dumping %s", to_dump)
        return json.dumps(to_dump)

    def _update_database(self) -> None:
        self.logger.debug("Updating database...")
        with self._acquire_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE telegram_bot_persistence SET data = %s", (self._dump_into_json(),))

    async def update_conversation(
        self, name: str, key: Tuple[int, ...], new_state: Optional[object]
    ) -> None:
        """Will update the conversations for the given handler.

        Args:
            name (:obj:`str`): The handler's name.
            key (:obj:`tuple`): The key the state is changed for.
            new_state (:obj:`tuple` | :obj:`any`): The new state for the given key.
        """
        await super().update_conversation(name, key, new_state)
        if not self.on_flush:
            await self.flush()

    async def update_user_data(self, user_id: int, data: Dict) -> None:
        """Will update the user_data (if changed).
        Args:
            user_id (:obj:`int`): The user the data might have been changed for.
            data (:obj:`dict`): The :attr:`telegram.ext.Dispatcher.user_data` ``[user_id]``.
        """
        await super().update_user_data(user_id, data)
        if not self.on_flush:
            await self.flush()

    async def update_chat_data(self, chat_id: int, data: Dict) -> None:
        """Will update the chat_data (if changed).
        Args:
            chat_id (:obj:`int`): The chat the data might have been changed for.
            data (:obj:`dict`): The :attr:`telegram.ext.Dispatcher.chat_data` ``[chat_id]``.
        """
        await super().update_chat_data(chat_id, data)
        if not self.on_flush:
            await self.flush()

    async def update_bot_data(self, data: Dict) -> None:
        """Will update the bot_data (if changed).
        Args:
            data (:obj:`dict`): The :attr:`telegram.ext.Dispatcher.bot_data`.
        """
        await super().update_bot_data(data)
        if not self.on_flush:
            await self.flush()

    async def update_callback_data(self, data: CDCData) -> None:
        """Will update the callback_data (if changed).

        Args:
            data (Tuple[List[Tuple[:obj:`str`, :obj:`float`, Dict[:obj:`str`, :class:`object`]]], \
                Dict[:obj:`str`, :obj:`str`]]): The relevant data to restore
                :class:`telegram.ext.CallbackDataCache`.
        """
        await super().update_callback_data(data)
        if not self.on_flush:
            await self.flush()

    async def flush(self) -> None:
        """Will be called by :class:`telegram.ext.Updater` upon receiving a stop signal. Gives the
        persistence a chance to finish up saving or close a database connection gracefully.
        """
        self._update_database()
        if not self.on_flush:
            self.logger.debug("Context persisted!")

    def _acquire_db_connection(self):
        return self._connection.acquire()

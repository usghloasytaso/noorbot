"""
میدل‌ور ثبت و پایش خودکار کاربران و گروه‌ها در پایگاه داده
"""

import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.db.repository import GroupRepository, UserRepository

logger = logging.getLogger("middleware.tracker")


class UserTrackerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        telegram_user = None
        chat = None

        if isinstance(event, Message):
            telegram_user = event.from_user
            chat = event.chat
        elif isinstance(event, CallbackQuery):
            telegram_user = event.from_user
            chat = event.message.chat if event.message else None

        # ثبت یا به‌روزرسانی مشخصات کاربر
        if telegram_user and not telegram_user.is_bot:
            try:
                db_user = await UserRepository.upsert_user(
                    telegram_id=telegram_user.id,
                    username=telegram_user.username,
                    first_name=telegram_user.first_name,
                    last_name=telegram_user.last_name,
                    language_code=telegram_user.language_code or "fa"
                )
                data["user"] = db_user
            except Exception as e:
                logger.warning("Error tracking user %s: %s", telegram_user.id, e)
                data["user"] = User(
                    telegram_id=telegram_user.id,
                    username=telegram_user.username,
                    first_name=telegram_user.first_name,
                    last_name=telegram_user.last_name,
                    language_code=telegram_user.language_code or "fa"
                )

        # ثبت یا به‌روزرسانی گروه
        if chat and chat.type in ("group", "supergroup"):
            try:
                db_group = await GroupRepository.upsert_group(
                    chat_id=chat.id,
                    title=chat.title,
                    username=chat.username,
                    chat_type=chat.type
                )
                data["group"] = db_group
            except Exception as e:
                logger.warning("Error tracking group %s: %s", chat.id, e)
                data["group"] = Group(
                    chat_id=chat.id,
                    title=chat.title or "گروه",
                    username=chat.username,
                    chat_type=chat.type
                )

        return await handler(event, data)

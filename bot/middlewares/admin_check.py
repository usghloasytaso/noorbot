"""
میدل‌ور و فیلتر احراز دسترسی مدیران ربات
"""

from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.config import settings


class AdminFilter(BaseFilter):
    """فیلتر بررسی اینکه آیا فرستنده در فهرست ادمین‌ها قرار دارد یا خیر"""
    async def __call__(self, obj: TelegramObject) -> bool:
        user_id = None
        if isinstance(obj, Message) and obj.from_user:
            user_id = obj.from_user.id
        elif isinstance(obj, CallbackQuery) and obj.from_user:
            user_id = obj.from_user.id
        return bool(user_id and settings.is_admin(user_id))

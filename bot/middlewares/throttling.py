"""
میدل‌ور مقابله با اسپم و کنترل نرخ درخواست‌ها (Rate Limiting / Throttling)
"""

import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.config import settings


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, burst_limit: int = 5, time_window: float = 3.0):
        super().__init__()
        self.burst_limit = burst_limit
        self.time_window = time_window
        self.user_history: Dict[int, list] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if user_id:
            now = time.time()
            history = self.user_history.get(user_id, [])
            # حذف درخواست‌های قدیمی‌تر از پنجره زمانی
            history = [t for t in history if now - t < self.time_window]

            if len(history) >= self.burst_limit:
                # پیام هشدار به کاربر فقط یک‌بار هنگام عبور از سقف
                if len(history) == self.burst_limit:
                    if isinstance(event, Message):
                        await event.answer("⚠️ لطفاً کمی شکیبا باشید و از ارسال متوالی پیام خودداری فرمایید.")
                    elif isinstance(event, CallbackQuery):
                        await event.answer("⚠️ لطفاً کمی صبر کنید.", show_alert=False)
                history.append(now)
                self.user_history[user_id] = history
                return None  # مسدودسازی پردازش پیام

            history.append(now)
            self.user_history[user_id] = history

        return await handler(event, data)

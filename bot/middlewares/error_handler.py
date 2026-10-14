"""
میدل‌ور مدیریت جامع خطاهای پیش‌بینی‌نشده و ثبت لاگ امن
"""

import logging
import traceback
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.db.repository import LogsRepository

logger = logging.getLogger("middleware.error")


class ErrorHandlerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as exc:
            err_msg = str(exc)
            tb = traceback.format_exc()
            logger.error("Unhandled exception in update handler: %s\n%s", err_msg, tb)

            # ثبت در گزارش‌های سیستمی پایگاه داده
            try:
                await LogsRepository.log("ERROR", "dispatcher", err_msg, {"traceback": tb[:1000]})
            except Exception:
                pass

            # ارسال بازخورد محترمانه به کاربر
            try:
                if isinstance(event, Message):
                    await event.answer("⚠️ متأسفانه در پردازش این دستور خطایی رخ داد. موضوع به تیم فنی گزارش شد.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("⚠️ خطایی رخ داد. لطفاً مجدداً تلاش کنید.", show_alert=True)
            except Exception:
                pass

            return None

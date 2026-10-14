"""
سرویس ارسال پیام همگانی امن با کنترل نرخ (Throttling) و مدیریت خطاهای تلگرام
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramNotFound, TelegramRetryAfter

from bot.db.repository import GroupRepository, LogsRepository, UserRepository

logger = logging.getLogger("service.broadcast")


class BroadcastService:
    @staticmethod
    async def broadcast_to_users(bot: Bot, text: str, reply_markup: Any = None) -> Dict[str, int]:
        users = await UserRepository.get_all_active_users()
        total = len(users)
        sent = 0
        blocked = 0
        failed = 0

        logger.info("Starting broadcast to %d users...", total)
        for user_id in users:
            try:
                await bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
                sent += 1
                # تأخیر ۰.۰۵ ثانیه‌ای جهت حفظ سقف ارسال زیر ۲۵ پیام در ثانیه
                await asyncio.sleep(0.05)
            except TelegramRetryAfter as e:
                logger.warning("Flood limit reached. Sleeping for %s seconds", e.retry_after)
                await asyncio.sleep(e.retry_after)
                try:
                    await bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
                    sent += 1
                except Exception:
                    failed += 1
            except (TelegramForbiddenError, TelegramNotFound):
                blocked += 1
            except Exception as e:
                logger.warning("Failed to send broadcast to user %s: %s", user_id, e)
                failed += 1

        await LogsRepository.log("INFO", "broadcast", f"Broadcast finished: {sent}/{total} sent, {blocked} blocked, {failed} failed")
        return {"total": total, "sent": sent, "blocked": blocked, "failed": failed}

    @staticmethod
    async def broadcast_to_groups(bot: Bot, text: str, reply_markup: Any = None) -> Dict[str, int]:
        groups = await GroupRepository.get_all_active_groups()
        total = len(groups)
        sent = 0
        failed = 0

        logger.info("Starting broadcast to %d groups...", total)
        for chat_id in groups:
            try:
                await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
                sent += 1
                await asyncio.sleep(0.05)
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
                try:
                    await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
                    sent += 1
                except Exception:
                    failed += 1
            except Exception as e:
                logger.warning("Failed to send broadcast to group %s: %s", chat_id, e)
                failed += 1

        await LogsRepository.log("INFO", "broadcast", f"Group broadcast finished: {sent}/{total} sent, {failed} failed")
        return {"total": total, "sent": sent, "failed": failed}

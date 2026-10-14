"""
سرویس زمان‌بندی (Scheduler) جهت ارسال اعلان‌های خودکار روزانه
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from aiogram import Bot

from bot.db.base import db
from bot.services.calendar_service import CalendarService
from bot.services.quran_service import QuranService

logger = logging.getLogger("service.scheduler")


class SchedulerService:
    def __init__(self, bot: Bot):
        self.bot = bot
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("Scheduler service started successfully.")

    async def stop(self):
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduler service stopped.")

    async def _loop(self):
        while self._running:
            try:
                await self._check_and_send_notifications()
            except Exception as e:
                logger.error("Error in scheduler loop: %s", e)
            # بررسی هر ۶۰ ثانیه
            await asyncio.sleep(60)

    async def _check_and_send_notifications(self):
        now_str = datetime.now().strftime("%H:%M")

        # ۱. اعلان‌های کاربران فعال
        query_users = "SELECT telegram_id FROM users WHERE notifications_enabled = 1 AND notification_time = $1" if db.is_sqlite else "SELECT telegram_id FROM users WHERE notifications_enabled = TRUE AND notification_time = $1"
        try:
            user_rows = await db.fetch(query_users, now_str)
            if user_rows:
                today_info = CalendarService.get_today_info()
                daily_content = CalendarService.format_daily_content(today_info)
                ayah = QuranService.get_daily_ayah()
                ayah_content = QuranService.format_daily_ayah_message(ayah)
                msg_text = f"{daily_content}\n\n{ayah_content}"

                for r in user_rows:
                    try:
                        await self.bot.send_message(chat_id=r["telegram_id"], text=msg_text, parse_mode="HTML")
                        await asyncio.sleep(0.05)
                    except Exception as e:
                        logger.warning("Failed to send scheduled message to user %s: %s", r["telegram_id"], e)
        except Exception as e:
            logger.warning("Failed checking scheduled user notifications: %s", e)

        # ۲. اعلان‌های گروه‌های فعال
        query_groups = "SELECT chat_id FROM groups WHERE is_active = 1 AND allow_daily_ayah = 1 AND daily_ayah_time = $1" if db.is_sqlite else "SELECT chat_id FROM groups WHERE is_active = TRUE AND allow_daily_ayah = TRUE AND daily_ayah_time = $1"
        try:
            group_rows = await db.fetch(query_groups, now_str)
            if group_rows:
                ayah = QuranService.get_daily_ayah()
                ayah_text = QuranService.format_daily_ayah_message(ayah)
                for g in group_rows:
                    try:
                        await self.bot.send_message(chat_id=g["chat_id"], text=ayah_text, parse_mode="HTML")
                        await asyncio.sleep(0.05)
                    except Exception as e:
                        logger.warning("Failed to send scheduled ayah to group %s: %s", g["chat_id"], e)
        except Exception as e:
            logger.warning("Failed checking scheduled group notifications: %s", e)

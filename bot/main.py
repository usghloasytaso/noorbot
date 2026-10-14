"""
نقطهٔ ورود اصلی و اجرای همزمان ربات تلگرام و وب‌سرور سلامت‌سنجی Render
"""

import asyncio
import logging
import signal
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.db.base import db
from bot.handlers import get_main_router
from bot.middlewares.error_handler import ErrorHandlerMiddleware
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.middlewares.user_tracker import UserTrackerMiddleware
from bot.services.calendar_service import CalendarService
from bot.services.istikhara_service import IstikharaService
from bot.services.quran_service import QuranService
from bot.services.scheduler_service import SchedulerService
from bot.web.health import start_health_server

# تنظیم لاگر استاندارد
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("noorbot.main")


async def main():
    logger.info("Starting NoorBot engine...")
    logger.info("Environment: %s | Port: %d | Host: %s", settings.environment, settings.port, settings.host)

    # ۱. اتصال به پایگاه داده و بارگذاری کش‌ها
    await db.connect()
    IstikharaService.load_data()
    QuranService.load_data()
    CalendarService.load_data()

    # ۲. راه‌اندازی سرور وب سلامت‌سنجی (سازگار با پایش Render و UptimeRobot)
    health_runner = await start_health_server(host=settings.host, port=settings.port)

    # ۳. راه‌اندازی ربات تلگرام
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # ۴. ثبت میدل‌ورها (کنترل خطا، ثبت کاربر و مقابله با اسپم)
    dp.update.outer_middleware(ErrorHandlerMiddleware())
    dp.message.middleware(UserTrackerMiddleware())
    dp.callback_query.middleware(UserTrackerMiddleware())
    dp.message.middleware(ThrottlingMiddleware(burst_limit=settings.rate_limit_burst, time_window=settings.rate_limit_window))
    dp.callback_query.middleware(ThrottlingMiddleware(burst_limit=settings.rate_limit_burst, time_window=settings.rate_limit_window))

    # ۵. اتصال روترها
    dp.include_router(get_main_router())

    # ۶. راه‌اندازی سرویس اعلان‌های زمان‌بندی‌شده
    scheduler = SchedulerService(bot)
    await scheduler.start()

    logger.info("NoorBot setup completed. Starting long polling...")

    try:
        # حذف وب‌هوک‌های قدیمی در صورت وجود برای تضمین عملکرد صحیح polling
        try:
            await bot.delete_webhook(drop_pending_updates=True)
        except Exception as e:
            logger.warning("Could not delete webhook (possibly mock token or offline): %s", e)

        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("Shutdown signal received.")
    except Exception as e:
        logger.error("Error during bot polling: %s", e)
    finally:
        logger.info("Gracefully shutting down services...")
        await scheduler.stop()
        await health_runner.cleanup()
        await db.close()
        await bot.session.close()
        logger.info("All services shut down cleanly.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Process terminated.")

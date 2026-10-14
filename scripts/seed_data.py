"""
اسکریپت مقداردهی اولیه پایگاه داده و آماده‌سازی سیستم (Database Seeding)
"""

import asyncio
import logging
import sys
from pathlib import Path

# افزودن ریشه پروژه به مسیر پایتون
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.config import settings
from bot.db.base import db
from bot.db.repository import StatsRepository, UserRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_data")


async def seed():
    logger.info("Connecting to database: %s", settings.database_url)
    await db.connect()

    # ایجاد و به‌روزرسانی اولیه متریک‌ها
    logger.info("Initializing bot metrics...")
    stats = [
        "total_users",
        "total_groups",
        "total_istikharas",
        "total_quran_searches",
        "total_tasbih_counts"
    ]
    for s in stats:
        await StatsRepository.increment(s, 0)

    # ایجاد یک کاربر نمونه برای آزمون در صورت تمایل
    if settings.admin_ids:
        for admin_id in settings.admin_ids:
            logger.info("Ensuring admin user %s exists in database...", admin_id)
            await UserRepository.upsert_user(
                telegram_id=admin_id,
                username="admin",
                first_name="مدیر سامانه",
                last_name="",
                language_code="fa"
            )

    logger.info("Database seeding completed successfully.")
    await db.close()


if __name__ == "__main__":
    asyncio.run(seed())

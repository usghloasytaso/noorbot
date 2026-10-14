import asyncio
import os
import sys
from pathlib import Path
import pytest

# افزودن ریشه پروژه به مسیر ماژول‌های پایتون
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# تنظیم متغیرهای محیطی آزمون قبل از بارگذاری ماژول‌ها
os.environ["BOT_TOKEN"] = "123456789:ABCdefGHIjklMNOpqrSTUvwxyz"
os.environ["ADMIN_IDS"] = "111222333,444555666"
os.environ["DATABASE_URL"] = "sqlite:///test_noorbot.db"
os.environ["ENVIRONMENT"] = "testing"
os.environ["PORT"] = "8080"

from bot.config import settings
from bot.db.base import DatabaseManager, db
from bot.services.calendar_service import CalendarService
from bot.services.istikhara_service import IstikharaService
from bot.services.quran_service import QuranService


@pytest.fixture(scope="session", autouse=True)
def init_services():
    """بارگذاری اولیه‌ی داده‌های مرجع"""
    IstikharaService.load_data()
    QuranService.load_data()
    CalendarService.load_data()


@pytest.fixture(scope="function")
async def test_db():
    """ایجاد دیتابیس تمیز برای هر تست و پاکسازی پس از اتمام"""
    test_db_path = "test_noorbot.db"
    manager = DatabaseManager(f"sqlite:///{test_db_path}")
    await manager.connect()
    yield manager
    await manager.close()
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except Exception:
            pass

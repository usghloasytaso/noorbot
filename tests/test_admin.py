"""
تست‌های خودکار پنل ادمین، فیلترهای امنیتی و ارسال پیام همگانی
"""

from unittest.mock import AsyncMock, MagicMock
import pytest
from aiogram.types import Message, User as TgUser

from bot.config import settings
from bot.db.repository import StatsRepository, UserRepository
from bot.middlewares.admin_check import AdminFilter
from bot.services.broadcast_service import BroadcastService


@pytest.mark.asyncio
async def test_admin_filter():
    # ادمین‌های معتبر در conftest: 111222333, 444555666
    admin_filter = AdminFilter()

    msg_admin = MagicMock(spec=Message)
    msg_admin.from_user = MagicMock(spec=TgUser)
    msg_admin.from_user.id = 111222333
    assert await admin_filter(msg_admin) is True

    msg_regular = MagicMock(spec=Message)
    msg_regular.from_user = MagicMock(spec=TgUser)
    msg_regular.from_user.id = 999999999
    assert await admin_filter(msg_regular) is False


@pytest.mark.asyncio
async def test_stats_repository(test_db):
    await StatsRepository.increment("total_users", 5)
    await StatsRepository.increment("total_istikharas", 12)

    stats = await StatsRepository.get_all_stats()
    assert stats.get("total_users") == 5
    assert stats.get("total_istikharas") == 12


@pytest.mark.asyncio
async def test_broadcast_service_safe_execution(test_db):
    # ایجاد کاربران آزمایشی
    await UserRepository.upsert_user(1001, "u1", "کاربر ۱", "")
    await UserRepository.upsert_user(1002, "u2", "کاربر ۲", "")

    bot = MagicMock()
    bot.send_message = AsyncMock(return_value=True)

    res = await BroadcastService.broadcast_to_users(bot, "پیام آزمایشی")
    assert res["total"] >= 2
    assert res["sent"] >= 2
    assert res["failed"] == 0

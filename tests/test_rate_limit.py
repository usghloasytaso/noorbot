"""
تست‌های خودکار میدل‌ور کنترل نرخ و ضد اسپم (Rate Limiting)
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest
from aiogram.types import Message, User as TgUser

from bot.middlewares.throttling import ThrottlingMiddleware


@pytest.mark.asyncio
async def test_throttling_allows_under_limit():
    middleware = ThrottlingMiddleware(burst_limit=3, time_window=1.0)
    handler = AsyncMock(return_value="handled")

    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=TgUser)
    message.from_user.id = 123456

    # ارسال ۲ درخواست (زیر سقف ۳)
    res1 = await middleware(handler, message, {})
    res2 = await middleware(handler, message, {})

    assert res1 == "handled"
    assert res2 == "handled"
    assert handler.call_count == 2


@pytest.mark.asyncio
async def test_throttling_blocks_excessive_requests():
    middleware = ThrottlingMiddleware(burst_limit=2, time_window=0.5)
    handler = AsyncMock(return_value="handled")

    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=TgUser)
    message.from_user.id = 654321
    message.answer = AsyncMock()

    # درخواست اول و دوم مجاز
    res1 = await middleware(handler, message, {})
    res2 = await middleware(handler, message, {})
    assert res1 == "handled"
    assert res2 == "handled"

    # درخواست سوم مسدود می‌شود
    res3 = await middleware(handler, message, {})
    assert res3 is None
    assert handler.call_count == 2
    message.answer.assert_called_once()

    # پس از سپری شدن زمان پنجره، مجدداً مجاز می‌شود
    await asyncio.sleep(0.6)
    res4 = await middleware(handler, message, {})
    assert res4 == "handled"
    assert handler.call_count == 3

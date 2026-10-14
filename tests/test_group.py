"""
تست‌های خودکار مدیریت گروه‌ها، تنظیمات اختصاصی مدیران و حریم خصوصی
"""

import pytest
from bot.db.models import Group
from bot.db.repository import GroupRepository
from bot.keyboards.group_kb import get_group_settings_keyboard


@pytest.mark.asyncio
async def test_group_upsert_and_settings(test_db):
    chat_id = -1001234567890
    group = await GroupRepository.upsert_group(
        chat_id=chat_id,
        title="گروه مذهبی منتظران",
        username="montazeran_grp",
        chat_type="supergroup"
    )

    assert group.chat_id == chat_id
    assert group.title == "گروه مذهبی منتظران"
    assert group.allow_istikhara is True
    assert group.private_result_mode is True

    # به‌روزرسانی تنظیمات
    await GroupRepository.update_settings(
        chat_id=chat_id,
        allow_istikhara=False,
        private_mode=False,
        allow_daily_ayah=True
    )

    updated = await GroupRepository.get_by_id(chat_id)
    assert updated.allow_istikhara is False
    assert updated.private_result_mode is False
    assert updated.allow_daily_ayah is True


def test_group_settings_keyboard():
    group = Group(
        chat_id=-100111,
        title="تست",
        allow_istikhara=True,
        private_result_mode=True,
        allow_daily_ayah=False
    )
    kb = get_group_settings_keyboard(group)
    assert len(kb.inline_keyboard) == 4
    # بررسی نمایش متن متناظر با وضعیت‌ها
    texts = [btn.text for row in kb.inline_keyboard for btn in row]
    assert any("استخاره در گروه: ✅ فعال" in t for t in texts)
    assert any("در پی‌وی کاربر (خصوصی)" in t for t in texts)
    assert any("ارسال آیه روزانه: ❌ غیرفعال" in t for t in texts)

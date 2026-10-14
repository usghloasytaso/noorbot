"""
تست‌های خودکار مدیریت گروه‌ها، تنظیمات اختصاصی مدیران و پیام خوش‌آمدگویی هوشمند
"""

from unittest.mock import MagicMock
import pytest
from bot.db.models import Group
from bot.db.repository import GroupRepository
from bot.handlers.group import build_smart_group_welcome
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

    # غیرفعال‌سازی وضعیت گروه هنگام خروج ربات
    await GroupRepository.set_active(chat_id, False)
    deactivated = await GroupRepository.get_by_id(chat_id)
    assert deactivated.is_active is False


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
    texts = [btn.text for row in kb.inline_keyboard for btn in row]
    assert any("استخاره در گروه: ✅ فعال" in t for t in texts)
    assert any("در پی‌وی کاربر (خصوصی)" in t for t in texts)
    assert any("ارسال آیه روزانه: ❌ غیرفعال" in t for t in texts)


def test_smart_group_welcome_message():
    # ۱. حالت عضو عادی
    member_mock = MagicMock()
    member_mock.status = "member"

    text_member, kb_member = build_smart_group_welcome("گروه اهل‌بیت", member_mock, "NoorBot")
    assert "گروه اهل‌بیت" in text_member
    assert "عضو عادی" in text_member
    assert "یادآوری به مدیران محترم گروه" in text_member
    assert "/istikhara" in text_member

    # ۲. حالت مدیر (Administrator)
    admin_mock = MagicMock()
    admin_mock.status = "administrator"
    admin_mock.can_delete_messages = True
    admin_mock.can_pin_messages = True

    text_admin, kb_admin = build_smart_group_welcome("گروه نور", admin_mock, "NoorBot")
    assert "مدیر (Administrator)" in text_admin
    assert "دسترسی‌های لازم تایید شد" in text_admin
    assert "حذف پیام‌های منسوخ" in text_admin

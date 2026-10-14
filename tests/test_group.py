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


def test_user_group_keyboards():
    from bot.keyboards.group_kb import (
        get_group_marja_picker_kb,
        get_group_profile_kb,
        get_group_tafsir_picker_kb,
        get_group_tasbih_kb,
        get_user_group_istikhara_kb,
    )

    # تست کیبورد استخاره در گروه
    kb_ist = get_user_group_istikhara_kb(12345, "sistani", "nemooneh", "NoorReligious_bot")
    assert len(kb_ist.inline_keyboard) == 2
    buttons = [b.text for row in kb_ist.inline_keyboard for b in row]
    assert any("تغییر مرجع (سیستانی)" in b for b in buttons)
    assert any("تغییر تفسیر (نمونه)" in b for b in buttons)
    assert any("استخاره مجدد" in b for b in buttons)

    # تست کیبورد انتخاب مرجع
    kb_m = get_group_marja_picker_kb(12345, "khamenei")
    m_buttons = [b.text for row in kb_m.inline_keyboard for b in row]
    assert any("رهبر معظم انقلاب ✅" in b for b in m_buttons)

    # تست کیبورد انتخاب تفسیر
    kb_t = get_group_tafsir_picker_kb(12345, "al-mizan")
    t_buttons = [b.text for row in kb_t.inline_keyboard for b in row]
    assert any("تفسیر المیزان ✅" in b for b in t_buttons)

    # تست کیبورد صلوات‌شمار گروهی
    kb_salawat = get_group_tasbih_kb(14)
    s_buttons = [b.text for row in kb_salawat.inline_keyboard for b in row]
    assert any("14" in b for b in s_buttons)

    # تست کیبورد پروفایل گروه
    kb_prof = get_group_profile_kb(12345, "sistani", "nemooneh", "NoorReligious_bot")
    assert len(kb_prof.inline_keyboard) == 2


"""
کیبوردهای تنظیمات مدیریتی گروه‌ها
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.db.models import Group


def get_group_settings_keyboard(group: Group) -> InlineKeyboardMarkup:
    ist_status = "✅ فعال" if group.allow_istikhara else "❌ غیرفعال"
    mode_status = "🔒 در پی‌وی کاربر (خصوصی)" if group.private_result_mode else "👥 داخل گروه (عمومی)"
    ayah_status = "✅ فعال" if group.allow_daily_ayah else "❌ غیرفعال"

    buttons = [
        [
            InlineKeyboardButton(
                text=f"استخاره در گروه: {ist_status}",
                callback_data="grp_toggle:istikhara"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"حالت نمایش نتیجه: {mode_status}",
                callback_data="grp_toggle:priv_mode"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"ارسال آیه روزانه: {ayah_status}",
                callback_data="grp_toggle:daily_ayah"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 به‌روزرسانی تنظیمات",
                callback_data="grp_refresh"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

"""
کیبوردهای اختصاصی پنل مدیریت (Admin Panel) و تاییدیه ارسال همگانی
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_admin_panel_kb() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="📊 آمار تفصیلی سامانه", callback_data="admin:stats"),
            InlineKeyboardButton(text="🩺 وضعیت سلامت سرور", callback_data="admin:health")
        ],
        [
            InlineKeyboardButton(text="📢 ارسال پیام همگانی (کاربران)", callback_data="admin:broadcast_users"),
            InlineKeyboardButton(text="👥 ارسال پیام همگانی (گروه‌ها)", callback_data="admin:broadcast_groups")
        ],
        [
            InlineKeyboardButton(text="🔙 خروج از پنل مدیریت", callback_data="menu:main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_broadcast_confirm_kb(target: str = "users") -> InlineKeyboardMarkup:
    """تاییدیه صریح قبل از ارسال پیام همگانی جهت جلوگیری از ارسال ناخواسته"""
    buttons = [
        [
            InlineKeyboardButton(text="✅ بله، ارسال به تمام گیرندگان", callback_data=f"bcast_confirm:{target}")
        ],
        [
            InlineKeyboardButton(text="❌ انصراف و لغو ارسال", callback_data="bcast_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

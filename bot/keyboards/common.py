"""
کیبوردهای عمومی، منوی اصلی و دکمه‌های ناوبری
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """منوی اصلی پایین صفحه به زبان فارسی"""
    kb = [
        [KeyboardButton(text="📖 استخاره با قرآن"), KeyboardButton(text="✨ آیه و محتوای روز")],
        [KeyboardButton(text="📿 تسبیح‌شمار تعاملی"), KeyboardButton(text="🕌 اوقات شرعی")],
        [KeyboardButton(text="🔍 جستجوی قرآن"), KeyboardButton(text="🤲 ادعیه و زیارات")],
        [KeyboardButton(text="📜 احکام و مراجع"), KeyboardButton(text="⚙️ تنظیمات من")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, is_persistent=True)


def get_main_inline_menu() -> InlineKeyboardMarkup:
    """منوی شیشه‌ای اصلی"""
    buttons = [
        [
            InlineKeyboardButton(text="📖 استخاره با قرآن", callback_data="menu:istikhara"),
            InlineKeyboardButton(text="✨ آیه روز", callback_data="menu:daily_ayah")
        ],
        [
            InlineKeyboardButton(text="📿 تسبیح‌شمار هوشمند", callback_data="menu:tasbih"),
            InlineKeyboardButton(text="🕌 اوقات شرعی", callback_data="menu:prayer")
        ],
        [
            InlineKeyboardButton(text="🔍 جستجو در قرآن", callback_data="menu:quran_search"),
            InlineKeyboardButton(text="🗓 مناسبت‌ها و تقویم", callback_data="menu:calendar")
        ],
        [
            InlineKeyboardButton(text="📜 احکام شرعی", callback_data="menu:ahkam"),
            InlineKeyboardButton(text="⚙️ تنظیمات من", callback_data="menu:settings")
        ],
        [
            InlineKeyboardButton(text="ℹ️ راهنما و درباره ربات", callback_data="menu:help")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_button(target: str = "main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data=f"menu:{target}")]]
    )

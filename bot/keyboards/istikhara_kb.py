"""
کیبوردهای اختصاصی بخش استخاره، انتخاب مرجع، تفسیر و علاقه‌مندی‌ها
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_istikhara_menu_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="✨ نیت کردم، استخاره بگیر", callback_data="istikhara:do")],
        [
            InlineKeyboardButton(text="📜 شروط و آداب استخاره", callback_data="istikhara:adab"),
            InlineKeyboardButton(text="🕒 تاریخچه استخاره‌ها", callback_data="istikhara:history")
        ],
        [
            InlineKeyboardButton(text="⚖️ انتخاب مرجع تقلید", callback_data="settings:marja"),
            InlineKeyboardButton(text="📚 انتخاب تفسیر", callback_data="settings:tafsir")
        ],
        [InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="menu:main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_istikhara_result_kb(record_id: int, is_favorite: bool = False) -> InlineKeyboardMarkup:
    fav_text = "⭐ ذخیره در علاقه‌مندی‌ها" if not is_favorite else "🌟 در علاقه‌مندی‌ها ذخیره شد"
    buttons = [
        [InlineKeyboardButton(text=fav_text, callback_data=f"istikhara:fav:{record_id}")],
        [
            InlineKeyboardButton(text="🔄 استخاره دیگر (با نیت جدید)", callback_data="istikhara:do"),
            InlineKeyboardButton(text="📖 منوی استخاره", callback_data="menu:istikhara")
        ],
        [InlineKeyboardButton(text="🔙 منوی اصلی", callback_data="menu:main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_marja_selection_kb(current_marja: str = "sistani") -> InlineKeyboardMarkup:
    maraji = [
        ("sistani", "آیت‌الله العظمی سیستانی"),
        ("khamenei", "آیت‌الله العظمی خامنه‌ای"),
        ("makarem", "آیت‌الله العظمی مکارم شیرازی")
    ]
    buttons = []
    for code, title in maraji:
        prefix = "✅ " if code == current_marja else ""
        buttons.append([InlineKeyboardButton(text=f"{prefix}{title}", callback_data=f"set_marja:{code}")])
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu:istikhara")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_tafsir_selection_kb(current_tafsir: str = "nemooneh") -> InlineKeyboardMarkup:
    tafasir = [
        ("nemooneh", "تفسیر نمونه (روان و کاربردی)"),
        ("al-mizan", "تفسیر المیزان (علامه طباطبایی)"),
        ("majma-al-bayan", "تفسیر مجمع‌البیان (طبرسی)")
    ]
    buttons = []
    for code, title in tafasir:
        prefix = "✅ " if code == current_tafsir else ""
        buttons.append([InlineKeyboardButton(text=f"{prefix}{title}", callback_data=f"set_tafsir:{code}")])
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu:istikhara")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

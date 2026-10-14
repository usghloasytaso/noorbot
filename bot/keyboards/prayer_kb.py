"""
کیبوردهای انتخاب شهر و روش محاسبه اوقات شرعی
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.services.prayer_service import PrayerService


def get_cities_keyboard(current_city: str = "تهران") -> InlineKeyboardMarkup:
    cities = PrayerService.get_supported_cities()
    buttons = []
    row = []
    for city in cities:
        prefix = "📍 " if city == current_city else ""
        row.append(InlineKeyboardButton(text=f"{prefix}{city}", callback_data=f"set_city:{city}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(text="⚙️ تغییر روش محاسبه", callback_data="prayer:method"),
        InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="menu:main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_prayer_method_keyboard(current_method: str = "tehran") -> InlineKeyboardMarkup:
    methods = [
        ("tehran", "مؤسسه ژئوفیزیک دانشگاه تهران (رسمی ایران)"),
        ("leva", "مؤسسه لوای قم (شیعه اثناعشری)")
    ]
    buttons = []
    for code, title in methods:
        prefix = "✅ " if code == current_method else ""
        buttons.append([InlineKeyboardButton(text=f"{prefix}{title}", callback_data=f"set_method:{code}")])
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت به اوقات شرعی", callback_data="menu:prayer")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

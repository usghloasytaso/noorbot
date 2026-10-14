"""
کیبوردهای تسبیح‌شمار هوشمند و تعاملی
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_tasbih_keyboard(preset_id: str, count: int, max_target: int = 100) -> InlineKeyboardMarkup:
    """کیبورد شمارشگر تسبیح با بازخورد بصری زنده"""
    buttons = [
        [InlineKeyboardButton(text="➕ شمارش (+1)", callback_data=f"tasbih:inc:{preset_id}")],
        [
            InlineKeyboardButton(text="➖ کاهش (-1)", callback_data=f"tasbih:dec:{preset_id}"),
            InlineKeyboardButton(text="🔄 صفر کردن", callback_data=f"tasbih:reset:{preset_id}")
        ],
        [
            InlineKeyboardButton(text="🌸 تسبیحات حضرت زهرا", callback_data="tasbih:preset:zahra"),
            InlineKeyboardButton(text="📿 صلوات شمار", callback_data="tasbih:preset:salawat")
        ],
        [
            InlineKeyboardButton(text="🌿 استغفار", callback_data="tasbih:preset:istighfar"),
            InlineKeyboardButton(text="✨ ذکر یونسیه", callback_data="tasbih:preset:yunusiya")
        ],
        [InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="menu:main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

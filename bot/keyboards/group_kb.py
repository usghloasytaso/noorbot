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


def get_user_group_istikhara_kb(user_id: int, marja: str, tafsir: str, bot_username: str) -> InlineKeyboardMarkup:
    """کیبورد زیر پیام استخاره شخصی‌سازی‌شده در گروه"""
    marja_labels = {
        "sistani": "سیستانی",
        "khamenei": "رهبری",
        "makarem": "مکارم"
    }
    tafsir_labels = {
        "nemooneh": "نمونه",
        "al-mizan": "المیزان",
        "majma-al-bayan": "مجمع‌البیان"
    }
    m_name = marja_labels.get(marja, "سیستانی")
    t_name = tafsir_labels.get(tafsir, "نمونه")
    clean_user = bot_username.lstrip("@")

    buttons = [
        [
            InlineKeyboardButton(text=f"👤 تغییر مرجع ({m_name})", callback_data=f"grp_m_menu:{user_id}"),
            InlineKeyboardButton(text=f"📚 تغییر تفسیر ({t_name})", callback_data=f"grp_t_menu:{user_id}")
        ],
        [
            InlineKeyboardButton(text="🔄 استخاره مجدد", callback_data=f"grp_reist:{user_id}"),
            InlineKeyboardButton(text="⚙️ پروفایل در پی‌وی", url=f"https://t.me/{clean_user}?start=settings")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_group_marja_picker_kb(user_id: int, current_marja: str) -> InlineKeyboardMarkup:
    """کیبورد انتخاب مرجع تقلید مستقیم در گروه"""
    maraji = [
        ("sistani", "آیت‌الله سیستانی"),
        ("khamenei", "رهبر معظم انقلاب"),
        ("makarem", "آیت‌الله مکارم شیرازی")
    ]
    buttons = []
    for key, name in maraji:
        check = " ✅" if key == current_marja else ""
        buttons.append([
            InlineKeyboardButton(text=f"{name}{check}", callback_data=f"grp_set_m:{user_id}:{key}")
        ])
    buttons.append([
        InlineKeyboardButton(text="🔙 بازگشت به استخاره", callback_data=f"grp_back_ist:{user_id}")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_group_tafsir_picker_kb(user_id: int, current_tafsir: str) -> InlineKeyboardMarkup:
    """کیبورد انتخاب تفسیر مستقیم در گروه"""
    tafasir = [
        ("nemooneh", "تفسیر نمونه"),
        ("al-mizan", "تفسیر المیزان"),
        ("majma-al-bayan", "تفسیر مجمع‌البیان")
    ]
    buttons = []
    for key, name in tafasir:
        check = " ✅" if key == current_tafsir else ""
        buttons.append([
            InlineKeyboardButton(text=f"{name}{check}", callback_data=f"grp_set_t:{user_id}:{key}")
        ])
    buttons.append([
        InlineKeyboardButton(text="🔙 بازگشت به استخاره", callback_data=f"grp_back_ist:{user_id}")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_group_profile_kb(user_id: int, current_marja: str, current_tafsir: str, bot_username: str) -> InlineKeyboardMarkup:
    """کیبورد پروفایل اختصاصی کاربر در گروه"""
    clean_user = bot_username.lstrip("@")
    buttons = [
        [
            InlineKeyboardButton(text="👤 تغییر مرجع تقلید", callback_data=f"grp_m_menu:{user_id}"),
            InlineKeyboardButton(text="📚 تغییر تفسیر قرآن", callback_data=f"grp_t_menu:{user_id}")
        ],
        [
            InlineKeyboardButton(text="📖 باز کردن تنظیمات کامل در پی‌وی", url=f"https://t.me/{clean_user}?start=settings")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_group_tasbih_kb(count: int = 0) -> InlineKeyboardMarkup:
    """کیبورد صلوات‌شمار تعاملی گروهی"""
    buttons = [
        [
            InlineKeyboardButton(text=f"📿 ذکر صلوات (+1) | {count:,}", callback_data=f"grp_salawat:{count}")
        ],
        [
            InlineKeyboardButton(text="🔄 بازنشانی شمارنده", callback_data="grp_salawat_reset")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


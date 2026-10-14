"""
هندلرهای دستورات /start و /help، منوی اصلی و تنظیمات کاربری
"""

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from bot.config import settings
from bot.db.models import User
from bot.db.repository import UserRepository
from bot.keyboards.common import (
    get_back_button,
    get_main_inline_menu,
    get_main_reply_keyboard,
)
from bot.keyboards.istikhara_kb import get_marja_selection_kb, get_tafsir_selection_kb

router = Router(name="start_handler")


WELCOME_TEXT = """
✨ <b>به ربات جامع مذهبی و قرآنی نور (NoorBot) خوش آمدید</b> ✨

این ربات با بهره‌گیری از منابع معتبر و اصیل شیعه، امکانات متعددی را در اختیار شما قرار می‌دهد:

📖 <b>استخاره مستند با قرآن:</b> بر مبنای مصحف شریف و با رعایت دقیق شروط فقهی
✨ <b>آیه و محتوای روز:</b> آیه منتخب روز، احادیث معتبر و اذکار ایام هفته
📿 <b>تسبیح‌شمار تعاملی:</b> تسبیحات حضرت زهرا (س)، صلوات‌شمار و اذکار با ذخیره شمارش
🕌 <b>اوقات شرعی:</b> محاسبه دقیق اوقات شرعی برای شهرهای ایران و عتبات عالیات
🔍 <b>جستجوی قرآن:</b> دسترسی به فهرست سوره‌ها و آیات نورانی
📜 <b>احکام شرعی:</b> بررسی استفتائات و فتاوای مراجع معظم تقلید

👇 <i>از دکمه‌های زیر یا منوی پایین صفحه برای انتخاب بخش مورد نظر استفاده فرمایید:</i>
"""

HELP_TEXT = """
📖 <b>راهنمای جامع ربات نور (NoorBot)</b>

دستورات فعال در گفتگوهای خصوصی و گروه‌ها:
▫️ <code>/start</code> - نمایش منوی اصلی و شروع کار با ربات
▫️ <code>/istikhara</code> - ورود به بخش استخاره با قرآن کریم
▫️ <code>/ayah</code> - دریافت آیه نورانی روز همراه با ترجمه
▫️ <code>/daily</code> - تقویم روز، مناسبت‌های مذهبی، ذکر و حدیث روز
▫️ <code>/prayer</code> - نمایش اوقات شرعی شهر انتخابی شما
▫️ <code>/tasbih</code> - بازکردن تسبیح‌شمار تعاملی و هوشمند
▫️ <code>/quran</code> - فهرست سوره‌ها و جستجو در متن قرآن
▫️ <code>/settings</code> - مدیریت تنظیمات (مرجع تقلید، تفسیر، شهر، اعلان‌ها)
▫️ <code>/help</code> - نمایش این پیام راهنما

👥 <b>استفاده در گروه‌ها:</b>
با افزودن ربات به گروه‌های مذهبی و خانوادگی، می‌توانید از امکانات اشتراکی بهره‌مند شوید. مدیران گروه می‌توانند با دستور <code>/settings</code> تنظیمات اختصاصی گروه را کنترل کنند.

🔒 <b>حریم خصوصی و امنیت:</b>
ربات نور هیچ‌گونه اطلاعات خصوصی کاربران را افشا نمی‌کند و امکان حذف کامل تاریخچه یا ارسال خصوصی نتایج استخاره فراهم است.
"""


@router.message(CommandStart(), F.chat.type == "private")
async def cmd_start_private(message: Message, user: User):
    await message.answer(
        text=WELCOME_TEXT,
        reply_markup=get_main_reply_keyboard(),
        parse_mode="HTML"
    )
    await message.answer(
        text="📌 <b>منوی دسترسی سریع:</b>",
        reply_markup=get_main_inline_menu(),
        parse_mode="HTML"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        text=HELP_TEXT,
        reply_markup=get_back_button("main"),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "menu:main")
async def cb_main_menu(call: CallbackQuery):
    await call.message.edit_text(
        text=WELCOME_TEXT,
        reply_markup=get_main_inline_menu(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "menu:help")
async def cb_help_menu(call: CallbackQuery):
    await call.message.edit_text(
        text=HELP_TEXT,
        reply_markup=get_back_button("main"),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "menu:settings")
@router.message(Command("settings"), F.chat.type == "private")
async def show_user_settings(event: Message | CallbackQuery, user: User):
    marja_names = {
        "sistani": "آیت‌الله العظمی سیستانی",
        "khamenei": "آیت‌الله العظمی خامنه‌ای",
        "makarem": "آیت‌الله العظمی مکارم شیرازی"
    }
    tafsir_names = {
        "nemooneh": "تفسیر نمونه",
        "al-mizan": "تفسیر المیزان",
        "majma-al-bayan": "تفسیر مجمع‌البیان"
    }

    marja_title = marja_names.get(user.selected_marja, user.selected_marja)
    tafsir_title = tafsir_names.get(user.selected_tafsir, user.selected_tafsir)
    hist_status = "✅ فعال" if user.save_history else "❌ غیرفعال"
    notif_status = f"✅ فعال (ساعت {user.notification_time})" if user.notifications_enabled else "❌ غیرفعال"

    text = (
        "⚙️ <b>تنظیمات حساب کاربری شما</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"⚖️ <b>مرجع تقلید:</b> {marja_title}\n"
        f"📚 <b>تفسیر منتخب:</b> {tafsir_title}\n"
        f"📍 <b>شهر اوقات شرعی:</b> {user.city}\n"
        f"🕒 <b>ذخیره تاریخچه استخاره:</b> {hist_status}\n"
        f"🔔 <b>اعلان‌های روزانه:</b> {notif_status}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "جهت تغییر هر یک از موارد، دکمه مربوطه را انتخاب کنید:"
    )

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    buttons = [
        [
            InlineKeyboardButton(text="⚖️ تغییر مرجع تقلید", callback_data="settings:marja"),
            InlineKeyboardButton(text="📚 تغییر تفسیر", callback_data="settings:tafsir")
        ],
        [
            InlineKeyboardButton(text="📍 تغییر شهر اوقات شرعی", callback_data="menu:prayer"),
            InlineKeyboardButton(text="🔔 فعال/غیرفعال اعلان‌ها", callback_data="settings:toggle_notif")
        ],
        [
            InlineKeyboardButton(text="🗑 پاکسازی سابقه استخاره", callback_data="settings:clear_history"),
            InlineKeyboardButton(text="🔙 منوی اصلی", callback_data="menu:main")
        ]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text=text, reply_markup=markup, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text=text, reply_markup=markup, parse_mode="HTML")


@router.callback_query(F.data == "settings:marja")
async def cb_settings_marja(call: CallbackQuery, user: User):
    await call.message.edit_text(
        text=(
            "⚖️ <b>انتخاب مرجع تقلید جهت نمایش احکام و شروط استخاره:</b>\n\n"
            "⚠️ <i>توجه شرعی: انتخاب مرجع صرفاً برای استناد احکام و شروط فقهی است و هرگز به معنای انتساب یک نتیجهٔ خاص به آن فقیه بزرگوار نمی‌باشد.</i>"
        ),
        reply_markup=get_marja_selection_kb(user.selected_marja),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("set_marja:"))
async def cb_set_marja(call: CallbackQuery, user: User):
    marja_code = call.data.split(":")[1]
    await UserRepository.update_marja(user.telegram_id, marja_code)
    user.selected_marja = marja_code
    await call.answer("✅ مرجع تقلید با موفقیت به‌روزرسانی شد.", show_alert=True)
    await show_user_settings(call, user)


@router.callback_query(F.data == "settings:tafsir")
async def cb_settings_tafsir(call: CallbackQuery, user: User):
    await call.message.edit_text(
        text="📚 <b>انتخاب تفسیر قرآن جهت نمایش نکات تفسیری آیات:</b>",
        reply_markup=get_tafsir_selection_kb(user.selected_tafsir),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("set_tafsir:"))
async def cb_set_tafsir(call: CallbackQuery, user: User):
    tafsir_code = call.data.split(":")[1]
    await UserRepository.update_tafsir(user.telegram_id, tafsir_code)
    user.selected_tafsir = tafsir_code
    await call.answer("✅ تفسیر منتخب با موفقیت به‌روزرسانی شد.", show_alert=True)
    await show_user_settings(call, user)


@router.callback_query(F.data == "settings:toggle_notif")
async def cb_toggle_notif(call: CallbackQuery, user: User):
    new_state = not user.notifications_enabled
    await UserRepository.toggle_notifications(user.telegram_id, new_state, user.notification_time)
    user.notifications_enabled = new_state
    msg = "✅ اعلان‌های روزانه فعال گردید." if new_state else "❌ اعلان‌های روزانه غیرفعال گردید."
    await call.answer(msg, show_alert=True)
    await show_user_settings(call, user)


@router.callback_query(F.data == "settings:clear_history")
async def cb_clear_history(call: CallbackQuery, user: User):
    from bot.db.repository import IstikharaRepository
    await IstikharaRepository.clear_history(user.telegram_id)
    await call.answer("✅ تاریخچه استخاره‌های شما با موفقیت پاکسازی شد.", show_alert=True)
    await show_user_settings(call, user)

"""
هندلرهای مربوط به قرآن کریم، آیهٔ روز و جستجو در سوره‌ها
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.db.repository import StatsRepository
from bot.keyboards.common import get_back_button
from bot.services.quran_service import QuranService

router = Router(name="quran_handler")


@router.message(Command("ayah"))
@router.message(F.text == "✨ آیه و محتوای روز")
@router.callback_query(F.data == "menu:daily_ayah")
async def show_daily_ayah(event: Message | CallbackQuery):
    ayah = QuranService.get_daily_ayah()
    text = QuranService.format_daily_ayah_message(ayah)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 فهرست و جستجوی سوره‌ها", callback_data="menu:quran_search")],
            [InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="menu:main")]
        ]
    )

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text=text, reply_markup=kb, parse_mode="HTML")


@router.message(Command("quran"))
@router.message(F.text == "🔍 جستجوی قرآن")
@router.callback_query(F.data == "menu:quran_search")
async def show_quran_menu(event: Message | CallbackQuery):
    text = (
        "🔍 <b>سامانه جستجو و مرور سوره‌های قرآن کریم</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "شما می‌توانید با ارسال نام سوره یا شماره سوره (مثلاً: <code>یس</code> یا <code>36</code> یا <code>الملک</code>)، "
        "مشخصات کامل آن را دریافت کنید.\n\n"
        "📖 <b>سوره‌های پرفضیلت قرآن:</b>"
    )
    popular_surahs = [
        ("الفاتحة (۱)", 1),
        ("البقرة (۲)", 2),
        ("یس (۳۶)", 36),
        ("الرحمن (۵۵)", 55),
        ("الواقعة (۵۶)", 56),
        ("الملک (۶۷)", 67),
        ("النبأ (۷۸)", 78),
        ("الإخلاص (۱۱۲)", 112)
    ]
    buttons = []
    row = []
    for name, num in popular_surahs:
        row.append(InlineKeyboardButton(text=name, callback_data=f"surah:view:{num}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="menu:main")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text=text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("surah:view:"))
async def view_surah_details(call: CallbackQuery):
    num_str = call.data.split(":")[2]
    if num_str.isdigit():
        num = int(num_str)
        surah = QuranService.get_surah_by_number(num)
        if surah:
            type_fa = "مکی" if surah["type"] == "Meccan" else "مدنی"
            text = (
                f"📜 <b>سوره مبارکه {surah['name']}</b> ({surah['tname']})\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"▫️ <b>شماره سوره:</b> {surah['number']}\n"
                f"▫️ <b>محل نزول:</b> {type_fa}\n"
                f"▫️ <b>تعداد آیات:</b> {surah['ayas']}\n"
                f"▫️ <b>صفحه شروع در مصحف شریف:</b> صفحه {surah['start_page']}\n"
                f"▫️ <b>معنای فارسی:</b> {surah['ename']}\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "<i>برای مشاهده آیات نورانی و استماع تلاوت، می‌توانید از پایگاه رسمی Tanzil.net بهره ببرید.</i>"
            )
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📖 بازگشت به فهرست سوره‌ها", callback_data="menu:quran_search")],
                    [InlineKeyboardButton(text="🔙 منوی اصلی", callback_data="menu:main")]
                ]
            )
            await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
            await call.answer()
            return
    await call.answer("سوره یافت نشد.", show_alert=True)

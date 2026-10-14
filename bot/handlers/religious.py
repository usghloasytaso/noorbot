"""
هندلرهای مربوط به تقویم دینی، مناسبت‌ها، ادعیه و زیارات
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.keyboards.common import get_back_button
from bot.services.calendar_service import CalendarService

router = Router(name="religious_handler")


@router.message(Command("daily"))
@router.callback_query(F.data == "menu:calendar")
async def show_daily_calendar(event: Message | CallbackQuery):
    today_info = CalendarService.get_today_info()
    text = CalendarService.format_daily_content(today_info)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🤲 ادعیه و زیارات", callback_data="menu:duas")],
            [InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="menu:main")]
        ]
    )

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text=text, reply_markup=kb, parse_mode="HTML")


@router.message(F.text == "🤲 ادعیه و زیارات")
@router.callback_query(F.data == "menu:duas")
async def show_duas_menu(event: Message | CallbackQuery):
    text = (
        "🤲 <b>گنجینه ادعیه و زیارات معتبر</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "لطفاً دعای مورد نظر خود را جهت مطالعه متن عربی، ترجمه فارسی و مأخذ انتخاب فرمایید:"
    )
    buttons = [
        [
            InlineKeyboardButton(text="🕊 دعای فرج (الهی عظم البلاء)", callback_data="dua:view:faraj"),
            InlineKeyboardButton(text="🌿 دعای سلامتی امام زمان (عج)", callback_data="dua:view:salamati")
        ],
        [
            InlineKeyboardButton(text="📜 فرازی از دعای عهد", callback_data="dua:view:ahd")
        ],
        [
            InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="menu:main")
        ]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text=text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("dua:view:"))
async def view_dua_detail(call: CallbackQuery):
    dua_id = call.data.split(":")[2]
    CalendarService.load_data()
    duas = CalendarService._duas_data.get("duas", [])
    selected = next((d for d in duas if d["id"] == dua_id), None)

    if selected:
        text = (
            f"🤲 <b>{selected['title']}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>«{selected['arabic']}»</i>\n\n"
            f"📝 <b>ترجمه فارسی:</b>\n"
            f"«{selected['persian']}»\n\n"
            f"📚 <b>مأخذ معتبر:</b> {selected['source']}"
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📖 بازگشت به فهرست ادعیه", callback_data="menu:duas")],
                [InlineKeyboardButton(text="🔙 منوی اصلی", callback_data="menu:main")]
            ]
        )
        await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
        await call.answer()
    else:
        await call.answer("دعا یافت نشد.", show_alert=True)

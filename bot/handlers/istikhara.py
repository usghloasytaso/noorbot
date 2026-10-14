"""
هندلرهای مربوط به بخش استخاره با قرآن کریم
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.db.models import User
from bot.db.repository import IstikharaRepository
from bot.keyboards.common import get_back_button
from bot.keyboards.istikhara_kb import (
    get_istikhara_menu_kb,
    get_istikhara_result_kb,
)
from bot.services.istikhara_service import IstikharaService

router = Router(name="istikhara_handler")

ISTIKHARA_INTRO_TEXT = """
📖 <b>بخش استخاره با قرآن کریم</b>

استخاره به معنای طلب خیر از خداوند متعال است. بر اساس فتاوای مراجع معظم تقلید، استخاره با قرآن مراحلی دارد:

۱. <b>تعقل و تفکر:</b> بررسی جوانب کار با خرد و تدبیر.
۲. <b>مشورت:</b> رایزنی با کارشناسان، خردمندان و اهل خبره.
۳. <b>رفع تحیّر:</b> چنانچه پس از تفکر و مشورت، همچنان در سرگردانی و دودلی ماندید، نوبت به استخاره می‌رسد.

🕊 <b>آداب شرعی قبل از استخاره:</b>
▫️ با وضو و رو به قبله باشید.
▫️ ۳ مرتبه سوره مبارکه اخلاص (توحید) را قرائت فرمایید.
▫️ ۳ صلوات بر محمد و آل محمد (ص) بفرستید.
▫️ دعای استخاره را زمزمه کنید:
<i>«اللَّهُمَّ إِنِّي تَفَأَّلْتُ بِكِتَابِكَ، وَ تَوَكَّلْتُ عَلَيْكَ، فَأَرِنِي مِنْ كِتَابِكَ مَا هُوَ مَكْتُومٌ مِنْ سِرِّكَ الْمَكْنُونِ فِي غَيْبِكَ»</i>

🤲 نیت خویش را خالصانه در نظر بگیرید و دکمهٔ زیر را لمس نمایید:
"""


@router.message(Command("istikhara"))
@router.message(F.text == "📖 استخاره با قرآن")
@router.callback_query(F.data == "menu:istikhara")
async def show_istikhara_intro(event: Message | CallbackQuery):
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(
            text=ISTIKHARA_INTRO_TEXT,
            reply_markup=get_istikhara_menu_kb(),
            parse_mode="HTML"
        )
        await event.answer()
    else:
        await event.answer(
            text=ISTIKHARA_INTRO_TEXT,
            reply_markup=get_istikhara_menu_kb(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "istikhara:do")
async def do_istikhara(call: CallbackQuery, user: User):
    await call.answer("⏳ در حال استخراج و تطبیق آیه شریفه...", show_alert=False)

    # اجرای استخاره با اعتبارسنجی
    result = IstikharaService.perform_istikhara()
    formatted_msg = IstikharaService.format_istikhara_message(
        result,
        marja=user.selected_marja,
        tafsir=user.selected_tafsir
    )

    # ثبت در تاریخچه کاربر در صورت تمایل کاربر
    record_id = 0
    if user.save_history:
        record_id = await IstikharaRepository.save_record(
            telegram_id=user.telegram_id,
            surah_number=result.get("surah_number", 1),
            surah_name=result.get("surah_name", "قرآن"),
            ayah_number=result.get("ayah_number", 1),
            page_number=result.get("page", 1),
            result_code=result.get("result_code", "good"),
            result_title=result.get("result_title", "خوب")
        )

    await call.message.edit_text(
        text=formatted_msg,
        reply_markup=get_istikhara_result_kb(record_id, is_favorite=False),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("istikhara:fav:"))
async def toggle_favorite(call: CallbackQuery, user: User):
    parts = call.data.split(":")
    if len(parts) >= 3 and parts[2].isdigit():
        rec_id = int(parts[2])
        is_fav = await IstikharaRepository.toggle_favorite(rec_id, user.telegram_id)
        alert_msg = "⭐ به علاقه‌مندی‌ها اضافه شد." if is_fav else "❌ از علاقه‌مندی‌ها حذف شد."
        await call.answer(alert_msg, show_alert=True)
        await call.message.edit_reply_markup(
            reply_markup=get_istikhara_result_kb(rec_id, is_favorite=is_fav)
        )
    else:
        await call.answer("خطا در شناسایی نتیجه.", show_alert=True)


@router.callback_query(F.data == "istikhara:adab")
async def show_istikhara_adab(call: CallbackQuery):
    methodology = IstikharaService.get_methodology()
    conds = methodology.get("conditions", [])
    conds_text = "\n".join([f"▫️ {c}" for c in conds])

    text = (
        "📜 <b>آداب، شروط و جایگاه فقهی استخاره با قرآن</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{methodology.get('description', '')}\n\n"
        "<b>مراحل و شرایط لازم:</b>\n"
        f"{conds_text}\n\n"
        "⚠️ <b>نکات مهم:</b>\n"
        "۱. در واجبات و محرمات استخاره باطل است.\n"
        "۲. استخاره پیشگویی آینده نیست؛ بلکه تعیین مسیر برتر در حالت تحیر است.\n"
        "۳. تکرار استخاره برای یک نیت بدون تغییر اوضاع ناپسند است."
    )
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✨ انجام استخاره", callback_data="istikhara:do")],
            [InlineKeyboardButton(text="🔙 بازگشت به منوی استخاره", callback_data="menu:istikhara")]
        ]
    )
    await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "istikhara:history")
async def show_istikhara_history(call: CallbackQuery, user: User):
    history = await IstikharaRepository.get_user_history(user.telegram_id, limit=5)
    if not history:
        text = (
            "🕒 <b>تاریخچه استخاره‌های شما</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "هنوز هیچ استخاره‌ای در سوابق شما ثبت نشده است.\n"
            "در صورت انجام استخاره، نتایج قبلی شما در اینجا نمایش داده خواهند شد."
        )
    else:
        lines = [
            "🕒 <b>تاریخچه استخاره‌های اخیر شما:</b>",
            "━━━━━━━━━━━━━━━━━━━━"
        ]
        for idx, item in enumerate(history, start=1):
            fav_icon = "⭐ " if item.is_favorite else ""
            date_str = item.created_at.strftime("%Y-%m-%d %H:%M") if item.created_at else ""
            lines.append(
                f"{idx}. {fav_icon}<b>سوره {item.surah_name} (آیه {item.ayah_number})</b> - صفحه {item.page_number}\n"
                f"   نتیجه: <b>{item.result_title}</b> ({date_str})\n"
            )
        text = "\n".join(lines)

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✨ انجام استخاره جدید", callback_data="istikhara:do")],
            [InlineKeyboardButton(text="🔙 بازگشت به منوی استخاره", callback_data="menu:istikhara")]
        ]
    )
    await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    await call.answer()

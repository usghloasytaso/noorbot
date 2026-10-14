"""
هندلرهای مربوط به اوقات شرعی و انتخاب شهر
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.db.models import User
from bot.db.repository import UserRepository
from bot.keyboards.prayer_kb import get_cities_keyboard, get_prayer_method_keyboard
from bot.services.prayer_service import PrayerService

router = Router(name="prayer_handler")


@router.message(Command("prayer"))
@router.message(F.text == "🕌 اوقات شرعی")
@router.callback_query(F.data == "menu:prayer")
async def show_prayer_times(event: Message | CallbackQuery, user: User):
    times = PrayerService.calculate_times(city_name=user.city, method=user.prayer_method)
    text = PrayerService.format_prayer_message(times)
    kb = get_cities_keyboard(user.city)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text=text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("set_city:"))
async def change_city(call: CallbackQuery, user: User):
    city = call.data.split(":")[1]
    await UserRepository.update_city(user.telegram_id, city, user.prayer_method)
    user.city = city

    times = PrayerService.calculate_times(city_name=city, method=user.prayer_method)
    text = PrayerService.format_prayer_message(times)
    kb = get_cities_keyboard(city)

    await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    await call.answer(f"📍 شهر به {city} تغییر یافت.")


@router.callback_query(F.data == "prayer:method")
async def show_methods(call: CallbackQuery, user: User):
    await call.message.edit_text(
        text=(
            "⚙️ <b>انتخاب روش و زاویه محاسبه اوقات شرعی:</b>\n\n"
            "▫️ <b>دانشگاه تهران:</b> زاویه فجر ۱۷.۷ درجه و مغرب ۴.۵ درجه (معیار رسمی صدا و سیما و تقویم ایران)\n"
            "▫️ <b>مؤسسه لوای قم:</b> زاویه فجر ۱۶.۰ درجه و مغرب ۴.۰ درجه (معیار فقهی رایج در برخی مراکز حوزوی)"
        ),
        reply_markup=get_prayer_method_keyboard(user.prayer_method),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("set_method:"))
async def change_method(call: CallbackQuery, user: User):
    method = call.data.split(":")[1]
    await UserRepository.update_city(user.telegram_id, user.city, method)
    user.prayer_method = method
    await call.answer("✅ روش محاسبه به‌روزرسانی شد.", show_alert=True)
    await show_prayer_times(call, user)

"""
هندلرهای اختصاصی گروه‌ها (Group Bot Management & Features)
کنترل دسترسی مدیران، رعایت Privacy Mode و ارسال خصوصی/عمومی نتایج
"""

import logging
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.db.models import Group, User
from bot.db.repository import GroupRepository, IstikharaRepository
from bot.keyboards.group_kb import get_group_settings_keyboard
from bot.services.calendar_service import CalendarService
from bot.services.istikhara_service import IstikharaService
from bot.services.quran_service import QuranService

logger = logging.getLogger("handler.group")
router = Router(name="group_handler")


async def _is_group_admin(message: Message) -> bool:
    """بررسی ادمین‌بودن کاربر در گروه"""
    if message.chat.type not in ("group", "supergroup"):
        return False
    try:
        member = await message.bot.get_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)
        return member.status in ("creator", "administrator")
    except Exception as e:
        logger.warning("Failed to check chat member status: %s", e)
        return False


@router.message(Command("start"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_start_group(message: Message, group: Group):
    bot_info = await message.bot.get_me()
    text = (
        f"🌟 <b>ربات مذهبی و قرآنی نور در گروه {message.chat.title} فعال شد!</b>\n\n"
        "دستورات فعال در گروه:\n"
        "▫️ <code>/istikhara</code> - استخاره با قرآن کریم\n"
        "▫️ <code>/ayah</code> - دریافت آیه روز\n"
        "▫️ <code>/daily</code> - تقویم و مناسبت‌های امروز\n"
        "▫️ <code>/settings</code> - پنل تنظیمات گروه (مخصوص مدیران گروه)\n"
        "▫️ <code>/help</code> - راهنمای امکانات"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📖 بازکردن در چت خصوصی", url=f"https://t.me/{bot_info.username}?start=group")]
        ]
    )
    await message.answer(text=text, reply_markup=kb, parse_mode="HTML")


@router.message(Command("settings"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_settings_group(message: Message, group: Group):
    is_admin = await _is_group_admin(message)
    if not is_admin:
        await message.reply("⚠️ تنها مدیران این گروه اجازه تغییر تنظیمات ربات را دارند.")
        return

    text = (
        f"⚙️ <b>تنظیمات ربات در گروه «{message.chat.title}»</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "مدیر گرامی، می‌توانید قابلیت‌های مورد نظر را برای این گروه فعال یا غیرفعال فرمایید:"
    )
    await message.answer(text=text, reply_markup=get_group_settings_keyboard(group), parse_mode="HTML")


@router.callback_query(F.data.startswith("grp_toggle:"), F.message.chat.type.in_({"group", "supergroup"}))
async def cb_group_toggle(call: CallbackQuery, group: Group):
    # بررسی مجدد دسترسی ادمین
    member = await call.bot.get_chat_member(chat_id=call.message.chat.id, user_id=call.from_user.id)
    if member.status not in ("creator", "administrator"):
        await call.answer("⚠️ شما مدیر این گروه نیستید.", show_alert=True)
        return

    action = call.data.split(":")[1]
    if action == "istikhara":
        group.allow_istikhara = not group.allow_istikhara
    elif action == "priv_mode":
        group.private_result_mode = not group.private_result_mode
    elif action == "daily_ayah":
        group.allow_daily_ayah = not group.allow_daily_ayah

    await GroupRepository.update_settings(
        chat_id=group.chat_id,
        allow_istikhara=group.allow_istikhara,
        private_mode=group.private_result_mode,
        allow_daily_ayah=group.allow_daily_ayah
    )
    await call.message.edit_reply_markup(reply_markup=get_group_settings_keyboard(group))
    await call.answer("✅ تنظیمات با موفقیت به‌روزرسانی شد.")


@router.callback_query(F.data == "grp_refresh", F.message.chat.type.in_({"group", "supergroup"}))
async def cb_group_refresh(call: CallbackQuery, group: Group):
    await call.message.edit_reply_markup(reply_markup=get_group_settings_keyboard(group))
    await call.answer("🔄 به‌روز شد.")


@router.message(Command("istikhara"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_istikhara_group(message: Message, group: Group, user: User):
    if not group.allow_istikhara:
        await message.reply("⚠️ قابلیت استخاره توسط مدیران در این گروه غیرفعال شده است.")
        return

    bot_info = await message.bot.get_me()

    # در صورت فعال‌بودن حالت حریم خصوصی، ارسال نتیجه در پی‌وی کاربر انجام می‌شود
    if group.private_result_mode:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔒 انجام و مشاهده استخاره در پی‌وی",
                        url=f"https://t.me/{bot_info.username}?start=istikhara"
                    )
                ]
            ]
        )
        await message.reply(
            text=(
                f"👤 {message.from_user.mention_html()}\n"
                "🔒 <b>جهت حفظ حریم خصوصی نیت شما و عدم شلوغی گروه:</b>\n"
                "لطفاً جهت انجام استخاره و دریافت نتیجه، دکمه زیر را لمس کرده و وارد گفتگوی خصوصی شوید."
            ),
            reply_markup=kb,
            parse_mode="HTML"
        )
        return

    # ارسال عمومی در گروه
    result = IstikharaService.perform_istikhara()
    formatted = IstikharaService.format_istikhara_message(result, marja=user.selected_marja, tafsir=user.selected_tafsir)
    await message.reply(text=formatted, parse_mode="HTML")


@router.message(Command("ayah"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_ayah_group(message: Message, group: Group):
    ayah = QuranService.get_daily_ayah()
    text = QuranService.format_daily_ayah_message(ayah)
    await message.answer(text=text, parse_mode="HTML")


@router.message(Command("daily"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_daily_group(message: Message, group: Group):
    today_info = CalendarService.get_today_info()
    text = CalendarService.format_daily_content(today_info)
    await message.answer(text=text, parse_mode="HTML")

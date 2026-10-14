"""
هندلرهای اختصاصی گروه‌ها (Group Bot Management & Features)
پیام هوشمند خوش‌آمدگویی، بررسی دسترسی‌ها، رعایت Privacy Mode و کنترل مدیران
"""

import html
import logging
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    ChatMemberAdministrator,
    ChatMemberOwner,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from bot.db.models import Group, User
from bot.db.repository import GroupRepository, IstikharaRepository
from bot.keyboards.group_kb import get_group_settings_keyboard
from bot.services.calendar_service import CalendarService
from bot.services.istikhara_service import IstikharaService
from bot.services.quran_service import QuranService

logger = logging.getLogger("handler.group")
router = Router(name="group_handler")


async def _is_group_admin(message: Message) -> bool:
    """بررسی ادمین‌بودن کاربر ارسال‌کننده پیام در گروه"""
    if message.chat.type not in ("group", "supergroup"):
        return False
    try:
        member = await message.bot.get_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)
        return member.status in ("creator", "administrator")
    except Exception as e:
        logger.warning("Failed to check chat member status: %s", e)
        return False


def build_smart_group_welcome(chat_title: str, bot_member, bot_username: str) -> tuple[str, InlineKeyboardMarkup]:
    """
    تولید پیام هوشمند ورود به گروه به همراه ارزیابی سطح دسترسی‌های ربات
    """
    safe_title = html.escape(chat_title or "گروه")
    status = getattr(bot_member, "status", "member")
    is_admin = status in ("administrator", "creator")

    if is_admin:
        admin_rights = []
        if getattr(bot_member, "can_delete_messages", False):
            admin_rights.append("حذف پیام‌های منسوخ")
        if getattr(bot_member, "can_pin_messages", False):
            admin_rights.append("سنجاق محتوای روزانه")
        if getattr(bot_member, "can_invite_users", False):
            admin_rights.append("دعوت کاربران")

        rights_desc = " (" + "، ".join(admin_rights) + ")" if admin_rights else ""

        perm_box = (
            "🛡 <b>وضعیت دسترسی در گروه:</b> 🟢 <b>مدیر (Administrator)</b>\n"
            f"✅ <i>دسترسی‌های لازم تایید شد{rights_desc}؛ ربات بدون هیچ محدودیتی آماده خدمت‌رسانی است.</i>"
        )
    else:
        perm_box = (
            "🛡 <b>وضعیت دسترسی در گروه:</b> 🟡 <b>عضو عادی</b>\n"
            "⚠️ <b>یادآوری به مدیران محترم گروه:</b>\n"
            "من در حال حاضر به عنوان عضو عادی اضافه شده‌ام. برای عملکرد کامل (حذف خودکار پیام‌های منسوخ، پین‌کردن آیه روزانه و پاسخ‌دهی سریع)، "
            "پیشنهاد می‌شود به ربات دسترسی <b>مدیریت (Admin)</b> اعطا فرمایید.\n\n"
            "🔒 <i>(طبق قوانین حریم خصوصی تلگرام، ربات به عنوان عضو عادی تنها دستوراتی را می‌بیند که با <code>/</code> آغاز شوند یا ریپلای روی پیام‌های ربات باشند).</i>"
        )

    text = (
        f"🌸 <b>سلام و درود بر اعضای محترم گروه «{safe_title}»</b>\n\n"
        "من <b>ربات جامع مذهبی و قرآنی نور (NoorBot)</b> هستم؛ مایهٔ افتخار است که در جمع معنوی و پربرکت شما حضور دارم.\n\n"
        f"{perm_box}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📌 <b>دستورات و امکانات فعال در این گروه:</b>\n"
        "▫️ <code>/istikhara</code> - استخاره با قرآن کریم (با امکان دریافت در پی‌وی جهت حفظ خلوت نیت)\n"
        "▫️ <code>/ayah</code> - دریافت آیه نورانی روز به همراه ترجمه\n"
        "▫️ <code>/daily</code> - تقویم روز، مناسبت‌های مذهبی، ذکر و حدیث روز\n"
        "▫️ <code>/prayer</code> - اوقات شرعی شهرهای ایران و عتبات عالیات\n"
        "▫️ <code>/tasbih</code> - تسبیح‌شمار تعاملی و هوشمند\n"
        "▫️ <code>/settings</code> - پنل تنظیمات گروه (مخصوص مدیران گروه)\n"
        "▫️ <code>/help</code> - راهنمای جامع و فهرست دستورات\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🤲 <i>امید است مایهٔ برکت، انس افزون‌تر با کلام وحی و تمسک به مکتب اهل‌بیت (ع) باشیم.</i>"
    )

    clean_user = bot_username.lstrip("@")
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚙️ تنظیمات گروه (مدیران)", callback_data="grp_refresh"),
                InlineKeyboardButton(text="📖 ورود به پی‌وی ربات", url=f"https://t.me/{clean_user}?start=group")
            ],
            [
                InlineKeyboardButton(text="📜 راهنما و احکام استخاره", callback_data="menu:help")
            ]
        ]
    )
    return text, kb


# ۱. رویداد هوشمند تغییر وضعیت عضویت ربات در گروه (ورود، خروج، ارتقا به ادمین)
@router.my_chat_member()
async def on_my_chat_member_updated(event: ChatMemberUpdated):
    if event.chat.type not in ("group", "supergroup"):
        return

    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status
    logger.info("Chat %s (%s): bot status changed: %s -> %s", event.chat.title, event.chat.id, old_status, new_status)

    # الف) اگر ربات از گروه خارج شد یا ریمو شد
    if new_status in ("left", "kicked"):
        try:
            await GroupRepository.set_active(event.chat.id, False)
        except Exception as e:
            logger.warning("Could not deactivate group %s: %s", event.chat.id, e)
        return

    # ب) اگر ربات به گروه اضافه شد (ورود اولیه)
    if old_status in ("left", "kicked", "restricted") and new_status in ("member", "administrator"):
        try:
            await GroupRepository.upsert_group(
                chat_id=event.chat.id,
                title=event.chat.title,
                username=event.chat.username,
                chat_type=event.chat.type
            )
        except Exception as e:
            logger.warning("DB upsert group failed: %s", e)

        bot_user = event.new_chat_member.user
        text, kb = build_smart_group_welcome(
            chat_title=event.chat.title or "گروه",
            bot_member=event.new_chat_member,
            bot_username=bot_user.username or "NoorBot"
        )

        try:
            await event.bot.send_message(
                chat_id=event.chat.id,
                text=text,
                reply_markup=kb,
                parse_mode="HTML"
            )
            logger.info("Successfully sent welcome message to group %s", event.chat.id)
        except Exception as e:
            logger.error("Could not send welcome message to group %s: %s", event.chat.id, e)
        return

    # ج) اگر ربات از عضو عادی به ادمین ارتقا یافت
    if old_status == "member" and new_status == "administrator":
        text = (
            "🛡 <b>دسترسی مدیریتی ربات نور با موفقیت تایید شد!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "مدیران محترم، سپاس از حسن اعتماد شما.\n"
            "✅ اکنون تمامی امکانات (پین‌کردن آیه روزانه، حذف پیام‌های منسوخ و پاسخگویی بی‌درنگ) فعال است.\n\n"
            "با دستور <code>/settings</code> می‌توانید امکانات این گروه را پیکربندی نمایید."
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⚙️ باز کردن پنل تنظیمات گروه", callback_data="grp_refresh")]
            ]
        )
        try:
            await event.bot.send_message(
                chat_id=event.chat.id,
                text=text,
                reply_markup=kb,
                parse_mode="HTML"
            )
            logger.info("Successfully sent admin promotion message to group %s", event.chat.id)
        except Exception as e:
            logger.error("Could not send admin promotion message: %s", e)


# ۲. رویداد پیامِ اضافه شدن اعضای جدید (New Chat Members)
@router.message(F.new_chat_members)
async def on_new_chat_members(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return

    bot_info = await message.bot.get_me()
    is_bot_added = any(m.id == bot_info.id for m in (message.new_chat_members or []))
    if is_bot_added:
        logger.info("Bot detected in new_chat_members of group %s", message.chat.id)
        try:
            await GroupRepository.upsert_group(
                chat_id=message.chat.id,
                title=message.chat.title,
                username=message.chat.username,
                chat_type=message.chat.type
            )
        except Exception:
            pass

        try:
            bot_member = await message.bot.get_chat_member(chat_id=message.chat.id, user_id=bot_info.id)
        except Exception:
            bot_member = message.bot

        text, kb = build_smart_group_welcome(
            chat_title=message.chat.title or "گروه",
            bot_member=bot_member,
            bot_username=bot_info.username or "NoorBot"
        )
        try:
            await message.answer(text=text, reply_markup=kb, parse_mode="HTML")
            logger.info("Sent welcome message via new_chat_members to %s", message.chat.id)
        except Exception as e:
            logger.error("Failed to answer new_chat_members in %s: %s", message.chat.id, e)


@router.message(Command("start"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_start_group(message: Message):
    bot_info = await message.bot.get_me()
    try:
        bot_member = await message.bot.get_chat_member(chat_id=message.chat.id, user_id=bot_info.id)
    except Exception:
        bot_member = message.bot

    text, kb = build_smart_group_welcome(message.chat.title or "گروه", bot_member, bot_info.username)
    await message.answer(text=text, reply_markup=kb, parse_mode="HTML")


@router.message(Command("settings"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_settings_group(message: Message):
    is_admin = await _is_group_admin(message)
    if not is_admin:
        await message.reply("⚠️ تنها مدیران این گروه اجازه تغییر تنظیمات ربات را دارند.")
        return

    group = await GroupRepository.get_by_id(message.chat.id)
    if not group:
        group = await GroupRepository.upsert_group(
            chat_id=message.chat.id,
            title=message.chat.title,
            username=message.chat.username,
            chat_type=message.chat.type
        )

    text = (
        f"⚙️ <b>تنظیمات ربات در گروه «{html.escape(message.chat.title or '')}»</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "مدیر گرامی، می‌توانید قابلیت‌های مورد نظر را برای این گروه فعال یا غیرفعال فرمایید:"
    )
    await message.answer(text=text, reply_markup=get_group_settings_keyboard(group), parse_mode="HTML")


@router.callback_query(F.data.startswith("grp_toggle:"), F.message.chat.type.in_({"group", "supergroup"}))
async def cb_group_toggle(call: CallbackQuery):
    member = await call.bot.get_chat_member(chat_id=call.message.chat.id, user_id=call.from_user.id)
    if member.status not in ("creator", "administrator"):
        await call.answer("⚠️ شما مدیر این گروه نیستید.", show_alert=True)
        return

    group = await GroupRepository.get_by_id(call.message.chat.id)
    if not group:
        group = await GroupRepository.upsert_group(
            chat_id=call.message.chat.id,
            title=call.message.chat.title,
            username=call.message.chat.username,
            chat_type=call.message.chat.type
        )

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
async def cb_group_refresh(call: CallbackQuery):
    group = await GroupRepository.get_by_id(call.message.chat.id)
    if not group:
        group = await GroupRepository.upsert_group(
            chat_id=call.message.chat.id,
            title=call.message.chat.title,
            username=call.message.chat.username,
            chat_type=call.message.chat.type
        )
    await call.message.edit_reply_markup(reply_markup=get_group_settings_keyboard(group))
    await call.answer("🔄 به‌روز شد.")


@router.message(Command("istikhara"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_istikhara_group(message: Message):
    group = await GroupRepository.get_by_id(message.chat.id)
    if group and not group.allow_istikhara:
        await message.reply("⚠️ قابلیت استخاره توسط مدیران در این گروه غیرفعال شده است.")
        return

    bot_info = await message.bot.get_me()

    # در صورت فعال‌بودن حالت حریم خصوصی، ارسال نتیجه در پی‌وی کاربر انجام می‌شود
    if not group or group.private_result_mode:
        clean_user = bot_info.username.lstrip("@")
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔒 انجام و مشاهده استخاره در پی‌وی",
                        url=f"https://t.me/{clean_user}?start=istikhara"
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
    formatted = IstikharaService.format_istikhara_message(result, marja="sistani", tafsir="nemooneh")
    await message.reply(text=formatted, parse_mode="HTML")


@router.message(Command("ayah"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_ayah_group(message: Message):
    ayah = QuranService.get_daily_ayah()
    text = QuranService.format_daily_ayah_message(ayah)
    await message.answer(text=text, parse_mode="HTML")


@router.message(Command("daily"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_daily_group(message: Message):
    today_info = CalendarService.get_today_info()
    text = CalendarService.format_daily_content(today_info)
    await message.answer(text=text, parse_mode="HTML")

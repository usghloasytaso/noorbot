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
from bot.db.repository import GroupRepository, IstikharaRepository, StatsRepository, UserRepository
from bot.keyboards.group_kb import (
    get_group_marja_picker_kb,
    get_group_profile_kb,
    get_group_settings_keyboard,
    get_group_tafsir_picker_kb,
    get_group_tasbih_kb,
    get_user_group_istikhara_kb,
)
from bot.services.calendar_service import CalendarService
from bot.services.istikhara_service import IstikharaService
from bot.services.prayer_service import PrayerService
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
        "📌 <b>دستورات و کلمات کلیدی فعال در این گروه:</b>\n"
        "▫️ نوشتن کلمه <b>«استخاره»</b> یا <code>/istikhara</code> - استخاره با قرآن کریم متناسب با مرجع و تفسیر شما\n"
        "▫️ <code>/profile</code> یا نوشتن <b>«پروفایل»</b> - مشاهده و تغییر مرجع تقلید و تفسیر شما مستقیم در گروه\n"
        "▫️ <code>/ayah</code> یا نوشتن <b>«آیه»</b> - دریافت آیه نورانی روز به همراه ترجمه\n"
        "▫️ <code>/daily</code> یا نوشتن <b>«تقویم»</b> یا <b>«ذکر روز»</b> - تقویم روز، مناسبت‌های مذهبی و ذکر روز\n"
        "▫️ <code>/prayer</code> یا نوشتن <b>«اوقات شرعی»</b> - اوقات شرعی به افق شهرهای مختلف\n"
        "▫️ <code>/tasbih</code> یا نوشتن <b>«صلوات»</b> - تسبیح‌شمار و صلوات جمعی گروهی با دکمه تعاملی\n"
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

    # الف) اگر ربات از گروه خارج شد یا اخراج شد
    if new_status in ("left", "kicked"):
        try:
            await GroupRepository.set_active(event.chat.id, False)
        except Exception as e:
            logger.warning("Could not deactivate group %s: %s", event.chat.id, e)
        return

    # ب) اگر ربات از قبل عضو بود و حالا ارتقا یافته به ادمین
    if old_status == "member" and new_status in ("administrator", "creator"):
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
        return

    # ج) اگر ربات به هر ترتیبی در گروه حضور فعال پیدا کرد (عضو عادی یا ادمین اولیه)
    if new_status in ("member", "administrator"):
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
        bot_username = bot_user.username if bot_user and bot_user.username else None
        if not bot_username:
            try:
                me = await event.bot.get_me()
                bot_username = me.username
            except Exception:
                bot_username = "NoorReligious_bot"

        text, kb = build_smart_group_welcome(
            chat_title=event.chat.title or "گروه",
            bot_member=event.new_chat_member,
            bot_username=bot_username or "NoorReligious_bot"
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
            logger.error("Could not send welcome message to group %s: %s. Trying plain text fallback...", event.chat.id, e)
            try:
                plain_msg = (
                    f"🌸 سلام و درود بر اعضای محترم گروه {event.chat.title or ''}\n\n"
                    "من ربات جامع قرآنی و مذهبی نور (NoorBot) هستم.\n"
                    "برای استفاده از امکانات لطفا دستورات زیر را بفرستید:\n"
                    "/istikhara - استخاره با قرآن کریم\n"
                    "/ayah - آیه نورانی روز\n"
                    "/daily - تقویم و ذکر روز\n"
                    "/prayer - اوقات شرعی\n"
                    "/tasbih - تسبیح‌شمار هوشمند\n"
                    "/settings - تنظیمات گروه (مخصوص مدیران)"
                )
                await event.bot.send_message(chat_id=event.chat.id, text=plain_msg)
            except Exception as e2:
                logger.error("Plain text fallback failed: %s", e2)
        return


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
            bot_username=bot_info.username or "NoorReligious_bot"
        )
        try:
            await message.answer(text=text, reply_markup=kb, parse_mode="HTML")
            logger.info("Sent welcome message via new_chat_members to %s", message.chat.id)
        except Exception as e:
            logger.error("Failed to answer new_chat_members in %s: %s. Trying plain text...", message.chat.id, e)
            try:
                plain_msg = (
                    f"🌸 سلام و درود بر اعضای محترم گروه {message.chat.title or ''}\n\n"
                    "من ربات جامع قرآنی و مذهبی نور (NoorBot) هستم.\n"
                    "/istikhara - استخاره با قرآن کریم\n"
                    "/ayah - آیه نورانی روز\n"
                    "/daily - تقویم و ذکر روز\n"
                    "/prayer - اوقات شرعی\n"
                    "/tasbih - تسبیح‌شمار هوشمند\n"
                    "/settings - تنظیمات گروه (مخصوص مدیران)"
                )
                await message.answer(text=plain_msg)
            except Exception as e2:
                logger.error("Plain fallback failed: %s", e2)


@router.message(Command("start"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_start_group(message: Message):
    bot_info = await message.bot.get_me()
    try:
        bot_member = await message.bot.get_chat_member(chat_id=message.chat.id, user_id=bot_info.id)
    except Exception:
        bot_member = message.bot

    text, kb = build_smart_group_welcome(message.chat.title or "گروه", bot_member, bot_info.username or "NoorReligious_bot")
    try:
        await message.answer(text=text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        plain_msg = (
            f"🌸 سلام و درود بر اعضای محترم گروه {message.chat.title or ''}\n\n"
            "من ربات جامع قرآنی و مذهبی نور (NoorBot) هستم.\n"
            "/istikhara - استخاره با قرآن کریم\n"
            "/ayah - آیه نورانی روز\n"
            "/daily - تقویم و ذکر روز\n"
            "/prayer - اوقات شرعی\n"
            "/tasbih - تسبیح‌شمار هوشمند\n"
            "/settings - تنظیمات گروه (مخصوص مدیران)"
        )
        await message.answer(text=plain_msg)


@router.message(Command("help"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_help_group(message: Message):
    bot_info = await message.bot.get_me()
    try:
        bot_member = await message.bot.get_chat_member(chat_id=message.chat.id, user_id=bot_info.id)
    except Exception:
        bot_member = message.bot

    text, kb = build_smart_group_welcome(message.chat.title or "گروه", bot_member, bot_info.username or "NoorReligious_bot")
    try:
        await message.answer(text=text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        plain_msg = (
            f"🌸 راهنمای دستورات ربات نور در گروه {message.chat.title or ''}:\n\n"
            "/istikhara - استخاره با قرآن کریم\n"
            "/ayah - آیه نورانی روز\n"
            "/daily - تقویم و ذکر روز\n"
            "/prayer - اوقات شرعی\n"
            "/tasbih - تسبیح‌شمار هوشمند\n"
            "/settings - تنظیمات گروه (مخصوص مدیران)"
        )
        await message.answer(text=plain_msg)


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


# ۳. استخاره هوشمند در گروه (دستور /istikhara یا ارسال متن «استخاره»)
@router.message(Command("istikhara", "estekhare"), F.chat.type.in_({"group", "supergroup"}))
@router.message(F.text.func(lambda t: t and "استخاره" in t), F.chat.type.in_({"group", "supergroup"}))
async def handle_group_istikhara(message: Message):
    group = await GroupRepository.get_by_id(message.chat.id)
    if group and not group.allow_istikhara:
        await message.reply("⚠️ قابلیت استخاره توسط مدیران در این گروه غیرفعال شده است.")
        return

    user_id = message.from_user.id
    user = await UserRepository.get_by_id(user_id)
    if not user:
        try:
            user = await UserRepository.upsert_user(
                telegram_id=user_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                language_code=message.from_user.language_code or "fa"
            )
        except Exception:
            user = User(telegram_id=user_id, username=message.from_user.username, first_name=message.from_user.first_name)

    marja = user.selected_marja or "sistani"
    tafsir = user.selected_tafsir or "nemooneh"

    marja_titles = {
        "sistani": "آیت‌الله سیستانی",
        "khamenei": "رهبر انقلاب",
        "makarem": "آیت‌الله مکارم"
    }
    tafsir_titles = {
        "nemooneh": "تفسیر نمونه",
        "al-mizan": "تفسیر المیزان",
        "majma-al-bayan": "مجمع‌البیان"
    }
    m_name = marja_titles.get(marja, "آیت‌الله سیستانی")
    t_name = tafsir_titles.get(tafsir, "تفسیر نمونه")

    # انجام استخاره معتبر شیعه بر مبنای مصحف عثمانی ۶۰۴ صفحه‌ای
    result = IstikharaService.perform_istikhara()
    try:
        await IstikharaRepository.add_record(
            telegram_id=user_id,
            surah_number=result.get("surah_number", 1),
            surah_name=result.get("surah_name", "قرآن"),
            ayah_number=result.get("ayah_number", 1),
            page_number=result.get("page", 1),
            result_code=result.get("result_code", "good"),
            result_title=result.get("result_title", ""),
            intent_topic=f"استخاره در گروه {message.chat.title or ''}"
        )
        await StatsRepository.increment("total_istikharas")
    except Exception as e:
        logger.warning("Failed to record istikhara in group: %s", e)

    formatted = IstikharaService.format_istikhara_message(result, marja=marja, tafsir=tafsir)
    header = (
        f"👤 <b>استخاره اختصاصی برای {message.from_user.mention_html()}</b>\n"
        f"▫️ <b>مرجع:</b> {m_name} | <b>تفسیر:</b> {t_name}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
    )
    full_text = header + formatted

    bot_info = await message.bot.get_me()
    kb = get_user_group_istikhara_kb(
        user_id=user_id,
        marja=marja,
        tafsir=tafsir,
        bot_username=bot_info.username or "NoorReligious_bot"
    )

    try:
        await message.reply(text=full_text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        logger.error("Failed to reply istikhara in group: %s", e)
        try:
            await message.reply(
                text=f"استخاره برای {message.from_user.full_name}:\n\nنتیجه: {result.get('result_title')}\nسوره: {result.get('surah_name')}\nآیه: {result.get('ayah_number')}\n\n«{result.get('translation')}»"
            )
        except Exception:
            pass


# ۴. مدیریت دکمه‌های استخاره و تغییر مرجع/تفسیر در گروه
@router.callback_query(F.data.startswith("grp_m_menu:"), F.message.chat.type.in_({"group", "supergroup"}))
async def cb_grp_marja_menu(call: CallbackQuery):
    target_id = int(call.data.split(":")[1])
    if call.from_user.id != target_id:
        await call.answer("⚠️ این دکمه فقط مخصوص صاحب استخاره است. برای خودتان کلمه «استخاره» را بنویسید.", show_alert=True)
        return
    user = await UserRepository.get_by_id(target_id)
    current_m = user.selected_marja if user else "sistani"
    kb = get_group_marja_picker_kb(target_id, current_m)
    await call.message.edit_reply_markup(reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("grp_set_m:"), F.message.chat.type.in_({"group", "supergroup"}))
async def cb_grp_set_marja(call: CallbackQuery):
    parts = call.data.split(":")
    target_id = int(parts[1])
    new_marja = parts[2]
    if call.from_user.id != target_id:
        await call.answer("⚠️ این دکمه فقط مخصوص صاحب استخاره است.", show_alert=True)
        return

    await UserRepository.update_marja(target_id, new_marja)
    marja_names = {"sistani": "آیت‌الله سیستانی", "khamenei": "رهبر معظم انقلاب", "makarem": "آیت‌الله مکارم شیرازی"}
    name = marja_names.get(new_marja, new_marja)

    bot_info = await call.bot.get_me()
    user = await UserRepository.get_by_id(target_id)
    tafsir = user.selected_tafsir if user else "nemooneh"
    kb = get_user_group_istikhara_kb(target_id, new_marja, tafsir, bot_info.username or "NoorReligious_bot")
    await call.message.edit_reply_markup(reply_markup=kb)
    await call.answer(f"✅ مرجع تقلید شما به «{name}» تغییر یافت و ذخیره شد.", show_alert=True)


@router.callback_query(F.data.startswith("grp_t_menu:"), F.message.chat.type.in_({"group", "supergroup"}))
async def cb_grp_tafsir_menu(call: CallbackQuery):
    target_id = int(call.data.split(":")[1])
    if call.from_user.id != target_id:
        await call.answer("⚠️ این دکمه فقط مخصوص صاحب استخاره است.", show_alert=True)
        return
    user = await UserRepository.get_by_id(target_id)
    current_t = user.selected_tafsir if user else "nemooneh"
    kb = get_group_tafsir_picker_kb(target_id, current_t)
    await call.message.edit_reply_markup(reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("grp_set_t:"), F.message.chat.type.in_({"group", "supergroup"}))
async def cb_grp_set_tafsir(call: CallbackQuery):
    parts = call.data.split(":")
    target_id = int(parts[1])
    new_tafsir = parts[2]
    if call.from_user.id != target_id:
        await call.answer("⚠️ این دکمه فقط مخصوص صاحب استخاره است.", show_alert=True)
        return

    await UserRepository.update_tafsir(target_id, new_tafsir)
    tafsir_names = {"nemooneh": "تفسیر نمونه", "al-mizan": "تفسیر المیزان", "majma-al-bayan": "مجمع‌البیان"}
    name = tafsir_names.get(new_tafsir, new_tafsir)

    bot_info = await call.bot.get_me()
    user = await UserRepository.get_by_id(target_id)
    marja = user.selected_marja if user else "sistani"
    kb = get_user_group_istikhara_kb(target_id, marja, new_tafsir, bot_info.username or "NoorReligious_bot")
    await call.message.edit_reply_markup(reply_markup=kb)
    await call.answer(f"✅ تفسیر شما به «{name}» تغییر یافت و ذخیره شد.", show_alert=True)


@router.callback_query(F.data.startswith("grp_back_ist:"), F.message.chat.type.in_({"group", "supergroup"}))
async def cb_grp_back_istikhara(call: CallbackQuery):
    target_id = int(call.data.split(":")[1])
    user = await UserRepository.get_by_id(target_id)
    marja = user.selected_marja if user else "sistani"
    tafsir = user.selected_tafsir if user else "nemooneh"
    bot_info = await call.bot.get_me()
    kb = get_user_group_istikhara_kb(target_id, marja, tafsir, bot_info.username or "NoorReligious_bot")
    await call.message.edit_reply_markup(reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("grp_reist:"), F.message.chat.type.in_({"group", "supergroup"}))
async def cb_grp_reistikhara(call: CallbackQuery):
    target_id = int(call.data.split(":")[1])
    if call.from_user.id != target_id:
        await call.answer("⚠️ این استخاره برای کاربر دیگری است. جهت دریافت استخاره خودتان، کلمه «استخاره» را بنویسید.", show_alert=True)
        return

    user = await UserRepository.get_by_id(target_id)
    marja = user.selected_marja if user else "sistani"
    tafsir = user.selected_tafsir if user else "nemooneh"

    marja_titles = {"sistani": "آیت‌الله سیستانی", "khamenei": "رهبر انقلاب", "makarem": "آیت‌الله مکارم"}
    tafsir_titles = {"nemooneh": "تفسیر نمونه", "al-mizan": "تفسیر المیزان", "majma-al-bayan": "مجمع‌البیان"}
    m_name = marja_titles.get(marja, "آیت‌الله سیستانی")
    t_name = tafsir_titles.get(tafsir, "تفسیر نمونه")

    result = IstikharaService.perform_istikhara()
    try:
        await IstikharaRepository.add_record(
            telegram_id=target_id,
            surah_number=result.get("surah_number", 1),
            surah_name=result.get("surah_name", "قرآن"),
            ayah_number=result.get("ayah_number", 1),
            page_number=result.get("page", 1),
            result_code=result.get("result_code", "good"),
            result_title=result.get("result_title", ""),
            intent_topic="استخاره مجدد در گروه"
        )
    except Exception:
        pass

    formatted = IstikharaService.format_istikhara_message(result, marja=marja, tafsir=tafsir)
    header = (
        f"👤 <b>استخاره مجدد برای {call.from_user.mention_html()}</b>\n"
        f"▫️ <b>مرجع:</b> {m_name} | <b>تفسیر:</b> {t_name}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
    )
    full_text = header + formatted

    bot_info = await call.bot.get_me()
    kb = get_user_group_istikhara_kb(target_id, marja, tafsir, bot_info.username or "NoorReligious_bot")
    try:
        await call.message.edit_text(text=full_text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await call.answer("🔄 استخاره جدید با موفقیت محاسبه شد.")


# ۵. پروفایل و تنظیمات فقهی کاربر مستقیم در گروه
@router.message(Command("profile", "myprofile"), F.chat.type.in_({"group", "supergroup"}))
@router.message(F.text.in_({"پروفایل", "پروفایل من"}), F.chat.type.in_({"group", "supergroup"}))
async def cmd_grp_profile(message: Message):
    user_id = message.from_user.id
    user = await UserRepository.get_by_id(user_id)
    if not user:
        try:
            user = await UserRepository.upsert_user(
                telegram_id=user_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
        except Exception:
            user = User(telegram_id=user_id, username=message.from_user.username, first_name=message.from_user.first_name)

    marja_names = {"sistani": "آیت‌الله سیستانی", "khamenei": "رهبر انقلاب", "makarem": "آیت‌الله مکارم"}
    tafsir_names = {"nemooneh": "تفسیر نمونه", "al-mizan": "تفسیر المیزان", "majma-al-bayan": "مجمع‌البیان"}
    m_name = marja_names.get(user.selected_marja, "آیت‌الله سیستانی")
    t_name = tafsir_names.get(user.selected_tafsir, "تفسیر نمونه")

    text = (
        f"👤 <b>پروفایل مذهبی شما در ربات نور:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"▫️ <b>نام:</b> {html.escape(message.from_user.full_name)}\n"
        f"▫️ <b>مرجع تقلید شما در استخاره:</b> 🟢 <b>{m_name}</b>\n"
        f"▫️ <b>تفسیر قرآن منتخب:</b> 📚 <b>{t_name}</b>\n"
        f"▫️ <b>شهر انتخابی اوقات شرعی:</b> 🕌 <b>{user.city}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<i>استخاره‌هایی که در این گروه یا پی‌وی می‌گیرید، بر اساس این مرجع و تفسیر شخصی شما محاسبه می‌شوند. با دکمه‌های زیر می‌توانید آن‌ها را تغییر دهید:</i>"
    )
    bot_info = await message.bot.get_me()
    kb = get_group_profile_kb(user_id, user.selected_marja, user.selected_tafsir, bot_info.username or "NoorReligious_bot")
    await message.reply(text=text, reply_markup=kb, parse_mode="HTML")


# ۶. صلوات‌شمار و تسبیح جمعی گروهی
@router.message(Command("tasbih", "salawat"), F.chat.type.in_({"group", "supergroup"}))
@router.message(F.text.in_({"صلوات", "تسبیح"}), F.chat.type.in_({"group", "supergroup"}))
async def cmd_grp_tasbih(message: Message):
    text = (
        "📿 <b>تسبیح‌شمار و صلوات جمعی در گروه</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✨ <i>اللّهُمَّ صَلِّ عَلی مُحَمَّدٍ وَ آلِ مُحَمَّدٍ وَ عَجِّلْ فَرَجَهُمْ</i> ✨\n\n"
        "▫️ <b>شمارش صلوات‌های ثبت‌شده:</b> <code>0</code>\n"
        "▫️ هر یک از اعضای محترم گروه می‌توانند با لمس دکمه زیر صلوات خود را ثبت نمایند."
    )
    await message.answer(text=text, reply_markup=get_group_tasbih_kb(0), parse_mode="HTML")


@router.callback_query(F.data.startswith("grp_salawat:"), F.message.chat.type.in_({"group", "supergroup"}))
async def cb_grp_salawat_increment(call: CallbackQuery):
    current_count = int(call.data.split(":")[1])
    new_count = current_count + 1

    text = (
        "📿 <b>تسبیح‌شمار و صلوات جمعی در گروه</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✨ <i>اللّهُمَّ صَلِّ عَلی مُحَمَّدٍ وَ آلِ مُحَمَّدٍ وَ عَجِّلْ فَرَجَهُمْ</i> ✨\n\n"
        f"▫️ <b>شمارش صلوات‌های ثبت‌شده:</b> <code>{new_count:,}</code>\n"
        f"▫️ آخرین صلوات توسط: {call.from_user.mention_html()}\n"
        "🤲 <i>طاعات و عبادات شما قبول درگاه حق.</i>"
    )
    try:
        await call.message.edit_text(text=text, reply_markup=get_group_tasbih_kb(new_count), parse_mode="HTML")
    except Exception:
        pass
    await call.answer("📿 صلوات شما ثبت شد. التماس دعا!")


@router.callback_query(F.data == "grp_salawat_reset", F.message.chat.type.in_({"group", "supergroup"}))
async def cb_grp_salawat_reset(call: CallbackQuery):
    is_admin = False
    try:
        member = await call.bot.get_chat_member(chat_id=call.message.chat.id, user_id=call.from_user.id)
        is_admin = member.status in ("creator", "administrator")
    except Exception:
        pass

    if not is_admin:
        await call.answer("⚠️ تنها مدیران گروه می‌توانند شمارنده را ریست کنند.", show_alert=True)
        return

    text = (
        "📿 <b>تسبیح‌شمار و صلوات جمعی در گروه (بازنشانی شد)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✨ <i>اللّهُمَّ صَلِّ عَلی مُحَمَّدٍ وَ آلِ مُحَمَّدٍ وَ عَجِّلْ فَرَجَهُمْ</i> ✨\n\n"
        "▫️ <b>شمارش صلوات‌های ثبت‌شده:</b> <code>0</code>\n"
    )
    await call.message.edit_text(text=text, reply_markup=get_group_tasbih_kb(0), parse_mode="HTML")
    await call.answer("🔄 شمارنده توسط مدیر بازنشانی شد.")


# ۷. دستورات و کلمات کلیدی مذهبی (آیه روز، تقویم و اوقات شرعی)
@router.message(Command("ayah"), F.chat.type.in_({"group", "supergroup"}))
@router.message(F.text.in_({"آیه", "آیه روز", "ایه"}), F.chat.type.in_({"group", "supergroup"}))
async def cmd_ayah_group(message: Message):
    ayah = QuranService.get_daily_ayah()
    text = QuranService.format_daily_ayah_message(ayah)
    await message.reply(text=text, parse_mode="HTML")


@router.message(Command("daily"), F.chat.type.in_({"group", "supergroup"}))
@router.message(F.text.in_({"تقویم", "ذکر روز", "مناسبت", "امروز"}), F.chat.type.in_({"group", "supergroup"}))
async def cmd_daily_group(message: Message):
    today_info = CalendarService.get_today_info()
    text = CalendarService.format_daily_content(today_info)
    await message.reply(text=text, parse_mode="HTML")


@router.message(Command("prayer", "azan"), F.chat.type.in_({"group", "supergroup"}))
@router.message(F.text.in_({"اوقات شرعی", "اذان"}), F.chat.type.in_({"group", "supergroup"}))
async def cmd_prayer_group(message: Message):
    user = await UserRepository.get_by_id(message.from_user.id)
    city = user.city if user else "تهران"
    method = user.prayer_method if user else "tehran"
    times = PrayerService.calculate_times(city_name=city, method=method)
    text = PrayerService.format_prayer_message(times)
    await message.reply(text=text, parse_mode="HTML")


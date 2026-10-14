"""
هندلرهای اختصاصی پنل مدیریت (Admin Panel)، آمار و ارسال پیام همگانی با تایید صریح
"""

import time
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot import __version__
from bot.config import settings
from bot.db.base import db
from bot.db.repository import GroupRepository, StatsRepository, UserRepository
from bot.keyboards.admin_kb import get_admin_panel_kb, get_broadcast_confirm_kb
from bot.middlewares.admin_check import AdminFilter
from bot.services.broadcast_service import BroadcastService
from bot.web.health import START_TIME

router = Router(name="admin_handler")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


class BroadcastStates(StatesGroup):
    waiting_for_text = State()
    confirm_broadcast = State()


@router.message(Command("admin"))
async def cmd_admin_panel(message: Message):
    text = (
        "🔐 <b>به پنل مدیریت ربات نور (NoorBot) خوش آمدید</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"▫️ نسخه ربات: <code>v{__version__}</code>\n"
        f"▫️ محیط استقرار: <code>{settings.environment}</code>\n"
        f"▫️ شناسه شما: <code>{message.from_user.id}</code>\n\n"
        "یکی از عملیات‌های زیر را انتخاب نمایید:"
    )
    await message.answer(text=text, reply_markup=get_admin_panel_kb(), parse_mode="HTML")


@router.callback_query(F.data == "admin:stats")
async def cb_admin_stats(call: CallbackQuery):
    stats = await StatsRepository.get_all_stats()
    user_count = await UserRepository.count_users()
    group_count = await GroupRepository.count_groups()

    text = (
        "📊 <b>آمار تفصیلی سامانه نور</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>کل کاربران ثبت‌شده:</b> {user_count:,}\n"
        f"👥 <b>گروه‌های فعال:</b> {group_count:,}\n"
        f"📖 <b>کل استخاره‌های انجام‌شده:</b> {stats.get('total_istikharas', 0):,}\n"
        f"📿 <b>کل دفعات ذکر تسبیح:</b> {stats.get('total_tasbih_counts', 0):,}\n"
        f"🔍 <b>کل جستجوهای قرآنی:</b> {stats.get('total_quran_searches', 0):,}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    await call.message.edit_text(text=text, reply_markup=get_admin_panel_kb(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "admin:health")
async def cb_admin_health(call: CallbackQuery):
    db_health = await db.health_check()
    uptime_sec = int(time.time() - START_TIME)
    hours, rem = divmod(uptime_sec, 3600)
    minutes, seconds = divmod(rem, 60)

    db_status = "🟢 متصل و سالم" if db_health.get("connected") else "🔴 قطع ارتباط"

    text = (
        "🩺 <b>وضعیت زنده سرور و منابع (Health Status)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <b>مدت فعالیت مداوم (Uptime):</b> {hours} ساعت و {minutes} دقیقه\n"
        f"💾 <b>موتور پایگاه داده:</b> {db_health.get('engine', 'نامشخص')}\n"
        f"🔌 <b>وضعیت اتصال دیتابیس:</b> {db_status}\n"
        f"🌐 <b>پورت سرور وب سلامت:</b> <code>{settings.port}</code>\n"
        f"🌍 <b>آدرس وب‌سرویس:</b> <code>http://0.0.0.0:{settings.port}/health</code>\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    await call.message.edit_text(text=text, reply_markup=get_admin_panel_kb(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "admin:broadcast_users")
async def start_broadcast_users(call: CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastStates.waiting_for_text)
    await state.update_data(target="users")
    await call.message.edit_text(
        text=(
            "📢 <b>ارسال پیام همگانی به کاربران</b>\n\n"
            "لطفاً متن پیامی را که می‌خواهید برای تمام کاربران ارسال شود بفرستید.\n"
            "<i>(می‌توانید از تگ‌های فرمت‌بندی HTML استفاده کنید)</i>"
        ),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "admin:broadcast_groups")
async def start_broadcast_groups(call: CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastStates.waiting_for_text)
    await state.update_data(target="groups")
    await call.message.edit_text(
        text=(
            "👥 <b>ارسال پیام همگانی به گروه‌ها</b>\n\n"
            "لطفاً متن پیامی را که می‌خواهید در تمام گروه‌های ثبت‌شده فرستاده شود ارسال فرمایید:"
        ),
        parse_mode="HTML"
    )
    await call.answer()


@router.message(BroadcastStates.waiting_for_text)
async def receive_broadcast_text(message: Message, state: FSMContext):
    text = message.html_text or message.text
    data = await state.get_data()
    target = data.get("target", "users")
    target_fa = "کاربران" if target == "users" else "گروه‌ها"

    count = await UserRepository.count_users() if target == "users" else await GroupRepository.count_groups()

    await state.update_data(broadcast_text=text)
    await state.set_state(BroadcastStates.confirm_broadcast)

    preview = (
        f"⚠️ <b>پیش‌نمایش پیام همگانی ({target_fa}):</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{text}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>تعداد گیرندگان تخمینی:</b> {count:,}\n\n"
        "❓ آیا از ارسال این پیام به تمام گیرندگان اطمینان کامل دارید؟"
    )
    await message.answer(text=preview, reply_markup=get_broadcast_confirm_kb(target), parse_mode="HTML")


@router.callback_query(F.data.startswith("bcast_confirm:"), BroadcastStates.confirm_broadcast)
async def confirm_broadcast(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = data.get("broadcast_text", "")
    target = data.get("target", "users")
    await state.clear()

    await call.message.edit_text("⏳ در حال ارسال پیام همگانی... لطفاً شکیبا باشید.", parse_mode="HTML")

    if target == "users":
        res = await BroadcastService.broadcast_to_users(bot=call.bot, text=text)
        report = (
            "✅ <b>ارسال همگانی به کاربران با موفقیت خاتمه یافت:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"▫️ کل مخاطبان: {res['total']:,}\n"
            f"▫️ ارسال موفق: {res['sent']:,}\n"
            f"▫️ مسدود/حذف‌شده: {res['blocked']:,}\n"
            f"▫️ خطای شبکه: {res['failed']:,}"
        )
    else:
        res = await BroadcastService.broadcast_to_groups(bot=call.bot, text=text)
        report = (
            "✅ <b>ارسال همگانی به گروه‌ها خاتمه یافت:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"▫️ کل گروه‌ها: {res['total']:,}\n"
            f"▫️ ارسال موفق: {res['sent']:,}\n"
            f"▫️ ناموفق: {res['failed']:,}"
        )

    await call.message.edit_text(text=report, reply_markup=get_admin_panel_kb(), parse_mode="HTML")
    await call.answer("عملیات پایان یافت.")


@router.callback_query(F.data == "bcast_cancel")
async def cancel_broadcast(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ ارسال همگانی لغو گردید.", reply_markup=get_admin_panel_kb(), parse_mode="HTML")
    await call.answer("ارسال لغو شد.")

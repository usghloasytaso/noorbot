"""
هندلرهای تسبیح‌شمار هوشمند و تعاملی
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.db.models import User
from bot.db.repository import TasbihRepository
from bot.keyboards.tasbih_kb import get_tasbih_keyboard

router = Router(name="tasbih_handler")

PRESETS_INFO = {
    "zahra": {
        "title": "تسبیحات حضرت فاطمه زهرا (سلام‌الله‌علیها)",
        "target": 100,
        "stages": [
            {"name": "الله اکبر", "limit": 34, "arabic": "اللَّهُ أَكْبَرُ"},
            {"name": "الحمد لله", "limit": 67, "arabic": "الْحَمْدُ لِلَّهِ"},
            {"name": "سبحان الله", "limit": 100, "arabic": "سُبْحَانَ اللَّهِ"}
        ]
    },
    "salawat": {
        "title": "صلوات بر محمد و آل محمد (صلی‌الله‌علیه‌وآله)",
        "target": 100,
        "arabic": "اللَّهُمَّ صَلِّ عَلَى مُحَمَّدٍ وَ آلِ مُحَمَّدٍ وَ عَجِّلْ فَرَجَهُمْ"
    },
    "istighfar": {
        "title": "استغفار و طلب مغفرت",
        "target": 70,
        "arabic": "أَسْتَغْفِرُ اللَّهَ رَبِّي وَ أَتُوبُ إِلَيْهِ"
    },
    "yunusiya": {
        "title": "ذکر شریف یونسیه",
        "target": 40,
        "arabic": "لَا إِلَهَ إِلَّا أَنْتَ سُبْحَانَكَ إِنِّي كُنْتُ مِنَ الظَّالِمِينَ"
    }
}


def _render_progress_bar(count: int, target: int, length: int = 10) -> str:
    target = max(1, target)
    ratio = min(1.0, count / target)
    filled = int(ratio * length)
    empty = length - filled
    percent = int(ratio * 100)
    return f"[{'🟩' * filled}{'⬜' * empty}] {percent}%"


def _format_tasbih_text(preset_id: str, count: int) -> str:
    info = PRESETS_INFO.get(preset_id, PRESETS_INFO["salawat"])
    target = info["target"]
    progress = _render_progress_bar(count, target)

    if preset_id == "zahra":
        # تعیین مرحله فعلی تسبیحات حضرت زهرا (س)
        if count < 34:
            current_stage = "۳۴ مرتبه: «اللَّهُ أَكْبَرُ»"
            current_arabic = "اللَّهُ أَكْبَرُ"
            step_count = count
            step_max = 34
        elif count < 67:
            current_stage = "۳۳ مرتبه: «الْحَمْدُ لِلَّهِ»"
            current_arabic = "الْحَمْدُ لِلَّهِ"
            step_count = count - 34
            step_max = 33
        else:
            current_stage = "۳۳ مرتبه: «سُبْحَانَ اللَّهِ»"
            current_arabic = "سُبْحَانَ اللَّهِ"
            step_count = count - 67
            step_max = 33

        completion_note = "🎉 <b>تسبیحات کامل شد! تقبل الله.</b>" if count >= 100 else ""
        return (
            f"📿 <b>{info['title']}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 <b>مرحله فعلی:</b> {current_stage}\n"
            f"✨ <b>ذکر:</b> <code>{current_arabic}</code>\n"
            f"🔢 <b>شمارش مرحله:</b> {step_count} از {step_max}\n"
            f"📊 <b>مجموع شمارش:</b> <b>{count}</b> از {target}\n"
            f"📈 <b>پیشرفت:</b> {progress}\n\n"
            f"{completion_note}"
            "<i>با فشردن دکمه (+1) زیر، شمارش را ادامه دهید:</i>"
        )

    completion_note = "🎉 <b>دور شمارش تکمیل شد! تقبل الله.</b>\n" if count >= target else ""
    return (
        f"📿 <b>{info['title']}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ <b>ذکر:</b> <code>{info['arabic']}</code>\n"
        f"🔢 <b>تعداد شمارش:</b> <b>{count}</b> از {target}\n"
        f"📈 <b>پیشرفت:</b> {progress}\n\n"
        f"{completion_note}"
        "<i>با فشردن دکمه (+1) زیر، شمارش را ادامه دهید:</i>"
    )


@router.message(Command("tasbih"))
@router.message(F.text == "📿 تسبیح‌شمار تعاملی")
@router.callback_query(F.data == "menu:tasbih")
async def show_tasbih(event: Message | CallbackQuery, user: User):
    preset_id = "zahra"
    count = await TasbihRepository.get_count(user.telegram_id, preset_id)
    text = _format_tasbih_text(preset_id, count)
    kb = get_tasbih_keyboard(preset_id, count, PRESETS_INFO[preset_id]["target"])

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text=text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("tasbih:inc:"))
async def tasbih_increment(call: CallbackQuery, user: User):
    preset_id = call.data.split(":")[2]
    new_count = await TasbihRepository.increment_count(user.telegram_id, preset_id, 1)
    text = _format_tasbih_text(preset_id, new_count)
    info = PRESETS_INFO.get(preset_id, PRESETS_INFO["salawat"])
    kb = get_tasbih_keyboard(preset_id, new_count, info["target"])

    try:
        await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await call.answer(f"➕ {new_count}")


@router.callback_query(F.data.startswith("tasbih:dec:"))
async def tasbih_decrement(call: CallbackQuery, user: User):
    preset_id = call.data.split(":")[2]
    new_count = await TasbihRepository.increment_count(user.telegram_id, preset_id, -1)
    text = _format_tasbih_text(preset_id, new_count)
    info = PRESETS_INFO.get(preset_id, PRESETS_INFO["salawat"])
    kb = get_tasbih_keyboard(preset_id, new_count, info["target"])

    try:
        await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await call.answer(f"➖ {new_count}")


@router.callback_query(F.data.startswith("tasbih:reset:"))
async def tasbih_reset(call: CallbackQuery, user: User):
    preset_id = call.data.split(":")[2]
    await TasbihRepository.reset_count(user.telegram_id, preset_id)
    text = _format_tasbih_text(preset_id, 0)
    info = PRESETS_INFO.get(preset_id, PRESETS_INFO["salawat"])
    kb = get_tasbih_keyboard(preset_id, 0, info["target"])

    try:
        await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await call.answer("🔄 شمارش صفر شد.")


@router.callback_query(F.data.startswith("tasbih:preset:"))
async def tasbih_switch_preset(call: CallbackQuery, user: User):
    preset_id = call.data.split(":")[2]
    count = await TasbihRepository.get_count(user.telegram_id, preset_id)
    text = _format_tasbih_text(preset_id, count)
    info = PRESETS_INFO.get(preset_id, PRESETS_INFO["salawat"])
    kb = get_tasbih_keyboard(preset_id, count, info["target"])

    await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    await call.answer()

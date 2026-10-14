"""
هندلرهای مربوط به احکام شرعی، استفتائات و فتاوای مراجع تقلید
"""

import json
from pathlib import Path
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.db.models import User

router = Router(name="ahkam_handler")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_ahkam_data():
    with open(DATA_DIR / "ahkam.json", "r", encoding="utf-8") as f:
        return json.load(f)


@router.message(F.text == "📜 احکام و مراجع")
@router.callback_query(F.data == "menu:ahkam")
async def show_ahkam_menu(event: Message | CallbackQuery, user: User):
    data = _load_ahkam_data()
    topics = data.get("topics", [])

    text = (
        "📜 <b>پرسش‌ها و احکام مستند فقهی</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"مرجع تقلید فعلی شما: <b>{user.selected_marja}</b>\n"
        "لطفاً موضوع مورد نظر را جهت مشاهده استفتائات معتبر انتخاب فرمایید:"
    )

    buttons = []
    for t in topics:
        buttons.append([InlineKeyboardButton(text=f"📌 {t['title']}", callback_data=f"ahkam:topic:{t['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="menu:main")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text=text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("ahkam:topic:"))
async def show_topic_questions(call: CallbackQuery, user: User):
    topic_id = call.data.split(":")[2]
    data = _load_ahkam_data()
    topic = next((t for t in data.get("topics", []) if t["id"] == topic_id), None)

    if not topic:
        await call.answer("موضوع یافت نشد.", show_alert=True)
        return

    text = f"📌 <b>پرسش‌های موضوع: {topic['title']}</b>\n━━━━━━━━━━━━━━━━━━━━\nیکی از پرسش‌ها را انتخاب کنید:"
    buttons = []
    for q in topic.get("questions", []):
        buttons.append([InlineKeyboardButton(text=f"❓ {q['question'][:40]}...", callback_data=f"ahkam:q:{topic_id}:{q['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت به مباحث احکام", callback_data="menu:ahkam")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("ahkam:q:"))
async def show_question_answer(call: CallbackQuery, user: User):
    parts = call.data.split(":")
    topic_id = parts[2]
    q_id = parts[3]
    data = _load_ahkam_data()
    topic = next((t for t in data.get("topics", []) if t["id"] == topic_id), None)
    if not topic:
        await call.answer("موضوع یافت نشد.", show_alert=True)
        return

    q = next((item for item in topic.get("questions", []) if item["id"] == q_id), None)
    if not q:
        await call.answer("پرسش یافت نشد.", show_alert=True)
        return

    marja_key = user.selected_marja if user.selected_marja in q["answers"] else "sistani"
    marja_names = {
        "sistani": "حضرت آیت‌الله العظمی سیستانی",
        "khamenei": "حضرت آیت‌الله العظمی خامنه‌ای",
        "makarem": "حضرت آیت‌الله العظمی مکارم شیرازی"
    }

    ans = q["answers"].get(marja_key, "")
    src = q["sources"].get(marja_key, "")

    text = (
        f"❓ <b>پرسش:</b>\n{q['question']}\n\n"
        f"⚖️ <b>فتوای {marja_names.get(marja_key, marja_key)}:</b>\n"
        f"{ans}\n\n"
        f"📚 <b>مأخذ فقهی:</b> {src}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<i>برای مشاهده نظر سایر مراجع می‌توانید مرجع خود را در تنظیمات تغییر دهید.</i>"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 بازگشت به پرسش‌ها", callback_data=f"ahkam:topic:{topic_id}")],
            [InlineKeyboardButton(text="🔙 منوی اصلی", callback_data="menu:main")]
        ]
    )
    await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    await call.answer()

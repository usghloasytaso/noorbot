"""
تست‌های خودکار منطق استخاره، احکام مراجع، و ذخیره تاریخچه
"""

import pytest
from bot.db.repository import IstikharaRepository, UserRepository
from bot.services.istikhara_service import IstikharaService


def test_verified_pages():
    """بررسی صفحات ثبت‌شده معتبر (مانند صفحه ۱، ۲، ۷۱، ۱۸۷ و ۶۰۴)"""
    res1 = IstikharaService.perform_istikhara(1)
    assert res1["is_verified"] is True
    assert res1["surah_name"] == "الفاتحة"
    assert res1["result_code"] == "very_good"
    assert "توکل" in res1["advice"]

    res187 = IstikharaService.perform_istikhara(187)
    assert res187["is_verified"] is True
    assert res187["surah_name"] == "التوبة"
    assert res187["result_code"] == "very_bad"

    res71 = IstikharaService.perform_istikhara(71)
    assert res71["is_verified"] is True
    assert res71["surah_name"] == "آل عمران"
    assert res71["result_code"] == "very_good"


def test_unmapped_page_fallback():
    """بررسی عدم جعل نتیجه در صورت عدم دسترسی به تطبیق مستند یک صفحه"""
    res = IstikharaService.perform_istikhara(333)
    assert res["is_verified"] is False
    assert len(res["arabic_text"]) > 0
    assert len(res["translation"]) > 0
    assert "تدبر" in res["result_title"] or "مشورت" in res["result_title"]


def test_random_istikhara():
    """بررسی اجرای استخاره تصادفی با بازگشت داده‌های استاندارد"""
    res = IstikharaService.perform_istikhara()
    assert 1 <= res["page"] <= 604
    assert 1 <= res["surah_number"] <= 114
    assert len(res["arabic_text"]) > 0
    assert len(res["translation"]) > 0


def test_formatting_with_maraji():
    """بررسی درج استناد به مرجع تقلید و تفسیر منتخب در متن خروجی"""
    res = IstikharaService.perform_istikhara(1)

    msg_sistani = IstikharaService.format_istikhara_message(res, marja="sistani", tafsir="nemooneh")
    assert "آیت‌الله العظمی سیستانی" in msg_sistani
    assert "تفسیر نمونه" in msg_sistani
    assert "نتیجه استخاره با قرآن کریم" in msg_sistani

    msg_khamenei = IstikharaService.format_istikhara_message(res, marja="khamenei", tafsir="al-mizan")
    assert "آیت‌الله العظمی خامنه‌ای" in msg_khamenei
    assert "تفسیر المیزان" in msg_khamenei


@pytest.mark.asyncio
async def test_save_history_and_favorites(test_db):
    """بررسی درج استخاره در تاریخچه کاربر و نشانه‌گذاری علاقه‌مندی"""
    user_id = 99887766
    await UserRepository.upsert_user(telegram_id=user_id, username="test_user", first_name="علی", last_name="")

    await IstikharaRepository.save_record(
        telegram_id=user_id,
        surah_number=1,
        surah_name="الفاتحة",
        ayah_number=1,
        page_number=1,
        result_code="very_good",
        result_title="بسیار خوب"
    )

    history = await IstikharaRepository.get_user_history(user_id, limit=5)
    assert len(history) == 1
    record = history[0]
    assert record.surah_name == "الفاتحة"
    assert record.is_favorite is False

    # تغییر وضعیت علاقه‌مندی
    new_fav = await IstikharaRepository.toggle_favorite(record.id, user_id)
    assert new_fav is True

    # بررسی ثبت وضعیت
    fav_history = await IstikharaRepository.get_user_history(user_id, favorites_only=True)
    assert len(fav_history) == 1
    assert fav_history[0].id == record.id

"""
تست‌های خودکار سوره‌های قرآن، آیه روز و جستجوی آیات
"""

from datetime import date
from bot.services.quran_service import QuranService


def test_surah_count_and_details():
    surahs = QuranService.get_all_surahs()
    assert len(surahs) == 114

    fatiha = QuranService.get_surah_by_number(1)
    assert fatiha is not None
    assert fatiha["name"] == "الفاتحة"
    assert fatiha["ayas"] == 7
    assert fatiha["start_page"] == 1

    yasin = QuranService.get_surah_by_number(36)
    assert yasin is not None
    assert yasin["name"] in ("يس", "یس")
    assert yasin["ayas"] == 83

    nas = QuranService.get_surah_by_number(114)
    assert nas is not None
    assert nas["name"] == "الناس"


def test_search_surahs():
    results = QuranService.search_surahs("یس")
    assert any(s["number"] == 36 for s in results)

    results_num = QuranService.search_surahs("112")
    assert any(s["number"] == 112 for s in results_num)


def test_daily_ayah_determinism():
    d1 = date(2026, 5, 10)
    ayah1 = QuranService.get_daily_ayah(d1)
    ayah2 = QuranService.get_daily_ayah(d1)

    assert ayah1["surah_number"] == ayah2["surah_number"]
    assert ayah1["ayah_number"] == ayah2["ayah_number"]
    assert ayah1["arabic_text"] == ayah2["arabic_text"]

    formatted = QuranService.format_daily_ayah_message(ayah1)
    assert ayah1["surah_name"] in formatted
    assert "آیهٔ نورانی روز" in formatted

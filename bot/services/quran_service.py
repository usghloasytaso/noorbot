"""
سرویس جستجو و مدیریت آیات قرآن کریم و آیهٔ روز
"""

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("service.quran")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class QuranService:
    _data = None
    _surahs = []
    _sample_verses = []

    @classmethod
    def load_data(cls):
        if cls._data is not None:
            return

        quran_file = DATA_DIR / "quran_sample.json"
        with open(quran_file, "r", encoding="utf-8") as f:
            cls._data = json.load(f)

        cls._surahs = cls._data.get("surahs", [])
        cls._sample_verses = cls._data.get("sample_verses", [])
        logger.info("Loaded %d surahs and %d sample verses.", len(cls._surahs), len(cls._sample_verses))

    @classmethod
    def get_all_surahs(cls) -> List[Dict[str, Any]]:
        cls.load_data()
        return cls._surahs

    @classmethod
    def get_surah_by_number(cls, number: int) -> Optional[Dict[str, Any]]:
        cls.load_data()
        for s in cls._surahs:
            if s["number"] == number:
                return s
        return None

    @staticmethod
    def normalize_text(text: str) -> str:
        """یکسان‌سازی حروف فارسی و عربی (ی/ي، ک/ك، اعراب) برای جستجوی دقیق"""
        if not text:
            return ""
        t = text.replace("ي", "ی").replace("ك", "ک").replace("ة", "ه").replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
        for diacritic in ['\u064b', '\u064c', '\u064d', '\u064e', '\u064f', '\u0650', '\u0651', '\u0652']:
            t = t.replace(diacritic, "")
        return t.strip().lower()

    @classmethod
    def search_surahs(cls, query: str) -> List[Dict[str, Any]]:
        cls.load_data()
        norm_query = cls.normalize_text(query)
        if not norm_query:
            return cls._surahs[:10]

        results = []
        for s in cls._surahs:
            norm_name = cls.normalize_text(s["name"])
            if (
                norm_query in norm_name
                or norm_query in s["tname"].lower()
                or norm_query in s["ename"].lower()
                or (norm_query.isdigit() and int(norm_query) == s["number"])
            ):
                results.append(s)
        return results

    @classmethod
    def search_verses(cls, query: str) -> List[Dict[str, Any]]:
        cls.load_data()
        norm_query = cls.normalize_text(query)
        if not norm_query:
            return []

        results = []
        for v in cls._sample_verses:
            norm_text = cls.normalize_text(v["text"])
            norm_tr = cls.normalize_text(v["translation"])
            if norm_query in norm_text or norm_query in norm_tr:
                results.append(v)
        return results

    @classmethod
    def get_daily_ayah(cls, target_date: Optional[date] = None) -> Dict[str, Any]:
        """انتخاب آیهٔ روز به صورت یکنواخت و معین بر اساس روز سال"""
        cls.load_data()
        if target_date is None:
            target_date = date.today()

        day_of_year = target_date.timetuple().tm_yday
        index = day_of_year % len(cls._sample_verses)
        verse = cls._sample_verses[index]
        surah = cls.get_surah_by_number(verse["surah"])
        return {
            "surah_number": verse["surah"],
            "surah_name": surah["name"] if surah else f"سوره {verse['surah']}",
            "ayah_number": verse["ayah"],
            "arabic_text": verse["text"],
            "translation": verse["translation"],
            "page": verse.get("page", 1),
            "juz": verse.get("juz", 1)
        }

    @classmethod
    def format_daily_ayah_message(cls, ayah: Dict[str, Any]) -> str:
        lines = [
            "✨ <b>آیهٔ نورانی روز</b> ✨",
            "━━━━━━━━━━━━━━━━━━━━",
            f"📜 <b>سوره:</b> {ayah['surah_name']} - <b>آیه:</b> {ayah['ayah_number']}",
            f"📄 <b>جزء:</b> {ayah['juz']} | <b>صفحه:</b> {ayah['page']}",
            "",
            f"<b>«{ayah['arabic_text']}»</b>",
            "",
            "📝 <b>ترجمه:</b>",
            f"«{ayah['translation']}»",
            "━━━━━━━━━━━━━━━━━━━━",
            "🌿 <i>تدبر در کلام الهی، آرامش‌بخش دل‌ها و هدایتگر مسیر زندگی است.</i>"
        ]
        return "\n".join(lines)

"""
سرویس تقویم، تبدیل تاریخ (شمسی، قمری، میلادی)، مناسبت‌های دینی و ذکر روز
"""

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("service.calendar")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

SHAMSI_MONTH_NAMES = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
]

HIJRI_MONTH_NAMES = [
    "محرم", "صفر", "ربیع‌الاول", "ربیع‌الثانی", "جمادی‌الاول", "جمادی‌الثانی",
    "رجب", "شعبان", "رمضان", "شوال", "ذی‌القعده", "ذی‌الحجه"
]

WEEKDAY_NAMES = [
    "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یک‌شنبه"
]


class CalendarService:
    _occasions_data = None
    _duas_data = None
    _hadiths_data = None

    @classmethod
    def load_data(cls):
        if cls._occasions_data is None:
            with open(DATA_DIR / "occasions.json", "r", encoding="utf-8") as f:
                cls._occasions_data = json.load(f)
        if cls._duas_data is None:
            with open(DATA_DIR / "duas.json", "r", encoding="utf-8") as f:
                cls._duas_data = json.load(f)
        if cls._hadiths_data is None:
            with open(DATA_DIR / "hadiths.json", "r", encoding="utf-8") as f:
                cls._hadiths_data = json.load(f)

    @staticmethod
    def gregorian_to_jalali(gy: int, gm: int, gd: int) -> Tuple[int, int, int]:
        """تبدیل دقیق تاریخ میلادی به تاریخ هجری خورشیدی (شمسی)"""
        g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
        if gy > 1600:
            jy = 979
            gy -= 1600
        else:
            jy = 0
            gy -= 621

        gy2 = gy + 1 if gm > 2 else gy
        days = (
            (365 * gy)
            + ((gy2 + 3) // 4)
            - ((gy2 + 99) // 100)
            + ((gy2 + 399) // 400)
            - 80
            + gd
            + g_d_m[gm - 1]
        )
        jy += 33 * (days // 12053)
        days %= 12053
        jy += 4 * (days // 1461)
        days %= 1461

        if days > 365:
            jy += (days - 1) // 365
            days = (days - 1) % 365

        if days < 186:
            jm = 1 + (days // 31)
            jd = 1 + (days % 31)
        else:
            jm = 7 + ((days - 186) // 30)
            jd = 1 + ((days - 186) % 30)

        return jy, jm, jd

    @staticmethod
    def gregorian_to_hijri(gy: int, gm: int, gd: int) -> Tuple[int, int, int]:
        """تقریب نجومی استاندارد تاریخ هجری قمری"""
        # محاسبه روز ژولینی
        if gm < 3:
            gy -= 1
            gm += 12
        a = gy // 100
        b = 2 - a + (a // 4)
        jd = int(365.25 * (gy + 4716)) + int(30.6001 * (gm + 1)) + gd + b - 1524.5

        # تبدیل به هجری قمری (مبدأ هجرت: 16 ژوئیه 622 میلادی)
        l = jd - 1948440 + 10632
        n = (l - 1) // 10631
        l = l - 10631 * n + 354
        j = ((10985 - l) // 5316) * ((50 * l) // 17719) + (l // 5670) * ((43 * l) // 15238)
        l = l - ((30 - j) // 15) * ((17719 * j) // 50) - (j // 16) * ((15238 * j) // 43) + 29
        hm = (24 * l) // 709
        hd = l - (709 * hm) // 24
        hy = 30 * n + j - 30

        return hy, hm, hd

    @classmethod
    def get_today_info(cls, target_date: Optional[date] = None) -> Dict[str, Any]:
        cls.load_data()
        if target_date is None:
            target_date = date.today()

        gy, gm, gd = target_date.year, target_date.month, target_date.day
        jy, jm, jd = cls.gregorian_to_jalali(gy, gm, gd)
        hy, hm, hd = cls.gregorian_to_hijri(gy, gm, gd)

        # روز هفته
        weekday_idx = target_date.weekday()  # 0: Monday, 6: Sunday
        weekday_name = WEEKDAY_NAMES[weekday_idx]

        # ذکر روز
        daily_azkar = cls._duas_data.get("daily_azkar", [])
        todays_zikr = None
        for z in daily_azkar:
            if z.get("day_index") == weekday_idx:
                todays_zikr = z
                break
        if not todays_zikr and daily_azkar:
            todays_zikr = daily_azkar[0]

        # مناسبت‌های امروز
        occasions = []
        for occ in cls._occasions_data.get("hijri_occasions", []):
            if occ["month"] == hm and occ["day"] == hd:
                occasions.append({"calendar": "قمری", "title": occ["title"], "type": occ.get("type", "normal")})

        for occ in cls._occasions_data.get("shamsi_occasions", []):
            if occ["month"] == jm and occ["day"] == jd:
                occasions.append({"calendar": "شمسی", "title": occ["title"], "type": occ.get("type", "normal")})

        # حدیث روز
        day_of_year = target_date.timetuple().tm_yday
        hadiths = cls._hadiths_data if isinstance(cls._hadiths_data, list) else []
        hadith_today = hadiths[day_of_year % len(hadiths)] if hadiths else None

        return {
            "weekday": weekday_name,
            "shamsi": f"{jd} {SHAMSI_MONTH_NAMES[jm - 1]} {jy}",
            "hijri": f"{hd} {HIJRI_MONTH_NAMES[hm - 1]} {hy}",
            "gregorian": target_date.strftime("%d %B %Y"),
            "occasions": occasions,
            "zikr": todays_zikr,
            "hadith": hadith_today
        }

    @classmethod
    def format_daily_content(cls, info: Dict[str, Any]) -> str:
        lines = [
            f"📅 <b>امروز: {info['weekday']}</b>",
            f"🇮🇷 شمسی: <code>{info['shamsi']}</code>",
            f"🌙 قمری: <code>{info['hijri']}</code>",
            f"🌍 میلادی: <code>{info['gregorian']}</code>",
            "━━━━━━━━━━━━━━━━━━━━"
        ]

        # مناسبت‌ها
        if info["occasions"]:
            lines.append("🗓 <b>مناسبت‌های امروز:</b>")
            for occ in info["occasions"]:
                icon = "🏴" if occ.get("type") == "mourning" else "🌸"
                lines.append(f"{icon} {occ['title']}")
            lines.append("")
        else:
            lines.append("🗓 <i>امروز مناسبت ثبت‌شدهٔ خاصی در تقویم ندارد.</i>")
            lines.append("")

        # ذکر روز
        if info.get("zikr"):
            z = info["zikr"]
            lines.extend([
                "📿 <b>ذکر امروز:</b>",
                f"<b>«{z['arabic']}»</b> ({z['count']} مرتبه)",
                f"📝 {z['persian']}",
                f"✨ <i>فضیلت: {z.get('virtue', '')}</i>",
                "━━━━━━━━━━━━━━━━━━━━"
            ])

        # حدیث روز
        if info.get("hadith"):
            h = info["hadith"]
            lines.extend([
                f"📖 <b>حدیث روز از {h['speaker']}:</b>",
                f"<i>«{h['arabic']}»</i>",
                f"«{h['persian']}»",
                f"📚 <b>منبع:</b> {h['source']}",
                "━━━━━━━━━━━━━━━━━━━━"
            ])

        return "\n".join(lines)

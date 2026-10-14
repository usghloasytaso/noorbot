"""
سرویس محاسبه اوقات شرعی با استفاده از محاسبات نجومی استاندارد
سازگار با روش مؤسسه ژئوفیزیک دانشگاه تهران و مؤسسه لوای قم (شیعه اثناعشری)
"""

import math
from datetime import date, datetime
from typing import Any, Dict, List, Optional


CITIES = {
    "تهران": {"lat": 35.6892, "lng": 51.3890, "tz": 3.5},
    "مشهد": {"lat": 36.2972, "lng": 59.6067, "tz": 3.5},
    "اصفهان": {"lat": 32.6546, "lng": 51.6680, "tz": 3.5},
    "شیراز": {"lat": 29.5918, "lng": 52.5837, "tz": 3.5},
    "تبریز": {"lat": 38.0962, "lng": 46.2738, "tz": 3.5},
    "قم": {"lat": 34.6401, "lng": 50.8764, "tz": 3.5},
    "اهواز": {"lat": 31.3183, "lng": 48.6706, "tz": 3.5},
    "کرمانشاه": {"lat": 34.3277, "lng": 47.0778, "tz": 3.5},
    "رشت": {"lat": 37.2808, "lng": 49.5832, "tz": 3.5},
    "کرمان": {"lat": 30.2839, "lng": 57.0834, "tz": 3.5},
    "همدان": {"lat": 34.7989, "lng": 48.5150, "tz": 3.5},
    "یزد": {"lat": 31.8974, "lng": 54.3569, "tz": 3.5},
    "زاهدان": {"lat": 29.4963, "lng": 60.8629, "tz": 3.5},
    "ساری": {"lat": 36.5659, "lng": 53.0586, "tz": 3.5},
    "ارومیه": {"lat": 37.5527, "lng": 45.0761, "tz": 3.5},
    "نجف اشرف": {"lat": 31.9961, "lng": 44.3142, "tz": 3.0},
    "کربلای معلی": {"lat": 32.6160, "lng": 44.0249, "tz": 3.0}
}


class PrayerService:
    @staticmethod
    def get_supported_cities() -> List[str]:
        return list(CITIES.keys())

    @staticmethod
    def _float_to_time_str(hours: float) -> str:
        hours = hours % 24
        h = int(hours)
        m = int((hours - h) * 60 + 0.5)
        if m == 60:
            h = (h + 1) % 24
            m = 0
        return f"{h:02d}:{m:02d}"

    @classmethod
    def calculate_times(
        cls,
        city_name: str = "تهران",
        target_date: Optional[date] = None,
        method: str = "tehran"
    ) -> Dict[str, Any]:
        """
        محاسبه اوقات شرعی بر مبنای زاویه و مشخصات جغرافیایی
        """
        city_info = CITIES.get(city_name, CITIES["تهران"])
        lat = city_info["lat"]
        lng = city_info["lng"]
        tz = city_info["tz"]

        if target_date is None:
            target_date = date.today()

        day_of_year = target_date.timetuple().tm_yday

        # معادلات مدار خورشید و زاویه میل خورشید (Declination)
        b = 2 * math.pi * (day_of_year - 81) / 365
        eot = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)  # دقیقه
        declination = 23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365))

        # ظهر شرعی (Solar Noon)
        noon_hours = 12.0 + tz - (lng / 15.0) - (eot / 60.0)

        lat_rad = math.radians(lat)
        dec_rad = math.radians(declination)

        # زاویه غروب و طلوع ظاهری (0.833 درجه زیر افق)
        def hour_angle(altitude_deg: float) -> float:
            alt_rad = math.radians(altitude_deg)
            cos_ha = (math.sin(alt_rad) - math.sin(lat_rad) * math.sin(dec_rad)) / (
                math.cos(lat_rad) * math.cos(dec_rad)
            )
            # کنترل محدوده‌های کره‌ای
            cos_ha = max(-1.0, min(1.0, cos_ha))
            return math.degrees(math.acos(cos_ha))

        ha_sun = hour_angle(-0.833)
        sunrise_hours = noon_hours - (ha_sun / 15.0)
        sunset_hours = noon_hours + (ha_sun / 15.0)

        # زاویه فجر (اذان صبح)
        # مؤسسه ژئوفیزیک تهران: 17.7 درجه؛ لوای قم: 16.0 درجه
        fajr_angle = -17.7 if method == "tehran" else -16.0
        ha_fajr = hour_angle(fajr_angle)
        fajr_hours = noon_hours - (ha_fajr / 15.0)

        # زاویه مغرب شرعی (4.5 درجه زیر افق پس از غروب آفتاب)
        maghrib_angle = -4.5
        ha_maghrib = hour_angle(maghrib_angle)
        maghrib_hours = noon_hours + (ha_maghrib / 15.0)

        # نیمه‌شب شرعی: میانگین اذان مغرب تا اذان صبح فردا
        midnight_hours = (maghrib_hours + (fajr_hours + 24.0)) / 2.0

        return {
            "city": city_name,
            "date": target_date.strftime("%Y-%m-%d"),
            "method": "دانشگاه تهران" if method == "tehran" else "مؤسسه لوای قم",
            "imsak": cls._float_to_time_str(fajr_hours - (10 / 60.0)),
            "fajr": cls._float_to_time_str(fajr_hours),
            "sunrise": cls._float_to_time_str(sunrise_hours),
            "dhuhr": cls._float_to_time_str(noon_hours),
            "sunset": cls._float_to_time_str(sunset_hours),
            "maghrib": cls._float_to_time_str(maghrib_hours),
            "midnight": cls._float_to_time_str(midnight_hours)
        }

    @classmethod
    def format_prayer_message(cls, times: Dict[str, Any]) -> str:
        lines = [
            f"🕌 <b>اوقات شرعی به افق {times['city']}</b>",
            f"📅 <b>تاریخ:</b> {times['date']} (روش محاسبه: {times['method']})",
            "━━━━━━━━━━━━━━━━━━━━",
            f"🌙 <b>امساک:</b> <code>{times['imsak']}</code>",
            f"🌅 <b>اذان صبح:</b> <code>{times['fajr']}</code>",
            f"☀️ <b>طلوع آفتاب:</b> <code>{times['sunrise']}</code>",
            f"🕛 <b>اذان ظهر:</b> <code>{times['dhuhr']}</code>",
            f"🌇 <b>غروب آفتاب:</b> <code>{times['sunset']}</code>",
            f"🌌 <b>اذان مغرب:</b> <code>{times['maghrib']}</code>",
            f"🌃 <b>نیمه‌شب شرعی:</b> <code>{times['midnight']}</code>",
            "━━━━━━━━━━━━━━━━━━━━",
            "🤲 <i>التماس دعا در لحظات استجابت دعا</i>"
        ]
        return "\n".join(lines)

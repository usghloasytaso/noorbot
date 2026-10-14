"""
تست‌های خودکار محاسبات اوقات شرعی، شهرهای پشتیبانی‌شده و توالی زمانی اذان‌ها
"""

from datetime import date
from bot.services.prayer_service import PrayerService


def test_supported_cities():
    cities = PrayerService.get_supported_cities()
    assert "تهران" in cities
    assert "مشهد" in cities
    assert "قم" in cities
    assert "کربلای معلی" in cities
    assert "نجف اشرف" in cities


def test_prayer_times_structure():
    times = PrayerService.calculate_times("تهران", target_date=date(2026, 3, 21), method="tehran")
    for key in ["city", "imsak", "fajr", "sunrise", "dhuhr", "sunset", "maghrib", "midnight"]:
        assert key in times
        assert len(times[key]) > 0


def test_prayer_chronological_order():
    """بررسی توالی منطقی اوقات شرعی (صبح قبل از طلوع، طلوع قبل از ظهر، ظهر قبل از غروب و مغرب)"""
    times = PrayerService.calculate_times("تهران", target_date=date(2026, 6, 21))

    def time_to_minutes(t_str: str) -> int:
        h, m = map(int, t_str.split(":"))
        return h * 60 + m

    fajr_m = time_to_minutes(times["fajr"])
    sunrise_m = time_to_minutes(times["sunrise"])
    dhuhr_m = time_to_minutes(times["dhuhr"])
    sunset_m = time_to_minutes(times["sunset"])
    maghrib_m = time_to_minutes(times["maghrib"])

    assert fajr_m < sunrise_m
    assert sunrise_m < dhuhr_m
    assert dhuhr_m < sunset_m
    assert sunset_m <= maghrib_m


def test_calculation_methods():
    times_tehran = PrayerService.calculate_times("قم", method="tehran")
    times_leva = PrayerService.calculate_times("قم", method="leva")

    assert times_tehran["method"] == "دانشگاه تهران"
    assert times_leva["method"] == "مؤسسه لوای قم"
    # روش دانشگاه تهران و لوای قم در زمان اذان صبح اندکی تفاوت دارند
    assert times_tehran["fajr"] != ""
    assert times_leva["fajr"] != ""


def test_format_prayer_message():
    times = PrayerService.calculate_times("مشهد")
    msg = PrayerService.format_prayer_message(times)
    assert "مشهد" in msg
    assert "اذان صبح" in msg
    assert "اذان ظهر" in msg
    assert "اذان مغرب" in msg

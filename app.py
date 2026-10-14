"""
رابط کاربری وب و نقطه اجرای ربات در پلتفرم‌های ابری (سازگار با Hugging Face Spaces و Railway)
"""

import asyncio
import logging
import os
import sys
import threading
from pathlib import Path

# افزودن ریشه پروژه به مسیر پایتون
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bot.config import settings
from bot.services.calendar_service import CalendarService
from bot.services.prayer_service import PrayerService
from bot.services.quran_service import QuranService

logger = logging.getLogger("app.web")


def run_telegram_bot_background():
    """اجرای ربات تلگرام در پس‌زمینه با حلقه رویداد مستقل"""
    from bot.main import main
    logger.info("Starting NoorBot background event loop...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except Exception as e:
        logger.error("Error in bot background execution: %s", e)


# آغاز اجرای ربات تلگرام در ترد پس‌زمینه
bot_thread = threading.Thread(target=run_telegram_bot_background, daemon=True)
bot_thread.start()


# تلاش برای راه‌اندازی رابط کاربری زیبا با Gradio (در صورت وجود روی هاگینگ‌فیس)
try:
    import gradio as gr

    CalendarService.load_data()
    QuranService.load_data()

    def get_status_info():
        today_info = CalendarService.get_today_info()
        ayah = QuranService.get_daily_ayah()
        times = PrayerService.calculate_times("تهران")

        return (
            "### 🟢 وضعیت ربات تلگرام: **فعال و آنلاین**\n"
            f"▫️ **امروز:** {today_info['weekday']} ({today_info['shamsi']} - {today_info['hijri']})\n"
            f"▫️ **آیه روز:** سوره {ayah['surah_name']} (آیه {ayah['ayah_number']}):\n"
            f"> *«{ayah['arabic_text']}»*\n\n"
            f"▫️ **اوقات شرعی تهران:** اذان صبح: `{times['fajr']}` | اذان ظهر: `{times['dhuhr']}` | اذان مغرب: `{times['maghrib']}`"
        )

    with gr.Blocks(title="NoorBot - سامانه جامع نور") as demo:
        gr.Markdown("# 🌟 ربات جامع مذهبی و قرآنی نور (NoorBot)")
        status_md = gr.Markdown(get_status_info())
        refresh_btn = gr.Button("🔄 به‌روزرسانی وضعیت")
        refresh_btn.click(fn=get_status_info, outputs=status_md)

    if __name__ == "__main__":
        port = int(os.environ.get("PORT", 7860))
        demo.launch(server_name="0.0.0.0", server_port=port)

except ImportError:
    # در صورت عدم نصب Gradio (مثلاً روی سرورهای مینیمال)، از سرور وب استاندارد استفاده می‌شود
    if __name__ == "__main__":
        from bot.web.health import start_health_server
        port = int(os.environ.get("PORT", 8080))
        asyncio.run(start_health_server("0.0.0.0", port))

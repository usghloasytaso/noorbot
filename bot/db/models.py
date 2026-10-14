"""
مدل‌های داده‌ای برای موجودیت‌های پایگاه داده ربات نور
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: str = "fa"
    selected_marja: str = "sistani"
    selected_tafsir: str = "nemooneh"
    save_history: bool = True
    city: str = "تهران"
    prayer_method: str = "tehran"
    notifications_enabled: bool = False
    notification_time: str = "07:00"
    is_banned: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Group:
    chat_id: int
    title: Optional[str] = None
    username: Optional[str] = None
    chat_type: str = "supergroup"
    is_active: bool = True
    allow_istikhara: bool = True
    private_result_mode: bool = True
    allow_daily_ayah: bool = True
    daily_ayah_time: str = "08:00"
    cooldown_seconds: int = 10
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class IstikharaRecord:
    id: Optional[int] = None
    telegram_id: int = 0
    surah_number: int = 1
    surah_name: str = ""
    ayah_number: int = 1
    page_number: int = 1
    result_code: str = "good"
    result_title: str = ""
    intent_topic: Optional[str] = None
    is_favorite: bool = False
    created_at: Optional[datetime] = None


@dataclass
class TasbihRecord:
    id: Optional[int] = None
    telegram_id: int = 0
    preset_name: str = ""
    total_count: int = 0
    updated_at: Optional[datetime] = None

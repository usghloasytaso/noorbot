"""
تنظیمات پیکربندی ربات نور (NoorBot) با استفاده از Pydantic Settings
پشتیبانی از متغیرهای محیطی و فایل .env
"""

from typing import Any, List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # توکن ربات تلگرام
    bot_token: str = Field(default="123456789:ABCdefGHIjklMNOpqrSTUvwxyz", alias="BOT_TOKEN")

    # شناسه‌های ادمین‌ها (با کاما جدا می‌شود یا آرایه عددی)
    admin_ids: Any = Field(default_factory=list, alias="ADMIN_IDS")

    # اتصال پایگاه داده (Supabase / PostgreSQL یا SQLite)
    database_url: str = Field(default="sqlite:///noorbot.db", alias="DATABASE_URL")

    # سرور سلامت‌سنجی (Render Web Service)
    port: int = Field(default=8080, alias="PORT")
    host: str = Field(default="0.0.0.0", alias="HOST")

    # محیط اجرا
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # محدودیت نرخ درخواست‌ها (ضد اسپم)
    rate_limit_burst: int = Field(default=5, alias="RATE_LIMIT_BURST")
    rate_limit_window: float = Field(default=3.0, alias="RATE_LIMIT_WINDOW")

    # پیش‌فرض‌های فقهی و قرآنی
    default_marja: str = Field(default="sistani", alias="DEFAULT_MARJA")
    default_tafsir: str = Field(default="nemooneh", alias="DEFAULT_TAFSIR")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: Union[str, int, List[Union[int, str]]]) -> List[int]:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            parts = [p.strip() for p in v.replace(";", ",").split(",") if p.strip()]
            return [int(p) for p in parts if p.isdigit() or (p.startswith("-") and p[1:].isdigit())]
        elif isinstance(v, int):
            return [v]
        elif isinstance(v, list):
            res = []
            for item in v:
                if isinstance(item, int):
                    res.append(item)
                elif isinstance(item, str) and (item.strip().isdigit() or (item.strip().startswith("-") and item.strip()[1:].isdigit())):
                    res.append(int(item.strip()))
            return res
        return []

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        # تبدیل خودکار postgres:// قدیمی به postgresql:// استاندارد
        if v.startswith("postgres://"):
            return "postgresql://" + v[len("postgres://"):]
        return v

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith("postgresql://") or self.database_url.startswith("postgres://")

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite://")


# شیء تکین تنظمیات
settings = Settings()

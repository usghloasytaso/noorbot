"""
مخازن داده (Repositories) برای تعامل ساختاریافته با پایگاه داده
"""

import json
import logging
from typing import Any, Dict, List, Optional

from bot.config import settings
from bot.db.base import db
from bot.db.models import Group, IstikharaRecord, User

logger = logging.getLogger("db.repository")


class UserRepository:
    @staticmethod
    async def get_by_id(telegram_id: int) -> Optional[User]:
        query = "SELECT * FROM users WHERE telegram_id = $1"
        row = await db.fetchrow(query, telegram_id)
        if not row:
            return None
        return User(
            telegram_id=row["telegram_id"],
            username=row.get("username"),
            first_name=row.get("first_name"),
            last_name=row.get("last_name"),
            language_code=row.get("language_code", "fa"),
            selected_marja=row.get("selected_marja", "sistani"),
            selected_tafsir=row.get("selected_tafsir", "nemooneh"),
            save_history=bool(row.get("save_history", True)),
            city=row.get("city", "تهران"),
            prayer_method=row.get("prayer_method", "tehran"),
            notifications_enabled=bool(row.get("notifications_enabled", False)),
            notification_time=row.get("notification_time", "07:00"),
            is_banned=bool(row.get("is_banned", False)),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at")
        )

    @staticmethod
    async def upsert_user(telegram_id: int, username: Optional[str], first_name: Optional[str], last_name: Optional[str], language_code: str = "fa") -> User:
        user = await UserRepository.get_by_id(telegram_id)
        if user:
            # به‌روزرسانی مشخصات نام کاربری در صورت تغییر
            if user.username != username or user.first_name != first_name or user.last_name != last_name:
                query = """
                UPDATE users SET username = $1, first_name = $2, last_name = $3, updated_at = CURRENT_TIMESTAMP
                WHERE telegram_id = $4
                """
                await db.execute(query, username, first_name, last_name, telegram_id)
                user.username = username
                user.first_name = first_name
                user.last_name = last_name
            return user

        # درج کاربر جدید
        query = """
        INSERT INTO users (telegram_id, username, first_name, last_name, language_code, selected_marja, selected_tafsir)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        await db.execute(query, telegram_id, username, first_name, last_name, language_code, settings.default_marja, settings.default_tafsir)
        await StatsRepository.increment("total_users")
        return (await UserRepository.get_by_id(telegram_id)) or User(telegram_id=telegram_id)

    @staticmethod
    async def update_marja(telegram_id: int, marja: str):
        query = "UPDATE users SET selected_marja = $1, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = $2"
        await db.execute(query, marja, telegram_id)

    @staticmethod
    async def update_tafsir(telegram_id: int, tafsir: str):
        query = "UPDATE users SET selected_tafsir = $1, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = $2"
        await db.execute(query, tafsir, telegram_id)

    @staticmethod
    async def update_city(telegram_id: int, city: str, method: str = "tehran"):
        query = "UPDATE users SET city = $1, prayer_method = $2, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = $3"
        await db.execute(query, city, method, telegram_id)

    @staticmethod
    async def toggle_history(telegram_id: int, enabled: bool):
        val = 1 if enabled else 0
        query = "UPDATE users SET save_history = $1, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = $2"
        await db.execute(query, val, telegram_id)

    @staticmethod
    async def toggle_notifications(telegram_id: int, enabled: bool, time_str: str = "07:00"):
        val = 1 if enabled else 0
        query = "UPDATE users SET notifications_enabled = $1, notification_time = $2, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = $3"
        await db.execute(query, val, time_str, telegram_id)

    @staticmethod
    async def count_users() -> int:
        query = "SELECT COUNT(*) FROM users"
        val = await db.fetchval(query)
        return int(val or 0)

    @staticmethod
    async def get_all_active_users() -> List[int]:
        query = "SELECT telegram_id FROM users WHERE is_banned = 0" if db.is_sqlite else "SELECT telegram_id FROM users WHERE is_banned = FALSE"
        rows = await db.fetch(query)
        return [r["telegram_id"] for r in rows]

    @staticmethod
    async def delete_user_data(telegram_id: int):
        """حذف کامل اطلاعات کاربر طبق قوانین حریم خصوصی"""
        await db.execute("DELETE FROM istikhara_history WHERE telegram_id = $1", telegram_id)
        await db.execute("DELETE FROM tasbih_records WHERE telegram_id = $1", telegram_id)
        await db.execute("DELETE FROM users WHERE telegram_id = $1", telegram_id)


class GroupRepository:
    @staticmethod
    async def get_by_id(chat_id: int) -> Optional[Group]:
        query = "SELECT * FROM groups WHERE chat_id = $1"
        row = await db.fetchrow(query, chat_id)
        if not row:
            return None
        return Group(
            chat_id=row["chat_id"],
            title=row.get("title"),
            username=row.get("username"),
            chat_type=row.get("chat_type", "supergroup"),
            is_active=bool(row.get("is_active", True)),
            allow_istikhara=bool(row.get("allow_istikhara", True)),
            private_result_mode=bool(row.get("private_result_mode", True)),
            allow_daily_ayah=bool(row.get("allow_daily_ayah", True)),
            daily_ayah_time=row.get("daily_ayah_time", "08:00"),
            cooldown_seconds=int(row.get("cooldown_seconds", 10)),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at")
        )

    @staticmethod
    async def upsert_group(chat_id: int, title: Optional[str], username: Optional[str], chat_type: str = "supergroup") -> Group:
        group = await GroupRepository.get_by_id(chat_id)
        if group:
            if group.title != title or group.username != username or not group.is_active:
                query = "UPDATE groups SET title = $1, username = $2, is_active = 1, updated_at = CURRENT_TIMESTAMP WHERE chat_id = $3"
                await db.execute(query, title, username, chat_id)
                group.title = title
                group.username = username
                group.is_active = True
            return group

        query = """
        INSERT INTO groups (chat_id, title, username, chat_type, is_active, allow_istikhara, private_result_mode)
        VALUES ($1, $2, $3, $4, 1, 1, 1)
        """
        await db.execute(query, chat_id, title, username, chat_type)
        await StatsRepository.increment("total_groups")
        return (await GroupRepository.get_by_id(chat_id)) or Group(chat_id=chat_id)

    @staticmethod
    async def update_settings(chat_id: int, allow_istikhara: bool, private_mode: bool, allow_daily_ayah: bool):
        val_ist = 1 if allow_istikhara else 0
        val_priv = 1 if private_mode else 0
        val_ayah = 1 if allow_daily_ayah else 0
        query = """
        UPDATE groups SET allow_istikhara = $1, private_result_mode = $2, allow_daily_ayah = $3, updated_at = CURRENT_TIMESTAMP
        WHERE chat_id = $4
        """
        await db.execute(query, val_ist, val_priv, val_ayah, chat_id)

    @staticmethod
    async def set_active(chat_id: int, is_active: bool):
        val = 1 if is_active else 0
        await db.execute("UPDATE groups SET is_active = $1, updated_at = CURRENT_TIMESTAMP WHERE chat_id = $2", val, chat_id)

    @staticmethod
    async def count_groups() -> int:
        query = "SELECT COUNT(*) FROM groups WHERE is_active = 1" if db.is_sqlite else "SELECT COUNT(*) FROM groups WHERE is_active = TRUE"
        val = await db.fetchval(query)
        return int(val or 0)

    @staticmethod
    async def get_all_active_groups() -> List[int]:
        query = "SELECT chat_id FROM groups WHERE is_active = 1" if db.is_sqlite else "SELECT chat_id FROM groups WHERE is_active = TRUE"
        rows = await db.fetch(query)
        return [r["chat_id"] for r in rows]


class IstikharaRepository:
    @staticmethod
    async def save_record(telegram_id: int, surah_number: int, surah_name: str, ayah_number: int, page_number: int, result_code: str, result_title: str, intent_topic: Optional[str] = None) -> int:
        query = """
        INSERT INTO istikhara_history (telegram_id, surah_number, surah_name, ayah_number, page_number, result_code, result_title, intent_topic)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        await db.execute(query, telegram_id, surah_number, surah_name, ayah_number, page_number, result_code, result_title, intent_topic)
        await StatsRepository.increment("total_istikharas")
        return 1

    @staticmethod
    async def get_user_history(telegram_id: int, limit: int = 5, favorites_only: bool = False) -> List[IstikharaRecord]:
        if favorites_only:
            query = "SELECT * FROM istikhara_history WHERE telegram_id = $1 AND is_favorite = 1 ORDER BY id DESC LIMIT $2"
        else:
            query = "SELECT * FROM istikhara_history WHERE telegram_id = $1 ORDER BY id DESC LIMIT $2"

        rows = await db.fetch(query, telegram_id, limit)
        records = []
        for r in rows:
            records.append(IstikharaRecord(
                id=r["id"],
                telegram_id=r["telegram_id"],
                surah_number=r["surah_number"],
                surah_name=r["surah_name"],
                ayah_number=r["ayah_number"],
                page_number=r["page_number"],
                result_code=r["result_code"],
                result_title=r["result_title"],
                intent_topic=r.get("intent_topic"),
                is_favorite=bool(r.get("is_favorite", False)),
                created_at=r.get("created_at")
            ))
        return records

    @staticmethod
    async def toggle_favorite(record_id: int, telegram_id: int) -> bool:
        row = await db.fetchrow("SELECT is_favorite FROM istikhara_history WHERE id = $1 AND telegram_id = $2", record_id, telegram_id)
        if not row:
            return False
        new_val = 0 if row["is_favorite"] else 1
        await db.execute("UPDATE istikhara_history SET is_favorite = $1 WHERE id = $2 AND telegram_id = $3", new_val, record_id, telegram_id)
        return bool(new_val)

    @staticmethod
    async def clear_history(telegram_id: int):
        await db.execute("DELETE FROM istikhara_history WHERE telegram_id = $1", telegram_id)

    @staticmethod
    async def count_total() -> int:
        val = await db.fetchval("SELECT COUNT(*) FROM istikhara_history")
        return int(val or 0)


class TasbihRepository:
    @staticmethod
    async def get_count(telegram_id: int, preset_name: str) -> int:
        query = "SELECT total_count FROM tasbih_records WHERE telegram_id = $1 AND preset_name = $2"
        val = await db.fetchval(query, telegram_id, preset_name)
        return int(val or 0)

    @staticmethod
    async def increment_count(telegram_id: int, preset_name: str, delta: int = 1) -> int:
        current = await TasbihRepository.get_count(telegram_id, preset_name)
        new_count = max(0, current + delta)
        # استفاده از INSERT OR REPLACE / ON CONFLICT
        if db.is_sqlite:
            query = "INSERT OR REPLACE INTO tasbih_records (telegram_id, preset_name, total_count, updated_at) VALUES ($1, $2, $3, CURRENT_TIMESTAMP)"
        else:
            query = """
            INSERT INTO tasbih_records (telegram_id, preset_name, total_count, updated_at)
            VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
            ON CONFLICT (telegram_id, preset_name) DO UPDATE SET total_count = EXCLUDED.total_count, updated_at = CURRENT_TIMESTAMP
            """
        await db.execute(query, telegram_id, preset_name, new_count)
        if delta > 0:
            await StatsRepository.increment("total_tasbih_counts", delta)
        return new_count

    @staticmethod
    async def reset_count(telegram_id: int, preset_name: str) -> int:
        if db.is_sqlite:
            query = "INSERT OR REPLACE INTO tasbih_records (telegram_id, preset_name, total_count, updated_at) VALUES ($1, $2, 0, CURRENT_TIMESTAMP)"
        else:
            query = """
            INSERT INTO tasbih_records (telegram_id, preset_name, total_count, updated_at)
            VALUES ($1, $2, 0, CURRENT_TIMESTAMP)
            ON CONFLICT (telegram_id, preset_name) DO UPDATE SET total_count = 0, updated_at = CURRENT_TIMESTAMP
            """
        await db.execute(query, telegram_id, preset_name)
        return 0


class StatsRepository:
    @staticmethod
    async def increment(metric_key: str, delta: int = 1):
        if db.is_sqlite:
            query = """
            INSERT INTO bot_stats (metric_key, metric_value, updated_at)
            VALUES ($1, $2, CURRENT_TIMESTAMP)
            ON CONFLICT(metric_key) DO UPDATE SET metric_value = bot_stats.metric_value + excluded.metric_value, updated_at = CURRENT_TIMESTAMP
            """
        else:
            query = """
            INSERT INTO bot_stats (metric_key, metric_value, updated_at)
            VALUES ($1, $2, CURRENT_TIMESTAMP)
            ON CONFLICT (metric_key) DO UPDATE SET metric_value = bot_stats.metric_value + EXCLUDED.metric_value, updated_at = CURRENT_TIMESTAMP
            """
        try:
            await db.execute(query, metric_key, delta)
        except Exception as e:
            logger.warning("Failed to increment metric %s: %s", metric_key, e)

    @staticmethod
    async def get_all_stats() -> Dict[str, int]:
        rows = await db.fetch("SELECT metric_key, metric_value FROM bot_stats")
        res = {r["metric_key"]: r["metric_value"] for r in rows}
        # مقادیر پیش‌فرض در صورت نبودن در دیتابیس
        defaults = ["total_users", "total_groups", "total_istikharas", "total_quran_searches", "total_tasbih_counts"]
        for d in defaults:
            if d not in res:
                res[d] = 0
        return res


class LogsRepository:
    @staticmethod
    async def log(level: str, module: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        meta_str = json.dumps(metadata or {}, ensure_ascii=False)
        query = "INSERT INTO system_logs (level, module, message, metadata) VALUES ($1, $2, $3, $4)"
        try:
            await db.execute(query, level, module, message, meta_str)
        except Exception as e:
            logger.error("Failed to write system log: %s", e)

"""
مدیریت اتصال و دسترسی ناهمگام به پایگاه داده (PostgreSQL/Supabase و SQLite)
طراحی دوگانه با جابجایی خودکار برای تست محلی و استقرار در کلود
"""

import asyncio
import logging
import re
import ssl
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from bot.config import settings

logger = logging.getLogger("db.base")


class DatabaseManager:
    def __init__(self, database_url: str):
        self.url = database_url
        self.is_postgres = settings.is_postgres
        self.is_sqlite = settings.is_sqlite
        self._pg_pool = None
        self._sqlite_path = None
        self._initialized = False

        if self.is_sqlite:
            # استخراج مسیر فایل sqlite
            path_str = self.url.replace("sqlite:///", "").replace("sqlite://", "")
            self._sqlite_path = path_str or "noorbot.db"

    async def connect(self):
        """ایجاد استخر اتصال به دیتابیس"""
        if self._initialized:
            return

        if self.is_postgres:
            import asyncpg
            logger.info("Connecting to PostgreSQL/Supabase pool...")
            # مدیریت SSL برای اتصال به Supabase / Render
            ssl_context = None
            if "sslmode=require" in self.url or "supabase.com" in self.url:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

            clean_url = self.url.split("?")[0]
            try:
                self._pg_pool = await asyncio.wait_for(
                    asyncpg.create_pool(
                        dsn=clean_url,
                        min_size=1,
                        max_size=10,
                        ssl=ssl_context,
                        command_timeout=15.0
                    ),
                    timeout=5.0
                )
                logger.info("Connected to PostgreSQL successfully.")
            except Exception as e:
                logger.error("Failed to connect to PostgreSQL: %s. Falling back to SQLite for safety.", e)
                self.is_postgres = False
                self.is_sqlite = True
                self._sqlite_path = "noorbot_fallback.db"
                await self._init_sqlite()
        else:
            await self._init_sqlite()

        self._initialized = True

    async def _init_sqlite(self):
        """ایجاد جداول در دیتابیس SQLite جهت اجرای محلی بدون نیاز به سرور"""
        import aiosqlite
        logger.info("Initializing SQLite database at %s...", self._sqlite_path)
        async with aiosqlite.connect(self._sqlite_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT DEFAULT 'fa',
                selected_marja TEXT DEFAULT 'sistani',
                selected_tafsir TEXT DEFAULT 'nemooneh',
                save_history INTEGER DEFAULT 1,
                city TEXT DEFAULT 'تهران',
                prayer_method TEXT DEFAULT 'tehran',
                notifications_enabled INTEGER DEFAULT 0,
                notification_time TEXT DEFAULT '07:00',
                is_banned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            await db.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                chat_id INTEGER PRIMARY KEY,
                title TEXT,
                username TEXT,
                chat_type TEXT DEFAULT 'supergroup',
                is_active INTEGER DEFAULT 1,
                allow_istikhara INTEGER DEFAULT 1,
                private_result_mode INTEGER DEFAULT 1,
                allow_daily_ayah INTEGER DEFAULT 1,
                daily_ayah_time TEXT DEFAULT '08:00',
                cooldown_seconds INTEGER DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            await db.execute("""
            CREATE TABLE IF NOT EXISTS istikhara_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                surah_number INTEGER NOT NULL,
                surah_name TEXT NOT NULL,
                ayah_number INTEGER NOT NULL,
                page_number INTEGER NOT NULL,
                result_code TEXT NOT NULL,
                result_title TEXT NOT NULL,
                intent_topic TEXT,
                is_favorite INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            await db.execute("""
            CREATE TABLE IF NOT EXISTS tasbih_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                preset_name TEXT NOT NULL,
                total_count INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(telegram_id, preset_name)
            );
            """)
            await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_stats (
                metric_key TEXT PRIMARY KEY,
                metric_value INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            await db.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                module TEXT NOT NULL,
                message TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            await db.commit()
            logger.info("SQLite schema initialized successfully.")

    def _format_query(self, query: str) -> str:
        """تبدیل نشانگرهای جایگزین $1, $2 به ? برای SQLite"""
        if self.is_sqlite:
            # تبدیل $1, $2, ... به ?
            return re.sub(r"\$\d+", "?", query)
        return query

    async def execute(self, query: str, *args) -> None:
        """اجرای دستور SQL (INSERT, UPDATE, DELETE)"""
        await self.connect()
        if self.is_postgres and self._pg_pool:
            async with self._pg_pool.acquire() as conn:
                await conn.execute(query, *args)
        else:
            import aiosqlite
            q = self._format_query(query)
            async with aiosqlite.connect(self._sqlite_path) as db:
                await db.execute(q, args)
                await db.commit()

    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """دریافت یک ردیف از نتیجه کوئری"""
        await self.connect()
        if self.is_postgres and self._pg_pool:
            async with self._pg_pool.acquire() as conn:
                record = await conn.fetchrow(query, *args)
                return dict(record) if record else None
        else:
            import aiosqlite
            q = self._format_query(query)
            async with aiosqlite.connect(self._sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(q, args) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """دریافت تمامی ردیف‌های منطبق"""
        await self.connect()
        if self.is_postgres and self._pg_pool:
            async with self._pg_pool.acquire() as conn:
                records = await conn.fetch(query, *args)
                return [dict(r) for r in records]
        else:
            import aiosqlite
            q = self._format_query(query)
            async with aiosqlite.connect(self._sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(q, args) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(r) for r in rows]

    async def fetchval(self, query: str, *args) -> Any:
        """دریافت تک مقدار نتیجه (مثلا COUNT)"""
        await self.connect()
        if self.is_postgres and self._pg_pool:
            async with self._pg_pool.acquire() as conn:
                return await conn.fetchval(query, *args)
        else:
            import aiosqlite
            q = self._format_query(query)
            async with aiosqlite.connect(self._sqlite_path) as db:
                async with db.execute(q, args) as cursor:
                    row = await cursor.fetchone()
                    return row[0] if row else None

    async def health_check(self) -> Dict[str, Any]:
        """بررسی سلامت زنده پایگاه داده برای مسیر /health"""
        try:
            val = await self.fetchval("SELECT 1")
            return {
                "status": "healthy" if val == 1 else "degraded",
                "engine": "postgresql" if self.is_postgres else "sqlite",
                "connected": True
            }
        except Exception as e:
            logger.error("Database health check failed: %s", e)
            return {
                "status": "unhealthy",
                "engine": "postgresql" if self.is_postgres else "sqlite",
                "connected": False,
                "error": str(e)
            }

    async def close(self):
        """بستن ایمن استخر ارتباطات پایگاه داده"""
        if self.is_postgres and self._pg_pool:
            logger.info("Closing PostgreSQL connection pool...")
            await self._pg_pool.close()
            self._pg_pool = None
        self._initialized = False


# نمونه مشترک دیتابیس
db = DatabaseManager(settings.database_url)

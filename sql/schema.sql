-- ====================================================================
-- NoorBot - پایگاه داده PostgreSQL / Supabase
-- ساختار جداول، ایندکس‌ها و سیاست‌های امنیتی (Row Level Security)
-- ====================================================================

-- ۱. جدول کاربران (Users)
CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    language_code VARCHAR(10) DEFAULT 'fa',
    selected_marja VARCHAR(50) DEFAULT 'sistani',
    selected_tafsir VARCHAR(50) DEFAULT 'nemooneh',
    save_history BOOLEAN DEFAULT TRUE,
    city VARCHAR(100) DEFAULT 'تهران',
    prayer_method VARCHAR(50) DEFAULT 'tehran',
    notifications_enabled BOOLEAN DEFAULT FALSE,
    notification_time VARCHAR(10) DEFAULT '07:00',
    is_banned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ۲. جدول گروه‌ها (Groups)
CREATE TABLE IF NOT EXISTS groups (
    chat_id BIGINT PRIMARY KEY,
    title TEXT,
    username TEXT,
    chat_type VARCHAR(50) DEFAULT 'supergroup',
    is_active BOOLEAN DEFAULT TRUE,
    allow_istikhara BOOLEAN DEFAULT TRUE,
    private_result_mode BOOLEAN DEFAULT TRUE, -- ارسال نتیجه به پی‌وی کاربر جهت حفظ حریم خصوصی
    allow_daily_ayah BOOLEAN DEFAULT TRUE,
    daily_ayah_time VARCHAR(10) DEFAULT '08:00',
    cooldown_seconds INT DEFAULT 10,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ۳. تاریخچه استخاره‌ها (Istikhara History)
CREATE TABLE IF NOT EXISTS istikhara_history (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    surah_number INT NOT NULL,
    surah_name TEXT NOT NULL,
    ayah_number INT NOT NULL,
    page_number INT NOT NULL,
    result_code VARCHAR(30) NOT NULL, -- very_good, good, moderate, bad, very_bad
    result_title TEXT NOT NULL,
    intent_topic TEXT,
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ۴. پیشخوان تسبیحات کاربر (Tasbih Records)
CREATE TABLE IF NOT EXISTS tasbih_records (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    preset_name VARCHAR(100) NOT NULL,
    total_count BIGINT DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_user_preset UNIQUE (telegram_id, preset_name)
);

-- ۵. آمار کلی سیستم (Bot Stats)
CREATE TABLE IF NOT EXISTS bot_stats (
    metric_key VARCHAR(100) PRIMARY KEY,
    metric_value BIGINT DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ۶. گزارش خطاها و رخدادها (System Logs)
CREATE TABLE IF NOT EXISTS system_logs (
    id BIGSERIAL PRIMARY KEY,
    level VARCHAR(20) NOT NULL,
    module VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====================================================================
-- ایندکس‌ها جهت بهینه‌سازی کوئری‌ها
-- ====================================================================
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_notifications ON users(notifications_enabled) WHERE notifications_enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_groups_is_active ON groups(is_active);
CREATE INDEX IF NOT EXISTS idx_istikhara_user ON istikhara_history(telegram_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_istikhara_fav ON istikhara_history(telegram_id, is_favorite) WHERE is_favorite = TRUE;
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON system_logs(created_at DESC);

-- مقداردهی اولیه متریک‌ها
INSERT INTO bot_stats (metric_key, metric_value) VALUES
    ('total_users', 0),
    ('total_groups', 0),
    ('total_istikharas', 0),
    ('total_quran_searches', 0),
    ('total_tasbih_counts', 0)
ON CONFLICT (metric_key) DO NOTHING;

-- ====================================================================
-- امنیت سطح ردیف (Row Level Security - RLS) برای Supabase
-- ====================================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE istikhara_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasbih_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE bot_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_logs ENABLE ROW LEVEL SECURITY;

-- سیاست پیش‌فرض: سرویس بات با service_role دسترسی کامل دارد
DROP POLICY IF EXISTS service_role_all ON users;
CREATE POLICY service_role_all ON users FOR ALL USING (true);

DROP POLICY IF EXISTS service_role_all ON groups;
CREATE POLICY service_role_all ON groups FOR ALL USING (true);

DROP POLICY IF EXISTS service_role_all ON istikhara_history;
CREATE POLICY service_role_all ON istikhara_history FOR ALL USING (true);

DROP POLICY IF EXISTS service_role_all ON tasbih_records;
CREATE POLICY service_role_all ON tasbih_records FOR ALL USING (true);

DROP POLICY IF EXISTS service_role_all ON bot_stats;
CREATE POLICY service_role_all ON bot_stats FOR ALL USING (true);

DROP POLICY IF EXISTS service_role_all ON system_logs;
CREATE POLICY service_role_all ON system_logs FOR ALL USING (true);

import sqlite3
import os
from datetime import datetime, timezone, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")
TZ_TASHKENT = timezone(timedelta(hours=5))


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            phone TEXT,
            gender TEXT,
            first_name TEXT,
            username TEXT,
            photo_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Eski bazaga yangi ustunlar qo'shish
    try:
        conn.execute("ALTER TABLE users ADD COLUMN username TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE users ADD COLUMN photo_url TEXT")
    except sqlite3.OperationalError:
        pass

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tariffs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            mock_count INTEGER NOT NULL DEFAULT 1,
            price INTEGER NOT NULL,
            description TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Default tariflar (agar bo'sh bo'lsa)
    cnt = conn.execute("SELECT COUNT(*) FROM tariffs").fetchone()[0]
    if cnt == 0:
        conn.execute(
            "INSERT INTO tariffs (title, mock_count, price, description, is_active, sort_order) VALUES (?, ?, ?, ?, 1, 1)",
            ("1 ta mock", 1, 39000, "Bitta mock imtihon"),
        )
        conn.execute(
            "INSERT INTO tariffs (title, mock_count, price, description, is_active, sort_order) VALUES (?, ?, ?, ?, 1, 2)",
            ("3 ta mock", 3, 99000, "Uchta mock imtihon — tejamkor"),
        )

    # User mocks (har til uchun alohida)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_mocks (
            telegram_id INTEGER NOT NULL,
            language TEXT NOT NULL,
            mock_count INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (telegram_id, language)
        )
    """)
    conn.commit()
    conn.close()


def add_user(telegram_id, phone, gender, first_name, username="", photo_url=""):
    # Telefon raqam oldiga + qo'shish
    if phone and not phone.startswith("+"):
        phone = "+" + phone
    now = datetime.now(TZ_TASHKENT).strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO users (telegram_id, phone, gender, first_name, username, photo_url, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (telegram_id, phone, gender, first_name, username, photo_url, now),
    )
    conn.commit()
    conn.close()


def update_user_gender(telegram_id, gender):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE users SET gender=? WHERE telegram_id=?", (gender, telegram_id))
    conn.commit()
    conn.close()


def update_user_phone(telegram_id, phone, first_name="", username="", photo_url=""):
    """Mini App'dan contact kelganda — phone, name, photo saqlash/yangilash"""
    if phone and not phone.startswith("+"):
        phone = "+" + phone
    now = datetime.now(TZ_TASHKENT).strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    existing = conn.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()
    if existing:
        conn.execute(
            "UPDATE users SET phone=?, first_name=?, username=?, photo_url=? WHERE telegram_id=?",
            (phone, first_name, username, photo_url, telegram_id),
        )
    else:
        conn.execute(
            "INSERT INTO users (telegram_id, phone, first_name, username, photo_url, gender, created_at) VALUES (?, ?, ?, ?, ?, '', ?)",
            (telegram_id, phone, first_name, username, photo_url, now),
        )
    conn.commit()
    conn.close()


def delete_user(telegram_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
    conn.commit()
    conn.close()


def get_user(telegram_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    user = conn.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()
    conn.close()
    return dict(user) if user else None


def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    users = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(u) for u in users]


def get_user_count():
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return count


# ===== TARIFFS =====
def get_all_tariffs(active_only=False):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if active_only:
        rows = conn.execute(
            "SELECT * FROM tariffs WHERE is_active = 1 ORDER BY sort_order, id"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM tariffs ORDER BY sort_order, id"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_tariff(tariff_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM tariffs WHERE id = ?", (tariff_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_tariff(title, mock_count, price, description="", is_active=1, sort_order=0):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO tariffs (title, mock_count, price, description, is_active, sort_order) VALUES (?, ?, ?, ?, ?, ?)",
        (title, mock_count, price, description, is_active, sort_order),
    )
    conn.commit()
    conn.close()


def update_tariff(tariff_id, title, mock_count, price, description="", is_active=1, sort_order=0):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE tariffs SET title=?, mock_count=?, price=?, description=?, is_active=?, sort_order=? WHERE id=?",
        (title, mock_count, price, description, is_active, sort_order, tariff_id),
    )
    conn.commit()
    conn.close()


def delete_tariff(tariff_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM tariffs WHERE id = ?", (tariff_id,))
    conn.commit()
    conn.close()


# ===== USER MOCKS =====
LANGUAGES = ("arabic", "turkish", "english")


def get_user_mocks(telegram_id):
    """Har til uchun mock count qaytaradi (default 0)."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT language, mock_count FROM user_mocks WHERE telegram_id = ?",
        (telegram_id,),
    ).fetchall()
    conn.close()
    result = {lang: 0 for lang in LANGUAGES}
    for lang, cnt in rows:
        if lang in result:
            result[lang] = cnt
    return result


def set_user_mocks(telegram_id, language, count):
    if language not in LANGUAGES:
        raise ValueError(f"Unknown language: {language}")
    count = max(0, int(count))
    now = datetime.now(TZ_TASHKENT).strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO user_mocks (telegram_id, language, mock_count, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(telegram_id, language) DO UPDATE SET
            mock_count = excluded.mock_count,
            updated_at = excluded.updated_at
        """,
        (telegram_id, language, count, now),
    )
    conn.commit()
    conn.close()
    return count


def adjust_user_mocks(telegram_id, language, delta):
    """Mock sonini +delta qiladi (manfiy bo'lsa kamaytiradi, 0 dan past bo'lmaydi)."""
    if language not in LANGUAGES:
        raise ValueError(f"Unknown language: {language}")
    current = get_user_mocks(telegram_id)[language]
    new_val = max(0, current + int(delta))
    return set_user_mocks(telegram_id, language, new_val)


def get_all_users_with_mocks():
    """Foydalanuvchilar + har til uchun mock count."""
    users = get_all_users()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT telegram_id, language, mock_count FROM user_mocks"
    ).fetchall()
    conn.close()

    mocks_by_user = {}
    for tid, lang, cnt in rows:
        mocks_by_user.setdefault(tid, {lang_: 0 for lang_ in LANGUAGES})
        mocks_by_user[tid][lang] = cnt

    for u in users:
        u["mocks"] = mocks_by_user.get(
            u["telegram_id"], {lang: 0 for lang in LANGUAGES}
        )
    return users


init_db()

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


init_db()

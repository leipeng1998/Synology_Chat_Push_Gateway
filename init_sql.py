import sqlite3

DB_FILE = "push_gateway.db"

# 初始化表（如果还没建）
def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS push_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            is_banned INTEGER DEFAULT 0,
            user_name TEXT UNIQUE,
            user_password TEXT,
            sid TEXT,
            GOTIFY_URL TEXT,
            GOTIFY_TOKEN TEXT
        )
        """)
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS channel_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    is_banned INTEGER DEFAULT 0,
                    channel_id TEXT UNIQUE,
                    channel_name TEXT,
                    channel_member TEXT,
                    channel_type TEXT
                )
                """)
        cursor.execute("""
                        CREATE TABLE IF NOT EXISTS user_info (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            is_banned INTEGER DEFAULT 0,
                            user_id TEXT UNIQUE,
                            user_nickname TEXT,
                            user_login_name TEXT,
                            user_type TEXT
                        )
                        """)
        conn.commit()
    except sqlite3.Error as e:
        print("数据库初始化错误:", e)
    finally:
        conn.close()
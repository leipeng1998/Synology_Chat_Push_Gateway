import sqlite3

DB_FILE = "push_gateway.db"

# 初始化表（如果还没建）
def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # push_users
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
        # channel_info
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
        # user_id
        cursor.execute("""
                        CREATE TABLE IF NOT EXISTS user_info (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id TEXT UNIQUE,
                            nickname TEXT,
                            username TEXT,
                            type TEXT
                        )
                        """)
        conn.commit()
    except sqlite3.Error as e:
        print("数据库初始化错误:", e)
    finally:
        conn.close()


def init_app():
    pass
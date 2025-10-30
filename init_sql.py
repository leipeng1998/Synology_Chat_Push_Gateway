import sqlite3
import logging

DB_FILE = "push_gateway.db"
logger = logging.getLogger(__name__)


# 初始化表（如果还没建）
def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # push_users 表
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

        # channel_info 表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS channel_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            is_banned INTEGER DEFAULT 0,
            channel_id TEXT UNIQUE,
            channel_name TEXT,
            members TEXT,
            channel_member TEXT,
            channel_type TEXT
        )
        """)

        # user_info 表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE,
            nickname TEXT,
            username TEXT,
            user_type TEXT
        )
        """)

        # 消息推送记录表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT,
            message_id TEXT,
            message_content TEXT,
            creator_id TEXT,
            create_at INTEGER,
            is_pushed INTEGER DEFAULT 0,
            push_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(channel_id, message_id)
        )
        """)

        # 系统配置表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT UNIQUE,
            config_value TEXT,
            description TEXT,
            updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        logger.info("所有数据库表结构初始化完成")

        # 检查表是否创建成功
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logger.info(f"数据库中的表: {[table[0] for table in tables]}")

    except sqlite3.Error as e:
        logger.error(f"数据库初始化错误: {e}")
        raise
    finally:
        if conn:
            conn.close()


def check_tables_exist():
    """检查所有必要的表是否存在"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        required_tables = ['push_users', 'channel_info', 'user_info', 'message_history', 'system_config']
        existing_tables = []

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        existing_tables = [table[0] for table in tables]

        missing_tables = [table for table in required_tables if table not in existing_tables]

        if missing_tables:
            logger.warning(f"缺少表: {missing_tables}")
            return False
        else:
            logger.info("所有必要的表都存在")
            return True

    except sqlite3.Error as e:
        logger.error(f"检查表存在性失败: {e}")
        return False
    finally:
        if conn:
            conn.close()


def init_app():
    """应用初始化，确保数据库表结构完整"""
    try:
        init_db()
        if check_tables_exist():
            logger.info("数据库初始化成功")
            return True
        else:
            logger.error("数据库表结构不完整")
            return False
    except Exception as e:
        logger.error(f"应用初始化失败: {e}")
        return False
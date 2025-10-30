"""
Synology Chat Push Gateway
Copyright 2024 leipeng1998

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import sqlite3
from typing import Dict

import logging
logger = logging.getLogger(__name__)
DB_FILE = "push_gateway.db"

# ======================== 推送用户 ======================== #
def add_push_users_info(user_name, user_password, sid=None, GOTIFY_URL=None, GOTIFY_TOKEN=None):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 检查用户是否存在
        cursor.execute("SELECT id FROM push_users WHERE user_name = ?", (str(user_name),))
        existing_user = cursor.fetchone()

        if existing_user:
            # 用户存在 → 更新
            cursor.execute("""
                UPDATE push_users 
                SET user_password = ?, sid = ?, GOTIFY_URL = ?, GOTIFY_TOKEN = ? 
                WHERE user_name = ?
            """, (str(user_password), str(sid), str(GOTIFY_URL), str(GOTIFY_TOKEN), str(user_name)))
            print(f"用户 {user_name} 更新成功")
        else:
            # 不存在 → 插入新用户
            cursor.execute("""
                INSERT INTO push_users (user_name, user_password, sid, GOTIFY_URL, GOTIFY_TOKEN)
                VALUES (?, ?, ?, ?, ?)
            """, (str(user_name), str(user_password), str(sid), str(GOTIFY_URL), str(GOTIFY_TOKEN)))
            print(f"用户 {user_name} 插入成功")

        conn.commit()
    except sqlite3.Error as e:
        print(f"写入用户 {user_name} 失败:", e)
    finally:
        if conn:
            conn.close()

# 更新SID的函数
def update_user_sid(username: str, new_sid: str) -> bool:
    """
    更新用户的SID

    Args:
        username: 用户名
        new_sid: 新的会话ID

    Returns:
        bool: 更新是否成功
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE push_users 
            SET sid = ? 
            WHERE user_name = ?
        """, (new_sid, username))

        conn.commit()
        success = cursor.rowcount > 0

        if success:
            logger.info(f"用户 {username} 的SID更新成功")
        else:
            logger.warning(f"用户 {username} 不存在，无法更新SID")

        return success

    except sqlite3.Error as e:
        logger.error(f"更新用户SID失败: {e}")
        return False
    finally:
        if conn:
            conn.close()
# ======================== 频道信息 ======================== #
def add_channel_info(channel_id, channel_name=None, channel_member=None, channel_type=None):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT channel_id FROM channel_info WHERE channel_id = ?", (channel_id,))
        existing_channel = cursor.fetchone()

        if existing_channel:
            cursor.execute("""
                UPDATE channel_info 
                SET channel_name = ?, channel_member = ?, channel_type = ?
                WHERE channel_id = ?
            """, (str(channel_name), str(channel_member), str(channel_type), channel_id))
            print(f"频道号 {channel_id}, 名称 {channel_name} 更新成功")
        else:
            cursor.execute("""
                INSERT INTO channel_info (channel_id, channel_name, channel_member, channel_type)
                VALUES (?, ?, ?, ?)
            """, (channel_id, str(channel_name), str(channel_member), str(channel_type)))
            print(f"频道号 {channel_id}, 名称 {channel_name} 插入成功")

        conn.commit()
    except sqlite3.Error as e:
        print(f"写入频道 {channel_id} 失败:", e)
    finally:
        if conn:
            conn.close()


# ======================== 用户表查询 ======================== #
def get_all_users():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, is_banned, user_name, user_password, GOTIFY_URL, GOTIFY_TOKEN FROM push_users")
        users = cursor.fetchall()

        print("所有用户信息：")
        for user in users:
            print(
                f"ID: {user[0]}, 用户名: {user[2]}, 封禁: {user[1]}, 密码: {user[3]}, GOTIFY_URL: {user[4]}, GOTIFY_TOKEN: {user[5]}"
            )

        return users
    except sqlite3.Error as e:
        print(f"查询所有用户失败:", e)
        return []
    finally:
        if conn:
            conn.close()
def get_all_users_no_password():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, is_banned, user_name, GOTIFY_URL, GOTIFY_TOKEN FROM push_users")
        users = cursor.fetchall()

        print("所有用户信息：")
        for user in users:
            print(
                f"ID: {user[0]}, 用户名: {user[2]}, 封禁: {user[1]}, GOTIFY_URL: {user[3]}, GOTIFY_TOKEN: {user[4]}"
            )

        return users
    except sqlite3.Error as e:
        print(f"查询所有用户失败:", e)
        return []
    finally:
        if conn:
            conn.close()
def get_user_info():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, is_banned, user_name,sid, GOTIFY_URL, GOTIFY_TOKEN FROM push_users")
        users = cursor.fetchall()
        return users

    except sqlite3.Error as e:
        print(f"查询所有用户主要信息失败:", e)
        return []
    finally:
        if conn:
            conn.close()
def get_user_by_name(user_name):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM push_users WHERE user_name = ?", (str(user_name),))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"查询用户 {user_name} 失败:", e)
        return None
    finally:
        if conn:
            conn.close()


def get_user_by_id(user_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM push_users WHERE id = ?", (user_id,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"查询用户 {user_id} 失败:", e)
        return None
    finally:
        if conn:
            conn.close()


def update_user_status(user_id, new_status):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE push_users SET is_banned = ? WHERE id = ?", (new_status, user_id))
    conn.commit()
    conn.close()


def update_push_users_info(user_id, username, password, gotify_url, gotify_token):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE push_users 
        SET user_name = ?, user_password = ?, GOTIFY_URL = ?, GOTIFY_TOKEN = ? 
        WHERE id = ?
    """, (username, password, gotify_url, gotify_token, user_id))
    conn.commit()
    conn.close()


# ======================== DSM 用户和频道 ======================== #
def add_dsm_users_info(user_id, nickname, username, user_type):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM user_info WHERE user_id = ?", (str(user_id),))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.execute("""
                UPDATE user_info 
                SET nickname = ?, username = ?, user_type = ?
                WHERE user_id = ?
            """, (str(nickname), str(username), str(user_type), str(user_id)))
            print(f"用户 user_id={user_id}, username={username}, nickname={nickname} 更新成功")
        else:
            cursor.execute("""
                INSERT INTO user_info (user_id, nickname, username, user_type)
                VALUES (?, ?, ?, ?)
            """, (str(user_id), str(nickname), str(username), str(user_type)))
            print(f"用户 user_id={user_id}, username={username}, nickname={nickname} 插入成功")

        conn.commit()
    except sqlite3.Error as e:
        print(f"写入用户 user_id={user_id} 失败:", e)
    finally:
        if conn:
            conn.close()

def search_dsm_user_id_by_username(username):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_info WHERE username = ?", (username,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"查询用户 {username} 失败:", e)
        return None
    finally:
        if conn:
            conn.close()

def search_dsm_user_id_by_id(user_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_info WHERE user_id = ?", (user_id,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"查询用户 {user_id} 失败:", e)
        return None
    finally:
        if conn:
            conn.close()



def add_dsm_channel_info(channel_id, channel_name, members,channel_member, channel_type):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM channel_info WHERE channel_id = ?", (str(channel_id),))
        existing_channel = cursor.fetchone()

        if existing_channel:
            cursor.execute("""
                UPDATE channel_info 
                SET channel_name = ?,members=?, channel_member = ?, channel_type = ?
                WHERE channel_id = ?
            """, (str(channel_name), str(channel_member), str(members), str(channel_type), str(channel_id)))
            print(f"channel_id={channel_id}, channel_name={channel_name} 更新成功")
        else:
            cursor.execute("""
                INSERT INTO channel_info (channel_id, channel_name, members,channel_member, channel_type)
                VALUES (?, ?, ?, ?,?)
            """, (str(channel_id), str(channel_name), str(members), str(channel_member), str(channel_type)))
            print(f"channel_id={channel_id}, channel_name={channel_name} 插入成功")

        conn.commit()
    except sqlite3.Error as e:
        print(f"channel_id={channel_id}, channel_name={channel_name} 写入失败:", e)
    finally:
        if conn:
            conn.close()

def search_channel_by_id(channel_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM channel_info WHERE channel_id = ?", (channel_id,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"查询频道 {channel_id} 失败:", e)
        return None
    finally:
        if conn:
            conn.close()


# ======================== 消息推送记录 ======================== #
def add_message_history(channel_id, message_id, message_content, creator_id, create_at):
    """添加消息记录"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO message_history 
            (channel_id, message_id, message_content, creator_id, create_at)
            VALUES (?, ?, ?, ?, ?)
        """, (str(channel_id), str(message_id), str(message_content), str(creator_id), create_at))

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"添加消息记录失败: {e}")
        return False
    finally:
        if conn:
            conn.close()


def mark_message_as_pushed(channel_id, message_id):
    """标记消息为已推送"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE message_history 
            SET is_pushed = 1, push_time = CURRENT_TIMESTAMP
            WHERE channel_id = ? AND message_id = ?
        """, (str(channel_id), str(message_id)))

        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"标记消息为已推送失败: {e}")
        return False
    finally:
        if conn:
            conn.close()


def is_message_pushed(channel_id, message_id):
    """检查消息是否已推送"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT is_pushed FROM message_history 
            WHERE channel_id = ? AND message_id = ?
        """, (str(channel_id), str(message_id)))

        result = cursor.fetchone()
        return result and result[0] == 1
    except sqlite3.Error as e:
        print(f"检查消息推送状态失败: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_unpushed_messages(channel_id=None):
    """获取未推送的消息"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        if channel_id:
            cursor.execute("""
                SELECT * FROM message_history 
                WHERE is_pushed = 0 AND channel_id = ?
                ORDER BY create_at ASC
            """, (str(channel_id),))
        else:
            cursor.execute("""
                SELECT * FROM message_history 
                WHERE is_pushed = 0 
                ORDER BY create_at ASC
            """)

        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"获取未推送消息失败: {e}")
        return []
    finally:
        if conn:
            conn.close()


# ======================== 系统配置管理 ======================== #
def set_system_config(config_key: str, config_value: str, description: str = "") -> bool:
    """
    设置系统配置项

    Args:
        config_key: 配置键
        config_value: 配置值
        description: 配置描述

    Returns:
        bool: 操作是否成功
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO system_config 
            (config_key, config_value, description, updated_time)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (config_key, config_value, description))

        conn.commit()
        logger.info(f"系统配置已更新: {config_key} = {config_value}")
        return True

    except sqlite3.Error as e:
        logger.error(f"设置系统配置失败 {config_key}: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_system_config(config_key: str, default_value: str = None) -> str:
    """
    获取系统配置项

    Args:
        config_key: 配置键
        default_value: 默认值（当配置不存在时返回）

    Returns:
        str: 配置值，如果不存在则返回默认值
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT config_value FROM system_config 
            WHERE config_key = ?
        """, (config_key,))

        result = cursor.fetchone()
        if result:
            logger.debug(f"获取系统配置: {config_key} = {result[0]}")
            return result[0]
        else:
            logger.warning(f"系统配置不存在: {config_key}，使用默认值: {default_value}")
            return default_value

    except sqlite3.Error as e:
        logger.error(f"获取系统配置失败 {config_key}: {e}")
        return default_value
    finally:
        if conn:
            conn.close()


def get_all_system_config() -> Dict[str, str]:
    """
    获取所有系统配置

    Returns:
        Dict: 配置键值对字典
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT config_key, config_value FROM system_config")
        results = cursor.fetchall()

        config_dict = {row[0]: row[1] for row in results}
        logger.debug(f"获取所有系统配置，共 {len(config_dict)} 项")
        return config_dict

    except sqlite3.Error as e:
        logger.error(f"获取所有系统配置失败: {e}")
        return {}
    finally:
        if conn:
            conn.close()


def delete_system_config(config_key: str) -> bool:
    """
    删除系统配置项

    Args:
        config_key: 配置键

    Returns:
        bool: 操作是否成功
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM system_config WHERE config_key = ?", (config_key,))
        conn.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"系统配置已删除: {config_key}")
        else:
            logger.warning(f"系统配置不存在，无法删除: {config_key}")

        return deleted

    except sqlite3.Error as e:
        logger.error(f"删除系统配置失败 {config_key}: {e}")
        return False
    finally:
        if conn:
            conn.close()


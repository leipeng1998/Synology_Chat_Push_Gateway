import sqlite3

DB_FILE = "push_gateway.db"

# 写入推送用户信息
def add_push_users_info(user_name, user_password, sid=None, GOTIFY_URL=None, GOTIFY_TOKEN=None):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 先检查用户是否存在
        cursor.execute("SELECT id FROM push_users WHERE user_name = ?", (str(user_name),))
        existing_user = cursor.fetchone()

        if existing_user:
            # 用户存在，更新记录（保持原ID）
            cursor.execute("""
            UPDATE push_users 
            SET user_password = ?, sid = ?, GOTIFY_URL=?,GOTIFY_TOKEN = ? 
            WHERE user_name = ?
            """, (str(user_name), str(user_password), str(sid), str(GOTIFY_TOKEN)))
            print(f"用户 {user_name} 更新成功")
        else:
            # 用户不存在，插入新记录
            cursor.execute("""
            INSERT INTO push_users (user_name, user_password, sid,GOTIFY_URL, GOTIFY_TOKEN)
            VALUES (?, ?, ?, ?,?)
            """, (str(user_name), str(user_password), str(sid),str(GOTIFY_URL), str(GOTIFY_TOKEN)))
            print(f"用户 {user_name} 插入成功")

        conn.commit()
    except sqlite3.Error as e:
        print(f"写入用户 {user_name} 失败:", e)
    finally:
        if conn:
            conn.close()

# 更新推送用户信息
# def update_push_users_info(user_name, new_password=None, new_sid = None,new_GOTIFY_URL=None, new_GOTIFY_TOKEN=None):
#     try:
#         conn = sqlite3.connect(DB_FILE)
#         cursor = conn.cursor()
#
#         updates = []
#         params = []
#
#         if new_password is not None:
#             updates.append("user_password = ?")
#             params.append(str(new_password))
#         if new_GOTIFY_URL is not None:
#             updates.append("GOTIFY_URL = ?")
#             params.append(str(new_GOTIFY_URL))
#         if new_GOTIFY_TOKEN is not None:
#             updates.append("GOTIFY_TOKEN = ?")
#             params.append(str(new_GOTIFY_TOKEN))
#         if new_sid is not None:
#             updates.append("sid = ?")
#             params.append(str(new_sid))
#
#         if updates:
#             params.append(str(user_name))
#             cursor.execute(f"""
#                 UPDATE push_users
#                 SET {', '.join(updates)}
#                 WHERE user_name = ?
#                 """, params)
#
#         conn.commit()
#         if cursor.rowcount > 0:
#             print(f"用户 {user_name} 信息更新成功")
#         else:
#             print(f"用户 {user_name} 不存在")
#
#     except sqlite3.Error as e:
#         print(f"更新用户 {user_name} 信息失败:", e)
#     finally:
#         if conn:
#             conn.close()

def add_channel_info(channel_id, channel_name=None, channel_member=None, channel_type=None):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 先检查频道是否存在
        cursor.execute("SELECT channel_id FROM channel_info WHERE channel_id = ?", (channel_id,))
        existing_channel = cursor.fetchone()

        if existing_channel:
            # 存在则更新
            cursor.execute("""
            UPDATE channel_info 
            SET channel_name = ?, channel_member = ?, channel_type = ?
            WHERE channel_id = ?
            """, (str(channel_name), str(channel_member), str(channel_type), channel_id))
            print(f"频道号 {channel_id}, 名称 {channel_name} 更新成功")
        else:
            # 不存在则插入
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

# 查询所有用户
def get_all_users():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id,is_banned,user_name,user_password,GOTIFY_URL,GOTIFY_TOKEN  FROM push_users")
        users = cursor.fetchall()

        print("所有用户信息：")
        for user in users:
            print(user)

            print(
                f"ID: {user[0]}, 用户名: {user[2]}, 封禁: {user[1]}, 密码: {user[3]},  GOTIFY_URL: {user[4]}, GOTIFY_TOKEN: {user[5]}")

        return users
    except sqlite3.Error as e:
        print(f"查询所有用户失败:", e)
        return []
    finally:
        if conn:
            conn.close()

#查询用户名
def get_user_by_name(user_name):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM push_users WHERE user_name = ?", (str(user_name),))
        user = cursor.fetchone()

        if user:
            print(f"用户 {user_name} 的信息：")
            print(f"  ID: {user[0]}")
            print(f"  封禁状态: {'是' if user[1] == 1 else '否'}")
            print(f"  用户名: {user[2]}")
            print(f"  密码: {user[3]}")
            print(f"  SID: {user[4]}")
            print(f"  Push Token: {user[5]}")
            return user
        else:
            print(f"用户 {user_name} 不存在")
            return None

    except sqlite3.Error as e:
        print(f"查询用户 {user_name} 失败:", e)
        return None
    finally:
        if conn:
            conn.close()

#查询用户名
def get_user_by_id(user_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM push_users WHERE id = ?", (str(user_id),))
        user = cursor.fetchone()

        if user:
            print(f"用户 {user_id} 的信息：")
            print(f"  ID: {user[0]}")
            print(f"  封禁状态: {'是' if user[1] == 1 else '否'}")
            print(f"  用户名: {user[2]}")
            print(f"  密码: {user[3]}")
            print(f"  SID: {user[4]}")
            print(f"  Push Token: {user[5]}")
            return user
        else:
            print(f"用户 {user_id} 不存在")
            return None

    except sqlite3.Error as e:
        print(f"查询用户 {user_id} 失败:", e)
        return None
    finally:
        if conn:
            conn.close()

def update_user_status(user_id,new_status):
    """
        更新用户启用/封禁状态
        :param user_id: 用户ID
        :param status: 0=启用, 1=封禁
        """
    conn = sqlite3.connect("push_gateway.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE push_users SET is_banned = ? WHERE id = ?", (new_status, user_id))
    conn.commit()
    conn.close()


def update_push_users_info(user_id, username, password, gotify_url, gotify_token):
    """
        更新用户信息
        :param user_id: 用户ID
        :param
        """
    conn = sqlite3.connect("push_gateway.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE push_users SET user_name = ?, user_password = ? ,GOTIFY_URL = ?, GOTIFY_TOKEN = ? WHERE id = ?", (username,password, gotify_url, gotify_token, user_id))
    conn.commit()
    conn.close()


# init_db()
# update_push_users_info(2221212121212,new_sid=236,new_GOTIFY_URL='121212')
# add_push_users_info("user2", "prd456")
# add_push_users_info(2,22,33)
# get_all_users()
# add_channel_info(1)
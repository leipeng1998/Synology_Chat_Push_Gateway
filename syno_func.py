"""
群晖消息推送网关核心功能模块
提供与群晖Chat API的交互、消息监控和推送功能
"""

import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

import requests
import urllib3

import use_sql
from use_sql import add_dsm_users_info

# 配置日志
logger = logging.getLogger(__name__)

# 全局常量
REQUEST_TIMEOUT = 30  # 请求超时时间（秒）

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_base_url() -> str:
    """
    从数据库获取群晖BASE_URL

    Returns:
        str: 群晖服务器地址

    Raises:
        Exception: 当BASE_URL未配置时抛出异常
    """
    base_url = use_sql.get_system_config("BASE_URL")
    if not base_url:
        error_msg = "BASE_URL未在系统配置中设置，请先完成系统初始化"
        logger.error(error_msg)
        raise Exception(error_msg)

    # 确保URL格式正确
    if not base_url.startswith(('http://', 'https://')):
        base_url = f"https://{base_url}"

    # 移除末尾的斜杠
    base_url = base_url.rstrip('/')

    logger.debug(f"使用BASE_URL: {base_url}")
    return base_url


def get_syno_sid(username: str, password: str) -> str:
    """
    获取群晖API的SID（会话ID）

    Args:
        username: 用户名
        password: 密码

    Returns:
        str: 有效的SID字符串

    Raises:
        Exception: 登录失败时抛出异常
    """
    base_url = get_base_url()
    logger.info(f"开始获取SID，用户: {username}, URL: {base_url}")

    auth_url = f"{base_url}/webapi/auth.cgi"
    params = {
        "api": "SYNO.API.Auth",
        "method": "login",
        "version": "7",
        "account": username,
        "passwd": password,
        "session": "Chat",
        "format": "sid"
    }

    try:
        resp = requests.get(auth_url, params=params, verify=False, timeout=REQUEST_TIMEOUT)
        data = resp.json()

        if data.get("success"):
            sid = data["data"]["sid"]
            logger.info(f"获取SID成功: {sid}")
            return sid
        else:
            error_msg = f"群晖登录失败: {data}"
            logger.error(error_msg)
            raise Exception(error_msg)

    except requests.exceptions.RequestException as e:
        error_msg = f"请求群晖API失败: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


def get_user_info(sid: str) -> None:
    """
    获取群晖用户信息并保存到数据库

    Args:
        sid: 会话ID
    """
    base_url = get_base_url()
    logger.info("开始获取群晖用户信息")

    url = f"{base_url}/webapi/entry.cgi"
    payload = {
        "api": "SYNO.Chat.User",
        "method": "list",
        "version": 3,
        "_sid": sid
    }

    try:
        resp = requests.post(url, data=payload, verify=False, timeout=REQUEST_TIMEOUT)
        data = resp.json()

        if data.get("success"):
            users = data["data"]["users"]
            user_count = 0

            for user in users:
                # 只处理有效用户（type不为空的用户）
                if user.get('type') != "":
                    add_dsm_users_info(
                        user['user_id'],
                        user.get('nickname', ''),
                        user.get('username', ''),
                        user.get('type', '')
                    )
                    user_count += 1

            logger.info(f"用户信息同步完成，共处理 {user_count} 个用户")
        else:
            logger.error(f"获取用户信息失败: {data}")

    except requests.exceptions.RequestException as e:
        logger.error(f"请求用户信息失败: {str(e)}")


def write_channel_info_sql(sid: str) -> None:
    """
    获取群晖频道信息并保存到数据库

    Args:
        sid: 会话ID
    """
    base_url = get_base_url()
    logger.info("开始获取群晖频道信息")

    url = f"{base_url}/webapi/entry.cgi"
    payload = {
        "api": "SYNO.Chat.Channel",
        "method": "list",
        "version": "2",
        "_sid": sid
    }

    try:
        resp = requests.post(url, data=payload, verify=False, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        channels = resp.json()["data"]["channels"]
        channel_count = 0

        for channel in channels:
            use_sql.add_dsm_channel_info(
                channel["channel_id"],
                channel.get("name", ""),
                channel.get("members", []),
                channel["total_member_count"],
                channel['type']
            )
            channel_count += 1

        logger.info(f"频道信息同步完成，共处理 {channel_count} 个频道")

    except requests.exceptions.RequestException as e:
        logger.error(f"请求频道信息失败: {str(e)}")
    except Exception as e:
        logger.error(f"处理频道信息失败: {str(e)}")


def message_send(gotify_url: str, token: str, title: str, message: str) -> bool:
    """
    通过Gotify发送推送消息

    Args:
        gotify_url: Gotify服务器URL
        token: Gotify访问令牌
        title: 消息标题
        message: 消息内容

    Returns:
        bool: 发送是否成功
    """
    logger.debug(f"准备发送Gotify消息，标题: {title}")

    payload = {
        "title": title,
        "message": message,
        "priority": 2
    }

    try:
        resp = requests.post(f"{gotify_url}?token={token}", data=payload, timeout=REQUEST_TIMEOUT)
        result = resp.json()

        if resp.status_code == 200:
            logger.info(f"Gotify消息发送成功: {title}")
            return True
        else:
            logger.error(f"Gotify消息发送失败: {result}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Gotify请求失败: {str(e)}")
        return False


def get_channels(sid: str) -> List[Dict[str, Any]]:
    """
    获取用户的所有频道信息（包含未读消息数）
    """
    base_url = get_base_url()
    logger.debug("开始获取频道列表")

    url = f"{base_url}/webapi/entry.cgi"
    payload = {
        "api": "SYNO.Chat.Channel",
        "method": "list",
        "version": 5,
        "limit": 100,
        "offset": 0,
        "additional": '["unread"]',
        "_sid": sid
    }

    try:
        resp = requests.post(url, data=payload, verify=False, timeout=REQUEST_TIMEOUT)
        data = resp.json()

        # 更详细的错误日志
        if not data.get("success"):
            error_code = data.get("error", {}).get("code")
            error_msg = f"获取频道列表失败: {data}, 错误代码: {error_code}"
            logger.error(error_msg)
            raise Exception(error_msg)

        channels = data["data"]["channels"]
        logger.debug(f"成功获取 {len(channels)} 个频道")
        return channels

    except requests.exceptions.RequestException as e:
        error_msg = f"请求频道列表失败: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


def get_display_name(user_info_tuple: tuple) -> str:
    """
    根据用户信息获取显示名称，优先使用nickname

    Args:
        user_info_tuple: 用户信息元组 (id, user_id, nickname, username, user_type)

    Returns:
        str: 显示名称
    """
    if not user_info_tuple or len(user_info_tuple) < 5:
        return "未知用户"

    nickname = user_info_tuple[2]  # nickname
    username = user_info_tuple[3]  # username

    # 优先使用nickname，如果没有或为空则使用username
    if nickname and nickname.strip():
        return nickname.strip()
    elif username and username.strip():
        return username.strip()
    else:
        return "未知用户"


# 然后在 process_single_message 中使用这个辅助函数
def process_single_message(channel_id: str, channel_name: str, message_data: Dict[str, Any], user_info: tuple) -> bool:
    """
    处理单条消息并推送（使用辅助函数版本）
    """
    try:
        message_id = message_data["message_id"]
        message_content = message_data["content"]
        creator_id = message_data["creator_id"]

        logger.info(f"开始处理消息: 频道={channel_name}, 消息ID={message_id}")

        # 首先获取频道信息来判断频道类型
        channel_info = use_sql.search_channel_by_id(channel_id)

        if not channel_info:
            logger.warning(f"未找到频道信息: {channel_id}")
            return False

        # 获取频道类型
        # channel_info 结构: (id, is_banned, channel_id, channel_name, members, channel_member, channel_type)
        channel_type = channel_info[6] if len(channel_info) > 6 else None

        logger.debug(f"频道类型: {channel_type}, 频道名称: {channel_name}")

        # 私聊频道处理 (anonymous)
        if channel_type == 'anonymous':
            logger.debug(f"处理私聊频道: {channel_id}")

            members_str = channel_info[4]  # members字段
            if members_str:
                # 解析成员列表
                members = [int(x.strip()) for x in members_str.strip("[]").split(",")]
                current_user_id = int(use_sql.search_dsm_user_id_by_username(user_info[2])[1])

                # 检查当前用户是否在频道成员中
                if current_user_id in members:
                    # 获取其他成员（排除当前用户）
                    other_members = [m for m in members if m != current_user_id]
                    if other_members:
                        other_user = use_sql.search_dsm_user_id_by_id(other_members[0])
                        if other_user:
                            # 使用辅助函数获取显示名称
                            display_name = get_display_name(other_user)
                            title = display_name
                            final_message = f'来自{title}的消息：{message_content}'

                            # 推送消息
                            if message_send(user_info[4], user_info[5], title, final_message):
                                use_sql.mark_message_as_pushed(channel_id, message_id)
                                logger.info(f"私聊频道消息推送成功: {message_id}")
                                return True
                        else:
                            logger.warning(f"未找到对方用户信息: {other_members[0]}")
                    else:
                        logger.warning(f"私聊频道 {channel_id} 没有其他成员")
                else:
                    logger.warning(f"当前用户 {current_user_id} 不在私聊频道成员中")
            else:
                logger.warning(f"私聊频道 {channel_id} 成员信息为空")

        # 机器人频道处理 (chatbot)
        elif channel_type == 'chatbot':
            logger.debug(f"处理机器人频道: {channel_id}")

            # 机器人频道的标题直接使用频道名称
            title = f"机器人 - {channel_name}" if channel_name else "机器人频道"
            final_message = message_content

            # 推送消息
            if message_send(user_info[4], user_info[5], title, final_message):
                use_sql.mark_message_as_pushed(channel_id, message_id)
                logger.info(f"机器人频道消息推送成功: {message_id}")
                return True
            else:
                logger.error(f"机器人频道消息推送失败: {message_id}")

        # 普通群组频道处理 (其他类型)
        else:
            logger.debug(f"处理普通频道: {channel_id}")

            # 尝试获取发送者信息
            sender_info = use_sql.search_dsm_user_id_by_id(creator_id)

            if sender_info:
                # 使用辅助函数获取显示名称
                display_name = get_display_name(sender_info)
                title = f"{channel_name} - {display_name}"
            else:
                title = f"频道: {channel_name}"

            # 构建消息内容
            final_message = message_content

            # 推送消息
            if message_send(user_info[4], user_info[5], title, final_message):
                use_sql.mark_message_as_pushed(channel_id, message_id)
                logger.info(f"普通频道消息推送成功: {message_id}")
                return True
            else:
                logger.error(f"普通频道消息推送失败: {message_id}")

        logger.warning(f"消息处理失败: {message_id}")
        return False

    except Exception as e:
        logger.error(f"处理单条消息时发生错误: {str(e)}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False

def get_channel_messages(sid: str, channel_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    获取频道的多条消息

    Args:
        sid: 会话ID
        channel_id: 频道ID
        limit: 获取的消息数量

    Returns:
        List[Dict]: 消息列表
    """
    base_url = get_base_url()
    logger.debug(f"获取频道 {channel_id} 的 {limit} 条消息")

    url = f"{base_url}/webapi/entry.cgi"
    payload = {
        "api": "SYNO.Chat.Post",
        "method": "list",
        "version": 8,
        "channel_id": channel_id,
        "prev_count": limit,  # 获取多条消息
        "next_count": 0,
        "_sid": sid
    }

    try:
        resp = requests.post(url, data=payload, verify=False, timeout=REQUEST_TIMEOUT)
        data = resp.json()
        posts = data.get("data", {}).get("posts", [])

        logger.debug(f"获取到 {len(posts)} 条消息")
        return posts

    except requests.exceptions.RequestException as e:
        logger.error(f"获取频道 {channel_id} 消息失败: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"处理频道 {channel_id} 消息时发生错误: {str(e)}")
        return []


def get_unread_messages(sid: str, channel_id: str, unread_count: int) -> List[Dict[str, Any]]:
    """
    获取未读消息

    Args:
        sid: 会话ID
        channel_id: 频道ID
        unread_count: 未读消息数量

    Returns:
        List[Dict]: 未读消息列表
    """
    # 获取比未读数稍多一些的消息，确保覆盖所有未读
    limit = min(unread_count + 5, 50)  # 最多获取50条
    all_messages = get_channel_messages(sid, channel_id, limit)

    unread_messages = []
    for message in all_messages:
        message_id = message.get("id")
        if not message_id:
            message_id = f"{channel_id}_{message.get('create_at', '')}"

        message_content = message.get("message", "")
        creator_id = message.get("creator_id", "")
        create_at = message.get("create_at", 0)

        # 记录消息到数据库（如果不存在）
        use_sql.add_message_history(channel_id, message_id, message_content, creator_id, create_at)

        # 检查是否已推送
        if not use_sql.is_message_pushed(channel_id, message_id):
            # 格式化时间戳
            timestamp = datetime.fromtimestamp(int(create_at) / 1000).strftime("%Y-%m-%d %H:%M:%S")
            formatted_content = f"{message_content}"

            unread_messages.append({
                "message_id": message_id,
                "content": formatted_content,
                "creator_id": creator_id,
                "create_at": create_at,
                "is_new": True
            })

            logger.debug(f"发现未推送消息: {message_id}")
        else:
            logger.debug(f"消息已推送过，跳过: {message_id}")

    logger.info(f"频道 {channel_id} 共有 {len(unread_messages)} 条未推送消息")
    return unread_messages


def process_channel_messages(sid: str, channel_id: str, channel_name: str, user_info: tuple) -> bool:
    """
    处理指定频道的消息（处理所有未读消息）

    Args:
        sid: 会话ID
        channel_id: 频道ID
        channel_name: 频道名称
        user_info: 用户信息元组

    Returns:
        bool: 是否有新消息被处理
    """
    try:
        logger.debug(f"开始处理频道消息: {channel_name}({channel_id})")

        # 获取频道信息以确定未读数量
        channels = get_channels(sid)
        current_channel = None
        for channel in channels:
            if channel.get("channel_id") == channel_id:
                current_channel = channel
                break

        if not current_channel:
            logger.warning(f"未找到频道信息: {channel_id}")
            return False

        unread_count = current_channel.get("unread", 0)
        if unread_count == 0:
            logger.debug(f"频道 {channel_name} 没有未读消息")
            return False

        logger.info(f"开始处理频道 {channel_name} 的 {unread_count} 条未读消息")

        # 获取所有未读消息
        unread_messages = get_unread_messages(sid, channel_id, unread_count)
        print(unread_messages)
        if not unread_messages:
            logger.debug(f"频道 {channel_name} 没有未推送的新消息")
            return False

        processed_count = 0
        # 按时间顺序处理消息（从旧到新）
        for message_data in reversed(unread_messages):


            if process_single_message(channel_id, channel_name, message_data, user_info):
                processed_count += 1

        if processed_count > 0:
            logger.info(f"频道 {channel_name} 成功处理了 {processed_count} 条新消息")
            return True
        else:
            logger.warning(f"频道 {channel_name} 没有成功处理任何消息")
            return False

    except Exception as e:
        logger.error(f"处理频道 {channel_name} 消息时发生错误: {str(e)}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False


def get_channels_with_retry_improved(user_info: tuple) -> List[Dict[str, Any]]:
    """
    改进的获取频道列表函数，自动处理SID过期
    """
    if len(user_info) < 4:
        logger.error(f"用户信息不完整: {user_info}")
        return []

    username = user_info[2]  # 用户名在第三个位置
    sid = user_info[3]  # SID在第四个位置

    try:
        # 第一次尝试使用当前SID
        logger.debug(f"用户 {username} 使用当前SID获取频道列表: {sid}")
        return get_channels(sid)

    except Exception as e:
        error_msg = str(e)
        logger.warning(f"用户 {username} 获取频道列表异常: {error_msg}")

        # 改进的错误代码检测
        if 'code": 119' in error_msg or '119' in error_msg or 'session timeout' in error_msg.lower() or 'invalid session' in error_msg.lower():
            logger.warning(f"检测到SID过期(119错误)，为用户 {username} 重新登录")
            try:
                # 从数据库获取完整的用户信息（包含密码）
                user_details = use_sql.get_user_by_name(username)
                if not user_details or len(user_details) < 5:
                    logger.error(f"无法获取用户 {username} 的完整信息: {user_details}")
                    return []

                # user_details 结构: (id, is_banned, user_name, user_password, sid, GOTIFY_URL, GOTIFY_TOKEN)
                password = user_details[3]  # 密码在第四个位置

                if not password:
                    logger.error(f"用户 {username} 的密码为空")
                    return []

                logger.info(f"为用户 {username} 重新登录获取新SID")

                # 重新登录获取新的SID
                new_sid = get_syno_sid(username, password)

                # 更新数据库中的SID
                update_success = use_sql.update_user_sid(username, new_sid)
                if update_success:
                    logger.info(f"用户 {username} 的SID已更新: {new_sid}")
                else:
                    logger.error(f"用户 {username} 的SID更新失败")

                # 使用新的SID重新获取频道列表
                logger.debug(f"使用新SID重新获取频道列表: {new_sid}")
                return get_channels(new_sid)

            except Exception as login_error:
                logger.error(f"用户 {username} 重新登录失败: {str(login_error)}")
                return []
        else:
            # 其他错误
            logger.error(f"用户 {username} 获取频道列表失败（非SID问题）: {error_msg}")
            return []


def main_run() -> None:
    """
    主监控循环
    """
    logger.info("消息监控线程启动")
    loop_count = 0

    while True:
        try:
            loop_count += 1
            logger.info(f"开始第 {loop_count} 轮消息监控")

            users = use_sql.get_user_info()
            total_processed = 0

            if not users:
                logger.debug("没有找到用户，跳过本轮监控")
                time.sleep(5)
                continue

            logger.info(f"本轮检查 {len(users)} 个用户")

            for user in users:
                if len(user) < 6:
                    logger.error(f"用户信息不完整: {user}")
                    continue

                user_name = user[2]
                user_sid = user[3]

                # 跳过被封禁的用户
                if user[1] == 1:
                    logger.debug(f"用户 {user_name} 被封禁，跳过")
                    continue

                # 检查推送配置是否完整
                if not user[4] or not user[5] or user[4] == 'None' or user[5] == 'None':
                    logger.warning(f"用户 {user_name} 推送配置不完整，跳过")
                    continue

                logger.info(f"处理用户: {user_name}, SID: {user_sid[:10]}...")

                try:
                    # 使用改进的SID刷新功能
                    channels = get_channels_with_retry_improved(user)
                    user_processed = 0

                    if not channels:
                        logger.warning(f"用户 {user_name} 获取频道列表失败，可能SID无效或网络问题")
                        # 这里可以添加强制刷新SID的逻辑
                        continue

                    logger.debug(f"用户 {user_name} 成功获取 {len(channels)} 个频道")

                    for channel in channels:
                        channel_id = channel.get("channel_id", "未知频道")
                        channel_name = channel.get("name") or f"匿名频道 {channel_id}"
                        unread_count = channel.get("unread", 0)

                        if unread_count > 0:
                            logger.info(f"发现未读消息: 用户={user_name}, 频道={channel_name}, 未读数={unread_count}")

                            # 获取当前用户的最新SID（可能已经刷新）
                            current_user = use_sql.get_user_by_name(user_name)
                            current_sid = current_user[4] if current_user and len(current_user) > 4 else user_sid

                            # 处理该频道的所有未读消息
                            if process_channel_messages(current_sid, channel_id, channel_name, user):
                                user_processed += 1
                                total_processed += 1
                        else:
                            logger.debug(f"频道 {channel_name} 无未读消息")

                    if user_processed > 0:
                        logger.info(f"用户 {user_name} 处理了 {user_processed} 个频道的消息")
                    else:
                        logger.debug(f"用户 {user_name} 本轮无新消息处理")

                except Exception as e:
                    logger.error(f"处理用户 {user_name} 时发生错误: {str(e)}")
                    import traceback
                    logger.error(f"详细错误信息: {traceback.format_exc()}")
                    continue

            # 本轮监控结果汇总
            if total_processed > 0:
                logger.info(f"第 {loop_count} 轮监控完成，共处理 {total_processed} 个频道的消息")
            else:
                logger.debug(f"第 {loop_count} 轮监控完成，无新消息")

            time.sleep(5)

        except Exception as e:
            logger.error(f"主监控循环发生错误: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            time.sleep(10)
def cleanup_old_messages(days: int = 7) -> None:
    """
    清理指定天数前的消息记录

    Args:
        days: 保留天数，默认7天
    """
    logger.info(f"开始清理 {days} 天前的消息记录")

    try:
        conn = use_sql.sqlite3.connect(use_sql.DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM message_history 
            WHERE datetime(push_time) < datetime('now', ?)
        """, (f'-{days} days',))

        deleted_count = cursor.rowcount
        conn.commit()

        if deleted_count > 0:
            logger.info(f"消息记录清理完成，共删除 {deleted_count} 条记录")
        else:
            logger.debug("没有需要清理的过期消息记录")

    except use_sql.sqlite3.Error as e:
        logger.error(f"清理消息记录失败: {str(e)}")
    finally:
        if conn:
            conn.close()


def update_base_url(new_base_url: str) -> bool:
    """
    更新BASE_URL配置

    Args:
        new_base_url: 新的群晖服务器地址

    Returns:
        bool: 更新是否成功
    """
    try:
        # 验证URL格式
        if not new_base_url.startswith(('http://', 'https://')):
            new_base_url = f"https://{new_base_url}"

        # 测试连接
        test_url = f"{new_base_url.rstrip('/')}/webapi/query.cgi"
        params = {
            "api": "SYNO.API.Info",
            "version": "1",
            "method": "query",
            "query": "all"
        }

        resp = requests.get(test_url, params=params, verify=False, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            # 更新数据库配置
            success = use_sql.set_system_config("BASE_URL", new_base_url, "群晖DSM服务器地址")
            if success:
                logger.info(f"BASE_URL更新成功: {new_base_url}")
                return True
            else:
                logger.error("BASE_URL数据库更新失败")
                return False
        else:
            logger.error(f"BASE_URL测试连接失败: {resp.status_code}")
            return False

    except Exception as e:
        logger.error(f"BASE_URL更新失败: {str(e)}")
        return False


def get_channels_with_retry(sid: str, username: str, password: str) -> List[Dict[str, Any]]:
    """
    获取频道列表，如果SID失效则自动重新登录

    Args:
        sid: 当前会话ID
        username: 用户名
        password: 密码

    Returns:
        List[Dict]: 频道信息列表
    """
    try:
        return get_channels(sid)
    except Exception as e:
        error_msg = str(e)
        # 检查是否是SID过期错误（错误代码119）
        if 'code": 119' in error_msg or 'session timeout' in error_msg.lower():
            logger.warning(f"检测到SID过期，为用户 {username} 重新登录")
            try:
                # 重新登录获取新的SID
                new_sid = get_syno_sid(username, password)

                # 更新数据库中的SID
                use_sql.update_user_sid(username, new_sid)
                logger.info(f"用户 {username} 的SID已更新")

                # 使用新的SID重新获取频道列表
                return get_channels(new_sid)
            except Exception as login_error:
                logger.error(f"重新登录失败: {str(login_error)}")
                raise login_error
        else:
            # 其他错误，直接抛出
            raise e


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
        conn = use_sql.sqlite3.connect(use_sql.DB_FILE)
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

    except use_sql.sqlite3.Error as e:
        logger.error(f"更新用户SID失败: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_user_with_sid_refresh(user_info: tuple) -> tuple:
    """
    获取用户信息，如果SID失效则自动刷新

    Args:
        user_info: 用户信息元组

    Returns:
        tuple: 更新后的用户信息
    """
    username = user_info[2]
    password = user_info[3]  # 假设密码在第三个位置

    try:
        # 先尝试使用当前SID获取频道列表
        test_channels = get_channels(user_info[3])  # SID在第四个位置
        return user_info  # SID有效，直接返回

    except Exception as e:
        error_msg = str(e)
        # 检查是否是SID过期错误
        if 'code": 119' in error_msg or 'session timeout' in error_msg.lower():
            logger.warning(f"用户 {username} 的SID已过期，正在重新登录")
            try:
                # 重新登录获取新的SID
                new_sid = get_syno_sid(username, password)

                # 更新数据库中的SID
                use_sql.update_user_sid(username, new_sid)

                # 返回更新后的用户信息
                updated_user = list(user_info)
                updated_user[3] = new_sid  # 更新SID
                return tuple(updated_user)

            except Exception as login_error:
                logger.error(f"用户 {username} 重新登录失败: {str(login_error)}")
                raise login_error
        else:
            # 其他错误，直接抛出
            raise e


# 模块初始化
if __name__ == "__main__":
    # 配置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logger.info("syno_func 模块加载完成")
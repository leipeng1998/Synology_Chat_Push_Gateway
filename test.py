from typing import Dict, Any

import use_sql
from syno_func import logger, message_send


def process_single_message(channel_id: str, channel_name: str, message_data: Dict[str, Any], user_info: tuple) -> bool:
    """
    处理单条消息并推送

    Args:
        channel_id: 频道ID
        channel_name: 频道名称
        message_data: 消息数据
        user_info: 用户信息元组

    Returns:
        bool: 处理是否成功
    """
    try:
        message_id = message_data["message_id"]
        message_content = message_data["content"]
        creator_id = message_data["creator_id"]

        logger.info(f"开始处理消息: 频道={channel_name}, 消息ID={message_id}")

        # 匿名频道的特殊处理逻辑
        if channel_name == '':
            channel_info = use_sql.search_channel_by_id(channel_id)
            if channel_info:
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
                                title = other_user[2]  # 对方用户名
                                final_message = f'来自{title}的消息：{message_content}'

                                # 推送消息
                                if message_send(user_info[4], user_info[5], title, final_message):
                                    # 标记为已推送
                                    use_sql.mark_message_as_pushed(channel_id, message_id)
                                    logger.info(f"匿名频道消息推送成功: {message_id}")
                                    return True
                                else:
                                    logger.error(f"匿名频道消息推送失败: {message_id}")
                            else:
                                logger.warning(f"未找到对方用户信息: {other_members[0]}")
                        else:
                            logger.warning(f"频道 {channel_id} 没有其他成员")
                    else:
                        logger.warning(f"当前用户 {current_user_id} 不在频道成员中")
                else:
                    logger.warning(f"频道 {channel_id} 成员信息为空")
            else:
                logger.warning(f"未找到频道信息: {channel_id}")

        # 处理普通频道（包括频道5和其他所有频道）
        else:
            # 尝试获取发送者信息
            sender_info = use_sql.search_dsm_user_id_by_id(creator_id)
            if sender_info:
                sender_name = sender_info[2]  # 发送者用户名
                title = f"{channel_name} - {sender_name}"
            else:
                title = f"频道: {channel_name}"
                sender_name = f"用户{creator_id}"

            # 构建消息内容
            final_message = f'来自{channel_name}的消息({sender_name})：{message_content}'

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

# def process_single_message(channel_id: str, channel_name: str, message_data: Dict[str, Any],user_info: tuple) -> bool:
process_single_message('5','',{'message_id': '5_1761799578367', 'content': '[2025-10-30 12:46:18] 用户5: k', 'creator_id': 5, 'create_at': 1761799578367, 'is_new': True},(1, 0, 'lp1895', 'VZi_CDsfKx8IgE52reitWA66vvtVsgmtXuNr_bIp5JApB0S7fSFyT6h4mYP8d0jIDsbBbdiigA4nZ1aOU8uOLc', 'http://10.10.10.115:7152/message', 'APqnfgN2BOFBCyY'))
"""
聊天记忆管理服务
处理记忆的创建、查询、更新和删除操作
"""
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.messages import BaseMessage

from config.settings import config
from config.logger import server_logger


class RedisService:
    """Redis 服务类，封装 Redis 相关操作"""

    @staticmethod
    def get_chat_history(session_id: str) -> RedisChatMessageHistory:
        """获取聊天记录对象"""
        return RedisChatMessageHistory(
            session_id=session_id,
            **config.get_redis_config()
        )

    @staticmethod
    def clear_chat_history(session_id: str) -> bool:
        """清除指定会话的聊天记录"""
        try:
            chat_history = RedisService.get_chat_history(session_id)
            chat_history.clear()
            server_logger.info(f"已清除会话 {session_id} 的 Redis 聊天记录")
            return True
        except Exception as e:
            server_logger.error(f"清除会话 {session_id} 的聊天记录失败: {e}")
            return False

    @staticmethod
    def get_chat_messages(session_id: str) -> list:
        """获取指定会话的聊天记录"""
        try:
            chat_history = RedisService.get_chat_history(session_id)
            messages = chat_history.messages
            server_logger.debug(f"获取会话 {session_id} 的聊天记录: {len(messages)} 条")
            return messages
        except Exception as e:
            server_logger.error(f"获取会话 {session_id} 的聊天记录失败: {e}")
            return []

    @staticmethod
    def session_exists(session_id: str) -> bool:
        """检查会话是否存在"""
        try:
            messages = RedisService.get_chat_messages(session_id)
            return len(messages) > 0
        except Exception as e:
            server_logger.error(f"检查会话 {session_id} 存在性时出错: {e}")
            return False

    @staticmethod
    def add_message(session_id: str, message: BaseMessage) -> bool:
        """向指定会话添加消息"""
        try:
            chat_history = RedisService.get_chat_history(session_id)
            chat_history.add_message(message)
            server_logger.debug(f"向会话 {session_id} 添加消息: {type(message).__name__}")
            return True
        except Exception as e:
            server_logger.error(f"向会话 {session_id} 添加消息失败: {e}")
            return False

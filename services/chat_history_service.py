"""
Mystical Oracle Chat History Service - 聊天历史服务
提供聊天历史记录的存储和查询功能
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from models.database import ChatHistory, ChatSession
from config.logger import server_logger


class ChatHistoryService:
    """聊天历史服务类"""
    
    @staticmethod
    def add_chat_history(
        db: Session,
        user_id: int,
        session_id: str,
        user_message: str,
        assistant_message: str,
        mood: str = "default",
        message_type: str = "text",
        metadata: Dict[str, Any] = None
    ) -> ChatHistory:
        """添加聊天历史记录"""

        # 创建聊天历史记录
        chat_history = ChatHistory(
            user_id=user_id,
            session_id=session_id,
            user_message=user_message,
            assistant_message=assistant_message,
            mood=mood,
            message_type=message_type,
            metadata_data=metadata or {}
        )

        db.add(chat_history)
        db.commit()
        db.refresh(chat_history)

        server_logger.info(f"添加聊天历史成功: user_id={user_id}, session_id={session_id}")
        return chat_history
    
    @staticmethod
    def get_chat_history(
        db: Session,
        user_id: int,
        session_id: str = None,
        skip: int = 0,
        limit: int = 50
    ) -> list[type[ChatHistory]]:
        """获取特定会话的聊天历史"""
        query = db.query(ChatHistory).filter(ChatHistory.user_id == user_id)
        
        if session_id:
            query = query.filter(ChatHistory.session_id == session_id)
        
        return query.order_by(desc(ChatHistory.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_recent_chats(db: Session, user_id: int, days: int = 7) -> list[type[ChatHistory]]:
        """获取最近几天的聊天记录"""
        since_date = datetime.now(timezone.utc) - timedelta(days=days)
        return db.query(ChatHistory).filter(
            and_(ChatHistory.user_id == user_id, ChatHistory.created_at >= since_date)
        ).order_by(desc(ChatHistory.created_at)).all()
    
    @staticmethod
    def get_chat_stats(db: Session, user_id: int) -> Dict[str, Any]:
        """获取聊天统计信息"""
        # 总聊天次数
        total_chats = db.query(ChatHistory).filter(ChatHistory.user_id == user_id).count()
        
        # 总会话数
        total_sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).count()
        
        # 最近聊天时间
        recent_chat = db.query(ChatHistory).filter(
            ChatHistory.user_id == user_id
        ).order_by(desc(ChatHistory.created_at)).first()
        
        # 情绪分布
        mood_stats = {}
        mood_results = db.query(ChatHistory.mood, func.count(ChatHistory.id)).filter(
            ChatHistory.user_id == user_id
        ).group_by(ChatHistory.mood).all()

        for mood, count in mood_results:
            mood_stats[mood] = count
        
        return {
            "total_chats": total_chats,
            "total_sessions": total_sessions,
            "last_chat_time": recent_chat.created_at if recent_chat else None,
            "mood_distribution": mood_stats
        }
    
    @staticmethod
    def to_dict(chat_history: ChatHistory) -> Dict[str, Any]:
        """将聊天历史记录转换为字典"""
        return {
            "id": chat_history.id,
            "session_id": chat_history.session_id,
            "user_message": chat_history.user_message,
            "assistant_message": chat_history.assistant_message,
            "mood": chat_history.mood,
            "message_type": chat_history.message_type,
            "metadata": chat_history.metadata_data,
            "created_at": chat_history.created_at.isoformat()
        }
    

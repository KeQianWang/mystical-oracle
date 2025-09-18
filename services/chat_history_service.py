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
    def create_chat_session(db: Session, user_id: int, session_id: str, title: str = None) -> type[ChatSession] | ChatSession:
        """创建聊天会话"""

        # 创建新会话
        chat_session = ChatSession(
            user_id=user_id,
            session_id=session_id,
            title=title or f"会话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)
        
        server_logger.info(f"创建聊天会话成功: user_id={user_id}, session_id={session_id}")
        return chat_session
    
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

        # 确保会话存在
        ChatHistoryService.create_chat_session(db, user_id, session_id)

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
        """获取聊天历史记录"""
        query = db.query(ChatHistory).filter(ChatHistory.user_id == user_id)
        
        if session_id:
            query = query.filter(ChatHistory.session_id == session_id)
        
        return query.order_by(desc(ChatHistory.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_chat_sessions(db: Session, user_id: int) -> list[type[ChatSession]]:
        """获取用户的所有聊天会话"""
        return db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(desc(ChatSession.updated_at)).all()
    
    @staticmethod
    def get_session_history(db: Session, user_id: int, session_id: str) -> list[type[ChatHistory]]:
        """获取特定会话的聊天历史"""
        return db.query(ChatHistory).filter(
            and_(ChatHistory.user_id == user_id, ChatHistory.session_id == session_id)
        ).order_by(ChatHistory.created_at).all()
    
    @staticmethod
    def update_session_title(db: Session, user_id: int, session_id: str, title: str) -> Optional[ChatSession]:
        """更新会话标题"""
        session = db.query(ChatSession).filter(
            and_(ChatSession.user_id == user_id, ChatSession.session_id == session_id)
        ).first()
        
        if not session:
            return None
        
        session.title = title
        session.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(session)
        
        server_logger.info(f"更新会话标题成功: user_id={user_id}, session_id={session_id}, title={title}")
        return session
    
    @staticmethod
    def delete_session(db: Session, user_id: int, session_id: str) -> bool:
        """删除会话及其历史记录"""
        # 删除聊天历史
        db.query(ChatHistory).filter(
            and_(ChatHistory.user_id == user_id, ChatHistory.session_id == session_id)
        ).delete()
        
        # 删除会话
        result = db.query(ChatSession).filter(
            and_(ChatSession.user_id == user_id, ChatSession.session_id == session_id)
        ).delete()
        
        db.commit()
        
        if result > 0:
            server_logger.info(f"删除会话成功: user_id={user_id}, session_id={session_id}")
            return True
        return False
    
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
    
    @staticmethod
    def session_to_dict(session: ChatSession) -> Dict[str, Any]:
        """将会话记录转换为字典"""
        return {
            "id": session.id,
            "session_id": session.session_id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        }
"""
聊天会话管理服务
处理会话的创建、查询、更新和删除操作
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from models.database import ChatSession
from models.user import ChatSessionCreate, ChatSessionUpdate
from config.logger import server_logger


class SessionService:
    """聊天会话服务类"""
    
    @staticmethod
    def create_session(db: Session, user_id: int, session_data: ChatSessionCreate) -> ChatSession:
        """创建新的聊天会话"""
        import uuid
        
        session_id = str(uuid.uuid4())
        db_session = ChatSession(
            user_id=user_id,
            session_id=session_id,
            title=session_data.title,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        
        server_logger.info(f"创建新会话: user_id={user_id}, session_id={session_id}")
        return db_session
    
    @staticmethod
    def get_user_sessions(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[ChatSession]:
        """获取用户的所有会话"""
        sessions = db.query(ChatSession).filter(
            and_(
                ChatSession.user_id == user_id,
                ChatSession.is_active == True
            )
        ).order_by(desc(ChatSession.updated_at)).offset(skip).limit(limit).all()
        
        return sessions
    
    @staticmethod
    def get_session_by_id(db: Session, session_id: str, user_id: int) -> Optional[ChatSession]:
        """根据session_id获取会话"""
        return db.query(ChatSession).filter(
            and_(
                ChatSession.session_id == session_id,
                ChatSession.user_id == user_id,
                ChatSession.is_active == True
            )
        ).first()
    
    @staticmethod
    def update_session(db: Session, session_id: str, user_id: int, update_data: ChatSessionUpdate) -> Optional[ChatSession]:
        """更新会话信息"""
        session = SessionService.get_session_by_id(db, session_id, user_id)
        if not session:
            return None
        
        # 更新字段
        if update_data.title is not None:
            session.title = update_data.title
        if update_data.is_active is not None:
            session.is_active = update_data.is_active
        
        session.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(session)
        
        server_logger.info(f"更新会话: session_id={session_id}, user_id={user_id}")
        return session
    
    @staticmethod
    def delete_session(db: Session, session_id: str, user_id: int) -> bool:
        """删除会话（软删除）"""
        session = SessionService.get_session_by_id(db, session_id, user_id)
        if not session:
            return False
        
        session.is_active = False
        session.updated_at = datetime.utcnow()
        
        db.commit()
        
        server_logger.info(f"删除会话: session_id={session_id}, user_id={user_id}")
        return True
    
    @staticmethod
    def get_session_with_message_count(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[dict]:
        """获取会话列表及消息数量"""
        # 查询会话及对应的聊天记录数量
        from services.chat_history_service import ChatHistory
        
        sessions = db.query(
            ChatSession,
            func.count(ChatHistory.id).label('message_count')
        ).outerjoin(
            ChatHistory,
            and_(
                ChatHistory.session_id == ChatSession.session_id,
                ChatHistory.user_id == ChatSession.user_id
            )
        ).filter(
            and_(
                ChatSession.user_id == user_id,
                ChatSession.is_active == True
            )
        ).group_by(ChatSession.id).order_by(desc(ChatSession.updated_at)).offset(skip).limit(limit).all()
        
        result = []
        for session, message_count in sessions:
            result.append({
                'id': session.id,
                'session_id': session.session_id,
                'title': session.title,
                'created_at': session.created_at,
                'updated_at': session.updated_at,
                'is_active': session.is_active,
                'message_count': message_count or 0
            })
        
        return result
    
    @staticmethod
    def ensure_default_session(db: Session, user_id: int) -> ChatSession:
        """确保用户有默认会话，如果没有则创建"""
        # 查找用户的活跃会话
        active_sessions = SessionService.get_user_sessions(db, user_id, limit=1)
        
        if active_sessions:
            return active_sessions[0]
        
        # 创建默认会话
        default_session = ChatSessionCreate(title="新对话")
        return SessionService.create_session(db, user_id, default_session)
    
    @staticmethod
    def update_session_activity(db: Session, session_id: str, user_id: int) -> None:
        """更新会话活跃时间"""
        session = SessionService.get_session_by_id(db, session_id, user_id)
        if session:
            session.updated_at = datetime.now(timezone.utc)
            db.commit()
"""
聊天会话管理路由器
处理会话的创建、查询、更新和删除操作
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from services.auth import get_current_active_user
from database.connection import get_db
from models.user import (
    ChatSessionCreate, 
    ChatSessionUpdate, 
    ChatSessionResponse,
    UserResponse
)
from models.database import ChatSession
from services.session_service import SessionService
from services.chat_history_service import ChatHistory
from config.logger import server_logger

router = APIRouter(tags=["会话管理"])


@router.post("/sessions", response_model=ChatSessionResponse)
def create_session(
    session_data: ChatSessionCreate,
    current_user: UserResponse = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建新的聊天会话"""
    try:
        session = SessionService.create_session(db, current_user.id, session_data)
        return ChatSessionResponse(
            id=session.id,
            session_id=session.session_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            is_active=session.is_active,
            message_count=0
        )
    except Exception as e:
        server_logger.error(f"创建会话失败: {e}")
        raise HTTPException(status_code=500, detail="创建会话失败")


@router.get("/sessions", response_model=List[ChatSessionResponse])
def get_user_sessions(
    skip: int = 0,
    limit: int = 50,
    current_user: UserResponse = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户的所有会话列表"""
    try:
        sessions_data = SessionService.get_session_with_message_count(db, current_user.id, skip, limit)
        
        return [
            ChatSessionResponse(
                id=data['id'],
                session_id=data['session_id'],
                title=data['title'],
                created_at=data['created_at'],
                updated_at=data['updated_at'],
                is_active=data['is_active'],
                message_count=data['message_count']
            ) for data in sessions_data
        ]
    except Exception as e:
        server_logger.error(f"获取会话列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取会话列表失败")


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
def get_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取特定会话信息"""
    try:
        session = SessionService.get_session_by_id(db, session_id, current_user.id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 获取消息数量
        message_count = db.query(ChatHistory).filter(
            ChatHistory.session_id == session_id,
            ChatHistory.user_id == current_user.id
        ).count()
        
        return ChatSessionResponse(
            id=session.id,
            session_id=session.session_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            is_active=session.is_active,
            message_count=message_count
        )
    except HTTPException:
        raise
    except Exception as e:
        server_logger.error(f"获取会话信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取会话信息失败")


@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
def update_session(
    session_id: str,
    session_data: ChatSessionUpdate,
    current_user: UserResponse = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新会话信息"""
    try:
        session = SessionService.update_session(db, session_id, current_user.id, session_data)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 获取消息数量
        message_count = db.query(ChatHistory).filter(
            ChatHistory.session_id == session_id,
            ChatHistory.user_id == current_user.id
        ).count()
        
        return ChatSessionResponse(
            id=session.id,
            session_id=session.session_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            is_active=session.is_active,
            message_count=message_count
        )
    except HTTPException:
        raise
    except Exception as e:
        server_logger.error(f"更新会话失败: {e}")
        raise HTTPException(status_code=500, detail="更新会话失败")


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除会话"""
    try:
        success = SessionService.delete_session(db, session_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {"message": "会话已删除"}
    except HTTPException:
        raise
    except Exception as e:
        server_logger.error(f"删除会话失败: {e}")
        raise HTTPException(status_code=500, detail="删除会话失败")


@router.get("/sessions/default")
def get_default_session(
    current_user: UserResponse = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取或创建用户的默认会话"""
    try:
        session = SessionService.ensure_default_session(db, current_user.id)
        
        # 获取消息数量
        message_count = db.query(ChatHistory).filter(
            ChatHistory.session_id == session.session_id,
            ChatHistory.user_id == current_user.id
        ).count()
        
        return ChatSessionResponse(
            id=session.id,
            session_id=session.session_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            is_active=session.is_active,
            message_count=message_count
        )
    except Exception as e:
        server_logger.error(f"获取默认会话失败: {e}")
        raise HTTPException(status_code=500, detail="获取默认会话失败")
"""
聊天历史记录接口路由器
包含会话管理和历史记录相关接口
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from services.chat_history_service import ChatHistoryService
from services.auth import get_current_active_user
from utils.helpers import format_error_message
from config.logger import server_logger
from database.connection import get_db

router = APIRouter(prefix="/chat", tags=["聊天历史"])


@router.get("/sessions")
def get_chat_sessions(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户的聊天会话列表"""
    try:
        sessions = ChatHistoryService.get_chat_sessions(db, current_user.id)
        return {
            "sessions": [ChatHistoryService.session_to_dict(session) for session in sessions]
        }
    except Exception as e:
        error_msg = format_error_message(e, "获取聊天会话列表")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="获取会话列表失败")


@router.get("/history")
def get_chat_history(
    session_id: str = None,
    skip: int = 0,
    limit: int = 50,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取聊天历史记录"""
    try:
        history = ChatHistoryService.get_chat_history(
            db, current_user.id, session_id, skip, limit
        )
        return {
            "history": [ChatHistoryService.to_dict(record) for record in history]
        }
    except Exception as e:
        error_msg = format_error_message(e, "获取聊天历史")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="获取聊天历史失败")


@router.get("/session/{session_id}/history")
def get_session_history(
    session_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取特定会话的聊天历史"""
    try:
        history = ChatHistoryService.get_session_history(db, current_user.id, session_id)
        return {
            "session_id": session_id,
            "history": [ChatHistoryService.to_dict(record) for record in history]
        }
    except Exception as e:
        error_msg = format_error_message(e, f"获取会话 {session_id} 的聊天历史")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="获取会话聊天历史失败")


@router.put("/session/{session_id}/title")
def update_session_title(
    session_id: str,
    title: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新会话标题"""
    try:
        session = ChatHistoryService.update_session_title(
            db, current_user.id, session_id, title
        )
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {
            "message": "会话标题更新成功",
            "session": ChatHistoryService.session_to_dict(session)
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = format_error_message(e, f"更新会话 {session_id} 标题")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="更新会话标题失败")


@router.delete("/session/{session_id}")
def delete_session(
    session_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除聊天会话"""
    try:
        success = ChatHistoryService.delete_session(db, current_user.id, session_id)
        if not success:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {"message": "会话删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        error_msg = format_error_message(e, f"删除会话 {session_id}")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="删除会话失败")


@router.get("/stats")
def get_chat_stats(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取聊天统计信息"""
    try:
        stats = ChatHistoryService.get_chat_stats(db, current_user.id)
        return stats
    except Exception as e:
        error_msg = format_error_message(e, "获取聊天统计")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="获取聊天统计失败")


@router.get("/recent")
def get_recent_chats(
    days: int = 7,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取最近几天的聊天记录"""
    try:
        if days < 1 or days > 30:
            raise HTTPException(status_code=400, detail="天数必须在1-30之间")
        
        recent_chats = ChatHistoryService.get_recent_chats(db, current_user.id, days)
        return {
            "days": days,
            "chats": [ChatHistoryService.to_dict(record) for record in recent_chats]
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = format_error_message(e, f"获取最近 {days} 天的聊天记录")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="获取最近聊天记录失败")
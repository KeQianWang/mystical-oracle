"""
聊天历史记录接口路由器
包含历史记录查询和统计相关接口
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from services.chat_history_service import ChatHistoryService
from services.auth import get_current_active_user
from utils.helpers import format_error_message
from config.logger import server_logger
from database.connection import get_db

router = APIRouter(prefix="/chat", tags=["聊天历史"])


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
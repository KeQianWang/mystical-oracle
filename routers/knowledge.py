"""
知识库管理接口路由器
包含添加网页、PDF、文本内容到知识库的接口
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from database.connection import get_db
from models.user import UserResponse
from services.knowled_service import KnowledgeService
from services.session_service import SessionService
from utils.helpers import format_error_message
from config.logger import server_logger
from services.auth import get_current_active_user

router = APIRouter(tags=["知识库管理"])


@router.post("/add_knowledge")
async def add_knowledge(
    url: str = Form(None),
    file: UploadFile = File(None),
    current_user: UserResponse = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """通用接口：添加 URL 或文件 到用户专属知识库（单 Collection）"""
    try:
        # 获取或创建用户的默认会话
        default_session = SessionService.ensure_default_session(db, current_user.id)
        session_id = default_session.session_id

        if url:
            return KnowledgeService.process_url(url, session_id)
        elif file:
            return KnowledgeService.process_file(file, session_id)
        else:
            raise HTTPException(status_code=400, detail="必须提供 URL 或文件")
    except Exception as e:
        error_msg = format_error_message(e, "添加知识库内容")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="添加知识库失败，请稍后再试")
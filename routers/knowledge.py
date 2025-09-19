"""
知识库管理接口路由器
包含添加网页、PDF、文本内容到知识库的接口
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from database.connection import get_db
from models.user import UserResponse
from services.knowledge_service import knowledge_service
from services.session_service import SessionService
from utils.helpers import format_error_message
from config.logger import server_logger
from services.auth import get_current_active_user

router = APIRouter(tags=["知识库管理"])


@router.post("/add_knowledge")
async def add_knowledge(
    url: str = Form(None),
    file: UploadFile = File(None),
    session_id: str = Form(None),
):
    """通用接口：添加 URL 或文件 到用户专属知识库（单 Collection）"""
    try:
        if url:
            return knowledge_service.process_url(url, session_id)
        elif file:
            return knowledge_service.process_file(file, session_id)
        else:
            raise HTTPException(status_code=400, detail="必须提供 URL 或文件")
    except Exception as e:
        error_msg = format_error_message(e, "添加知识库内容")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="添加知识库失败，请稍后再试")
"""
聊天接口路由器
包含主要的对话功能接口
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from agent import Master
from models.user import ChatRequest, UserResponse
from utils.helpers import validate_user_input, format_error_message
from config.logger import server_logger
from services.auth import get_current_active_user
from database.connection import get_db
from services.session_service import SessionService

router = APIRouter(tags=["聊天接口"])


@router.post("/chat")
def chat(
    chat_request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """与算命师对话，支持语音合成"""
    try:
        # 验证输入
        if not validate_user_input(chat_request.query):
            raise HTTPException(status_code=400, detail="输入内容无效")
        
        # 获取或创建用户的默认会话
        default_session = SessionService.ensure_default_session(db, current_user.id)
        session_id = default_session.session_id
        
        # 更新会话活跃时间
        SessionService.update_session_activity(db, session_id, current_user.id)
        
        # 创建算命师实例并处理对话
        master = Master(session_id=session_id)
        result = master.run(chat_request.query, user_id=current_user.id)
        
        # 生成唯一 ID 用于音频文件
        unique_id = str(uuid.uuid4())
        
        # 后台任务：语音合成
        if result.get("output") and chat_request.enable_tts:
            background_tasks.add_task(
                master.synthesize_speech_background,
                result["output"],
                unique_id
            )
        
        return {
            "msg": result.get("output", "无法获取回复"),
            "id": unique_id,
            "session_id": session_id,
            "mood": master.get_current_mood(),
            "voice_style": master.get_voice_style()
        }
        
    except Exception as e:
        error_msg = format_error_message(e, "对话处理")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="服务暂时不可用，请稍后再试")
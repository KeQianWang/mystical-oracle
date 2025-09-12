"""
聊天接口路由器
包含主要的对话功能接口
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from agent import Master
from utils.helpers import validate_user_input, format_error_message
from config.logger import server_logger
from services.auth import get_current_active_user
from database.connection import get_db

router = APIRouter(tags=["聊天接口"])


@router.post("/chat")
def chat(
    query: str, 
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """与算命师对话，支持语音合成"""
    try:
        # 验证输入
        if not validate_user_input(query):
            raise HTTPException(status_code=400, detail="输入内容无效")
        
        # 创建算命师实例并处理对话（使用用户ID作为会话ID）
        master = Master(session_id=f"user_{current_user.id}")
        result = master.run(query, user_id=current_user.id)
        
        # 生成唯一 ID 用于音频文件
        unique_id = str(uuid.uuid4())
        
        # 后台任务：语音合成
        if result.get("output"):
            background_tasks.add_task(
                master.synthesize_speech_background,
                result["output"],
                unique_id
            )
        
        return {
            "msg": result.get("output", "无法获取回复"),
            "id": unique_id,
            "mood": master.get_current_mood(),
            "voice_style": master.get_voice_style()
        }
        
    except Exception as e:
        error_msg = format_error_message(e, "对话处理")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="服务暂时不可用，请稍后再试")
"""
聊天接口路由器
包含主要的对话功能接口
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from models.user import ChatRequest, UserResponse
from services.chat_service import ChatService
from utils.helpers import  format_error_message
from config.logger import server_logger
from services.auth import get_current_active_user
from database.connection import get_db

router = APIRouter(tags=["聊天接口"])



@router.post("/chat")
def chat(
    chat_request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """与算命师对话，支持语音合成"""
    try:
        context, master = ChatService.prepare_chat_context(chat_request, db, current_user)

        # 执行对话
        result = master.run(chat_request.query)

        # 后台执行 TTS
        if result.get("output") and chat_request.enable_tts:
            background_tasks.add_task(
                master.synthesize_speech_background,
                result["output"],
                context.session_id,
            )

        return {
            "msg": result.get("output", "无法获取回复"),
            "session_id": context.session_id,
            "mood": context.mood,
            "voice_style": context.voice_style,
        }

    except Exception as e:
        error_msg = format_error_message(e, "对话处理")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="服务暂时不可用，请稍后再试")


@router.post("/chat/stream")
async def chat_stream(
    chat_request: ChatRequest,
    current_user: UserResponse = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """与算命师流式对话 (支持同步/异步两种模式)"""
    try:
        context, master = ChatService.prepare_chat_context(chat_request, db, current_user)

        if chat_request.async_mode:
            # 异步流
            result_generator = master.run_stream_async(chat_request.query)
            stream_gen = ChatService.async_stream_response(
                result_generator,
                db,
                context
            )
        else:
            # 同步流
            result_generator = master.run_stream(chat_request.query)
            stream_gen = ChatService.stream_response(
                result_generator,
                db,
                context
            )

        return StreamingResponse(stream_gen, media_type="text/event-stream", headers=ChatService.sse_headers())

    except Exception as e:
        error_msg = format_error_message(e, "流式对话处理")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="服务暂时不可用，请稍后再试")

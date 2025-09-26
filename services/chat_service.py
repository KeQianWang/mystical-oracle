"""
Mystical Oracle Chat Service - 聊天服务
提供聊天功能
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from agent import Master
from models.user import ChatRequest, UserResponse, ChatSessionCreate
from services.session_service import SessionService
from utils.helpers import validate_user_input


class ChatService:
    """聊天服务类"""

    @staticmethod
    def stream_response_generator(result_generator, unique_id, session_id, mood, voice_style):
        """流式响应生成器 - 字符级SSE输出"""
        full_response = ""

        for chunk in result_generator:
            if chunk:  # 确保chunk不为空
                full_response += chunk
                # 为每个字符创建SSE事件
                for char in chunk:
                    data = {
                        "type": "content",
                        "content": char,
                        "id": unique_id,
                        "session_id": session_id,
                        "mood": mood,
                        "voice_style": voice_style
                    }
                    yield f"data: {data}\n\n"

        # 发送完成信号
        final_data = {
            "type": "complete",
            "content": full_response,
            "id": unique_id,
            "session_id": session_id,
            "mood": mood,
            "voice_style": voice_style
        }
        yield f"data: {final_data}\n\n"

    @staticmethod
    async def async_stream_response_generator(result_generator, unique_id, session_id, mood, voice_style):
        """异步流式响应生成器 - 字符级SSE输出"""
        full_response = ""

        async for chunk in result_generator:
            if chunk:  # 确保chunk不为空
                full_response += chunk
                # 为每个字符创建SSE事件
                for char in chunk:
                    data = {
                        "type": "content",
                        "content": char,
                        "id": unique_id,
                        "session_id": session_id,
                        "mood": mood,
                        "voice_style": voice_style
                    }
                    yield f"data: {data}\n\n"

        # 发送完成信号
        final_data = {
            "type": "complete",
            "content": full_response,
            "id": unique_id,
            "session_id": session_id,
            "mood": mood,
            "voice_style": voice_style
        }
        yield f"data: {final_data}\n\n"

    # ==================== 工具函数 ====================
    @staticmethod
    def prepare_chat_context(chat_request: ChatRequest, db: Session, current_user: UserResponse) -> tuple[str, Master]:
        """
        公共的对话上下文准备逻辑：
        - 校验输入
        - 确保 session 存在
        - 更新 session 活跃时间
        - 初始化 Master
        """
        if not validate_user_input(chat_request.query):
            raise HTTPException(status_code=400, detail="输入内容无效")

        if not chat_request.session_id:
            session = SessionService.create_session(
                db, current_user.id, ChatSessionCreate(title="默认会话")
            )
            chat_request.session_id = session.session_id

        session_id = chat_request.session_id
        SessionService.update_session_activity(db, session_id, current_user.id)

        master = Master(session_id=session_id, user_id=current_user.id)
        return session_id, master

    @staticmethod
    def sse_headers() -> dict[str, str]:
        """SSE 默认响应头"""
        return {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
"""
Mystical Oracle Chat Service - 聊天服务
提供聊天功能
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from agent import Master
from models.user import ChatRequest, UserResponse, ChatSessionCreate
from services.chat_history_service import ChatHistoryService
from services.session_service import SessionService
from utils.helpers import validate_user_input
from config.logger import server_logger
from prompts.mood_prompts import MoodPrompts


class ChatContext:
    """封装聊天上下文信息，避免参数过多"""
    def __init__(self, user_id, session_id, query, master=None):
        self.user_id = user_id
        self.session_id = session_id
        self.query = query
        self._master = master

    @property
    def mood(self):
        """动态获取当前mood，确保返回的是分析后的最终mood"""
        return self._master.get_current_mood() if self._master else MoodPrompts.get_default_mood()

    @property
    def voice_style(self):
        """动态获取当前voice_style，确保返回的是分析后最终的voice_style"""
        return self._master.get_voice_style() if self._master else "chat"

class ChatService:
    """聊天服务类"""

    # ======== 核心流式处理逻辑 ========

    @staticmethod
    def _format_sse_event(event_type: str, content: str, context: ChatContext) -> str:
        """格式化SSE事件"""
        data = {
            "type": event_type,
            "content": content,
            "session_id": context.session_id,
            "mood": context.mood,
            "voice_style": context.voice_style,
        }
        return f"data: {data}\n\n"

    @staticmethod
    def _save_history(db: Session, context: ChatContext, assistant_response: str):
        """保存聊天记录"""
        ChatHistoryService.add_chat_history(
            db=db,
            user_id=context.user_id,
            session_id=context.session_id,
            user_message=context.query,
            assistant_message=assistant_response,
            mood=context.mood,
            message_type="text",
        )
        server_logger.debug(f"聊天历史已保存: user_id={context.user_id}, session_id={context.session_id}")

    # ======== 同步 / 异步流式生成 ========

    @classmethod
    def stream_response(cls, result_generator, db: Session, context: ChatContext, master=None, enable_tts: bool = False):
        """同步流式SSE生成器"""
        import asyncio
        full_response = ""
        for chunk in result_generator:
            if not chunk:
                continue
            full_response += chunk
            for char in chunk:
                yield cls._format_sse_event("content", char, context)

        cls._save_history(db, context, full_response)
        yield cls._format_sse_event("complete", full_response, context)

        if full_response and enable_tts and master:
            loop = asyncio.get_event_loop()
            loop.create_task(master.synthesize_speech_background(full_response, context.session_id))

    @classmethod
    async def async_stream_response(cls, result_generator, db: Session, context: ChatContext, master=None, enable_tts: bool = False):
        """异步流式SSE生成器"""
        full_response = ""
        async for chunk in result_generator:
            if not chunk:
                continue
            full_response += chunk
            for char in chunk:
                yield cls._format_sse_event("content", char, context)

        cls._save_history(db, context, full_response)
        yield cls._format_sse_event("complete", full_response, context)

        if full_response and enable_tts and master:
            await master.synthesize_speech_background(full_response, context.session_id)

    # ======== 公共上下文准备 ========

    @staticmethod
    def prepare_chat_context(chat_request: ChatRequest, db: Session, current_user: UserResponse) -> tuple[ChatContext, Master]:
        """
        准备对话上下文：
        - 校验输入
        - 确保 session 存在
        - 更新活跃时间
        - 初始化 Master 实例
        """
        if not validate_user_input(chat_request.query):
            raise HTTPException(status_code=400, detail="输入内容无效")

        # 保证 session 存在
        if not chat_request.session_id:
            session = SessionService.create_session(
                db, current_user.id, ChatSessionCreate(title="默认会话")
            )
            chat_request.session_id = session.session_id

        SessionService.update_session_activity(db, chat_request.session_id, current_user.id)
        master = Master(session_id=chat_request.session_id, user_id=current_user.id)

        # 创建上下文对象
        context = ChatContext(
            user_id=current_user.id,
            session_id=chat_request.session_id,
            query=chat_request.query,
            master=master
        )

        return context, master

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

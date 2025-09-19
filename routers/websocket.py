"""
WebSocket接口路由器
包含实时对话WebSocket接口
"""
import uuid
import asyncio
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session

from agent import Master
from models.user import  ChatSessionCreate
from utils.helpers import validate_user_input, format_error_message
from config.logger import server_logger
from services.auth import get_current_active_user_websocket
from database.connection import get_db
from services.session_service import SessionService
from models.database import User

router = APIRouter(tags=["WebSocket接口"])


async def process_websocket_message(
    data: dict,
    current_user: User,
    db: Session,
) -> dict:
    """处理WebSocket消息的核心逻辑，与chat.py保持一致"""
    try:
        query = data.get("query", "")
        enable_tts = data.get("enable_tts", False)
        session_id = data.get("session_id")

        # 验证输入
        if not validate_user_input(query):
            raise HTTPException(status_code=400, detail="输入内容无效")

        # 如果没有session_id，创建新的会话
        if not session_id:
            session = SessionService.create_session(db, current_user.id, ChatSessionCreate(title="WebSocket会话"))
            session_id = session.session_id

        # 更新会话活跃时间
        SessionService.update_session_activity(db, session_id, current_user.id)

        # 创建算命师实例并处理对话
        master = Master(session_id=session_id, user_id=current_user.id)
        result = master.run(query)

        # 生成唯一 ID 用于音频文件
        unique_id = str(uuid.uuid4())

        # 后台任务：语音合成（WebSocket中异步处理）
        if result.get("output") and enable_tts:
            asyncio.create_task(
                master.synthesize_speech_background(
                    result["output"],
                    unique_id
                )
            )

        return {
            "msg": result.get("output", "无法获取回复"),
            "id": unique_id,
            "session_id": session_id,
            "mood": master.get_current_mood(),
            "voice_style": master.get_voice_style()
        }

    except Exception as e:
        error_msg = format_error_message(e, "WebSocket对话处理")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="服务暂时不可用，请稍后再试")


@router.websocket('/ws')
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """WebSocket 端点 - 实时对话，与chat.py逻辑保持一致"""
    try:
        await websocket.accept()

        # WebSocket用户认证
        if not token:
            # 等待客户端发送认证信息
            auth_data = await websocket.receive_json()
            token = auth_data.get("token")

        if not token:
            await websocket.send_json({
                "msg": "需要认证令牌",
                "type": "error"
            })
            await websocket.close()
            return

        # 获取当前用户
        try:
            current_user = await get_current_active_user_websocket(token, db)
        except Exception as e:
            await websocket.send_json({
                "msg": "认证失败",
                "type": "error"
            })
            await websocket.close()
            return

        while True:
            # 接收消息
            data = await websocket.receive_json()

            try:
                # 使用与chat.py相同的核心处理逻辑
                response_data = await process_websocket_message(
                    data, current_user, db, websocket
                )

                # 发送回复
                await websocket.send_json(response_data)

            except HTTPException as he:
                await websocket.send_json({
                    "msg": he.detail,
                    "type": "error"
                })
            except Exception as e:
                error_msg = format_error_message(e, "WebSocket 对话处理")
                server_logger.error(error_msg)
                await websocket.send_json({
                    "msg": "服务暂时不可用，请稍后再试",
                    "type": "error"
                })

    except WebSocketDisconnect:
        server_logger.info("WebSocket 客户端断开连接")
    except Exception as e:
        server_logger.error(f"WebSocket 连接错误: {e}")
        try:
            await websocket.close()
        except:
            pass

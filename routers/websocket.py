"""
WebSocket接口路由器
包含实时对话WebSocket接口
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from agent import Master
from utils.helpers import validate_user_input, format_error_message
from config.logger import server_logger

router = APIRouter(tags=["WebSocket接口"])


@router.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点 - 实时对话"""
    await websocket.accept()
    master = Master()
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            
            # 验证输入
            if not validate_user_input(data):
                await websocket.send_text("输入内容无效，请重新输入")
                continue
            
            try:
                # 处理对话
                result = master.run(data)
                response = result.get("output", "无法获取回复")
                
                # 发送回复
                await websocket.send_text(response)
                
            except Exception as e:
                error_msg = format_error_message(e, "WebSocket 对话处理")
                server_logger.error(error_msg)
                await websocket.send_text("处理消息时出现错误，请稍后再试")
                
    except WebSocketDisconnect:
        server_logger.info("WebSocket 客户端断开连接")
    except Exception as e:
        server_logger.error(f"WebSocket 连接错误: {e}")
        await websocket.close()
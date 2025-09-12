"""
Mystical Oracle Server - 神秘预言师 Web 服务器
使用配置管理和更好的错误处理，集成语音合成功能
采用模块化路由器架构
"""
import sys
import os
from pathlib import Path

# 设置必要的环境变量
os.environ.setdefault("USER_AGENT", "Mozilla/5.0 (Mystical Oracle/1.0)")

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from database.connection import create_tables
from config.logger import server_logger

# 导入路由器
from routers import (
    system,
    auth,
    chat,
    chat_history,
    knowledge,
    audio,
    websocket
)

# 创建数据库表
create_tables()

# 创建 FastAPI 应用
app = FastAPI(
    title="Mystical Oracle API",
    description="神秘预言师 - 基于 LangChain 的智能算命师聊天机器人，支持语音合成",
    version="1.0.0"
)

# 注册所有路由器
app.include_router(system.router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(chat_history.router)
app.include_router(knowledge.router)
app.include_router(audio.router)
app.include_router(websocket.router)


if __name__ == '__main__':
    import uvicorn
    
    server_logger.info("🔮 算命师机器人服务启动中...")
    server_logger.info(f"📍 服务地址: http://localhost:8001")
    server_logger.info(f"🌐 API 文档: http://localhost:8001/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
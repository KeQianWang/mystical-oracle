"""
Mystical Oracle Server - 神秘预言师 Web 服务器
使用配置管理和更好的错误处理，集成语音合成功能
"""
import sys
import os
import uuid
from pathlib import Path

from starlette import status

# 设置必要的环境变量
os.environ.setdefault("USER_AGENT", "Mozilla/5.0 (Mystical Oracle/1.0)")

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, Depends
from fastapi.security import HTTPBearer
from fastapi.responses import FileResponse
from langchain_community.document_loaders import WebBaseLoader
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import Qdrant
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session

from agent import Master
from config.settings import config
from utils.helpers import validate_user_input, format_error_message
from config.logger import server_logger
from database.connection import get_db, create_tables
from models.user import UserCreate, UserLogin, UserResponse, UserUpdate, Token
from services.auth import (
    authenticate_user, 
    create_user_token, 
    get_current_active_user,
    update_last_login
)
from services.user_service import UserService
from services.chat_history_service import ChatHistoryService

# 创建数据库表
create_tables()

# 创建 FastAPI 应用
app = FastAPI(
    title="Mystical Oracle API",
    description="神秘预言师 - 基于 LangChain 的智能算命师聊天机器人，支持语音合成",
    version="1.0.0"
)

# JWT认证
security = HTTPBearer()


@app.get("/")
def get_root():
    """根路径"""
    return {"response": "神秘预言师服务正在运行", "service": "Mystical Oracle"}


# 用户认证接口
@app.post("/auth/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    try:
        user = UserService.create_user(db, user_data)
        return UserService.to_response(user)
    except HTTPException:
        raise
    except Exception as e:
        error_msg = format_error_message(e, "用户注册")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="注册失败，请稍后再试")


@app.post("/auth/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    try:
        # 验证用户
        user = authenticate_user(db, user_data.username, user_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 更新最后登录时间
        update_last_login(db, user)
        
        # 创建访问令牌
        return create_user_token(user)
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = format_error_message(e, "用户登录")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="登录失败，请稍后再试")


@app.get("/auth/me", response_model=UserResponse)
def get_current_user_info(current_user = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return UserService.to_response(current_user)


@app.put("/auth/me", response_model=UserResponse)
def update_current_user(
    user_data: UserUpdate, 
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新当前用户信息"""
    try:
        updated_user = UserService.update_user(db, current_user.id, user_data)
        return UserService.to_response(updated_user)
    except HTTPException:
        raise
    except Exception as e:
        error_msg = format_error_message(e, "更新用户信息")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="更新失败，请稍后再试")


@app.post("/chat")
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


@app.get("/audio/{audio_id}")
def get_audio(audio_id: str):
    """获取生成的音频文件"""
    try:
        audio_path = Path(f"{audio_id}.mp3")

        if not audio_path.exists():
            raise HTTPException(status_code=404, detail="音频文件不存在")
        
        return FileResponse(
            path=audio_path,
            media_type="audio/mpeg",
            filename=f"{audio_id}.mp3"
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="音频文件不存在")
    except Exception as e:
        error_msg = format_error_message(e, f"获取音频文件: {audio_id}")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="获取音频文件失败")


@app.post("/add_urls")
def add_urls(
    URL: str,
    current_user = Depends(get_current_active_user)
):
    """添加网页内容到知识库"""
    try:
        # 验证 URL
        if not URL or not URL.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="无效的 URL")
        
        # 加载网页内容
        loader = WebBaseLoader(URL)
        docs = loader.load()
        
        # 分割文档
        documents = RecursiveCharacterTextSplitter(
            chunk_size=800, 
            chunk_overlap=50
        ).split_documents(docs)
        
        # 获取配置
        qdrant_config = config.get_qdrant_config()
        embedding_config = config.get_embedding_config()
        
        # 创建向量数据库
        qdrant = Qdrant.from_documents(
            documents,
            OllamaEmbeddings(**embedding_config),
            path=qdrant_config["path"],
            collection_name=qdrant_config["collection_name"],
        )
        
        server_logger.info(f'用户 {current_user.username} 成功添加 URL: {URL} 到向量数据库')
        return {"response": "网页内容添加成功！"}
        
    except Exception as e:
        error_msg = format_error_message(e, f"添加 URL: {URL}")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="添加网页内容失败，请稍后再试")


@app.post("/add_pdfs")
def add_pdfs(current_user = Depends(get_current_active_user)):
    """添加 PDF 文档（待实现）"""
    return {"response": "PDF 添加功能开发中..."}


@app.post("/add_texts")  
def add_texts(current_user = Depends(get_current_active_user)):
    """添加文本内容（待实现）"""
    return {"response": "文本添加功能开发中..."}


@app.get("/health")
def health_check():
    """健康检查"""
    try:
        from services.tts_service import tts_service

        # 检查配置
        config_valid = config.validate_config()
        tts_available = tts_service.is_available()
        db_available = False
        
        # 检查数据库连接
        try:
            from database.connection import check_database_connection
            db_available = check_database_connection()
        except:
            db_available = False
        
        return {
            "status": "healthy" if config_valid and db_available else "warning",
            "config_valid": config_valid,
            "tts_available": tts_available,
            "database_available": db_available,
            "version": "2.1.0",
            "features": {
                "chat": True,
                "tts": tts_available,
                "knowledge_base": True,
                "websocket": True,
                "authentication": True
            }
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# 聊天历史记录接口
@app.get("/chat/sessions")
def get_chat_sessions(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户的聊天会话列表"""
    try:
        sessions = ChatHistoryService.get_chat_sessions(db, current_user.id)
        return {
            "sessions": [ChatHistoryService.session_to_dict(session) for session in sessions]
        }
    except Exception as e:
        error_msg = format_error_message(e, "获取聊天会话列表")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="获取会话列表失败")


@app.get("/chat/history")
def get_chat_history(
    session_id: str = None,
    skip: int = 0,
    limit: int = 50,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取聊天历史记录"""
    try:
        history = ChatHistoryService.get_chat_history(
            db, current_user.id, session_id, skip, limit
        )
        return {
            "history": [ChatHistoryService.to_dict(record) for record in history]
        }
    except Exception as e:
        error_msg = format_error_message(e, "获取聊天历史")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="获取聊天历史失败")


@app.get("/chat/session/{session_id}/history")
def get_session_history(
    session_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取特定会话的聊天历史"""
    try:
        history = ChatHistoryService.get_session_history(db, current_user.id, session_id)
        return {
            "session_id": session_id,
            "history": [ChatHistoryService.to_dict(record) for record in history]
        }
    except Exception as e:
        error_msg = format_error_message(e, f"获取会话 {session_id} 的聊天历史")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="获取会话聊天历史失败")


@app.put("/chat/session/{session_id}/title")
def update_session_title(
    session_id: str,
    title: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新会话标题"""
    try:
        session = ChatHistoryService.update_session_title(
            db, current_user.id, session_id, title
        )
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {
            "message": "会话标题更新成功",
            "session": ChatHistoryService.session_to_dict(session)
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = format_error_message(e, f"更新会话 {session_id} 标题")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="更新会话标题失败")


@app.delete("/chat/session/{session_id}")
def delete_session(
    session_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除聊天会话"""
    try:
        success = ChatHistoryService.delete_session(db, current_user.id, session_id)
        if not success:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {"message": "会话删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        error_msg = format_error_message(e, f"删除会话 {session_id}")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="删除会话失败")


@app.get("/chat/stats")
def get_chat_stats(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取聊天统计信息"""
    try:
        stats = ChatHistoryService.get_chat_stats(db, current_user.id)
        return stats
    except Exception as e:
        error_msg = format_error_message(e, "获取聊天统计")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="获取聊天统计失败")


@app.get("/chat/recent")
def get_recent_chats(
    days: int = 7,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取最近几天的聊天记录"""
    try:
        if days < 1 or days > 30:
            raise HTTPException(status_code=400, detail="天数必须在1-30之间")
        
        recent_chats = ChatHistoryService.get_recent_chats(db, current_user.id, days)
        return {
            "days": days,
            "chats": [ChatHistoryService.to_dict(record) for record in recent_chats]
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = format_error_message(e, f"获取最近 {days} 天的聊天记录")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="获取最近聊天记录失败")


@app.websocket('/ws')
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


if __name__ == '__main__':
    import uvicorn
    
    server_logger.info("🔮 算命师机器人服务启动中...")
    server_logger.info(f"📍 服务地址: http://localhost:8001")
    server_logger.info(f"🌐 API 文档: http://localhost:8001/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
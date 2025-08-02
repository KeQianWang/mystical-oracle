"""
Mystical Oracle Server - 神秘预言师 Web 服务器
使用配置管理和更好的错误处理，集成语音合成功能
"""
import sys
import os
import uuid
from pathlib import Path

# 设置必要的环境变量
os.environ.setdefault("USER_AGENT", "Mozilla/5.0 (Mystical Oracle/1.0)")

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from langchain_community.document_loaders import WebBaseLoader
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import Qdrant
from langchain_text_splitters import RecursiveCharacterTextSplitter

from agent import Master
from config.settings import config
from utils.helpers import validate_user_input, format_error_message
from config.logger import server_logger

# 创建 FastAPI 应用
app = FastAPI(
    title="Mystical Oracle API",
    description="神秘预言师 - 基于 LangChain 的智能算命师聊天机器人，支持语音合成",
    version="1.0.0"
)


@app.get("/")
def get_root():
    """根路径"""
    return {"response": "神秘预言师服务正在运行", "service": "Mystical Oracle"}


@app.post("/chat")
def chat(query: str, background_tasks: BackgroundTasks):
    """与算命师对话，支持语音合成"""
    try:
        # 验证输入
        if not validate_user_input(query):
            raise HTTPException(status_code=400, detail="输入内容无效")
        
        # 创建算命师实例并处理对话
        master = Master()
        result = master.run(query)
        
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
def add_urls(URL: str):
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
        
        server_logger.info(f'成功添加 URL: {URL} 到向量数据库')
        return {"response": "网页内容添加成功！"}
        
    except Exception as e:
        error_msg = format_error_message(e, f"添加 URL: {URL}")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="添加网页内容失败，请稍后再试")


@app.post("/add_pdfs")
def add_pdfs():
    """添加 PDF 文档（待实现）"""
    return {"response": "PDF 添加功能开发中..."}


@app.post("/add_texts")  
def add_texts():
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
        
        return {
            "status": "healthy" if config_valid else "warning",
            "config_valid": config_valid,
            "tts_available": tts_available,
            "version": "2.1.0",
            "features": {
                "chat": True,
                "tts": tts_available,
                "knowledge_base": True,
                "websocket": True
            }
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


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
    server_logger.info(f"📍 服务地址: http://localhost:8000")
    server_logger.info(f"🌐 API 文档: http://localhost:8000/docs")
    
    uvicorn.run(app, host="localhost", port=8000)
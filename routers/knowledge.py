"""
知识库管理接口路由器
包含添加网页、PDF、文本内容到知识库的接口
"""
from fastapi import APIRouter, Depends, HTTPException
from langchain_community.document_loaders import WebBaseLoader
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import Qdrant
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import config
from utils.helpers import format_error_message
from config.logger import server_logger
from services.auth import get_current_active_user

router = APIRouter(tags=["知识库管理"])


@router.post("/add_urls")
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


@router.post("/add_pdfs")
def add_pdfs(current_user = Depends(get_current_active_user)):
    """添加 PDF 文档（待实现）"""
    return {"response": "PDF 添加功能开发中..."}


@router.post("/add_texts")  
def add_texts(current_user = Depends(get_current_active_user)):
    """添加文本内容（待实现）"""
    return {"response": "文本添加功能开发中..."}
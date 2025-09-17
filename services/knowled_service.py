import os
import shutil

from fastapi import HTTPException, UploadFile
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader, Docx2txtLoader, UnstructuredExcelLoader
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import Qdrant
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import config
from config.logger import server_logger
from utils.helpers import format_error_message


class KnowledgeService:
    """知识库写入服务"""

    BASE_UPLOAD_DIR = "./uploads"  # 所有用户上传文件根目录
    BASE_QDRANT_DIR = "./qdrant"   # 所有用户向量数据库根目录

    @staticmethod
    def get_user_collection_name(user_id: int) -> str:
        """返回用户唯一 collection 名"""
        return f"knowledge_user_{user_id}"

    @staticmethod
    def save_upload_file(file: UploadFile, user_id: int) -> str:
        """保存上传文件到用户目录"""
        user_dir = os.path.join(KnowledgeService.BASE_UPLOAD_DIR, f"user_{user_id}")
        os.makedirs(user_dir, exist_ok=True)
        file_path = os.path.join(user_dir, file.filename)

        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        return file_path

    @staticmethod
    def load_from_file(file: UploadFile, user_id: int):
        """加载文件内容"""
        file_path = KnowledgeService.save_upload_file(file, user_id)
        ext = file.filename.split(".")[-1].lower()
        try:
            if ext == "pdf":
                loader = PyPDFLoader(file_path)
            elif ext == "docx":
                loader = Docx2txtLoader(file_path)
            elif ext in ["xls", "xlsx"]:
                loader = UnstructuredExcelLoader(file_path, mode="elements")
            else:
                raise HTTPException(status_code=400, detail="仅支持 docx, pdf, xlsx 文件")

            return loader.load(), f"文件: {file.filename}"

        except Exception as e:
            error_msg = format_error_message(e, "加载文件内容")
            server_logger.error(error_msg)
            return None


    @staticmethod
    def load_from_url(url: str):
        """加载网页内容"""
        if not url or not url.startswith(("http://", "https://")):
            raise HTTPException(status_code=400, detail="无效的 URL")
        loader = WebBaseLoader(url)
        return loader.load(), f"URL: {url}"

    @staticmethod
    def split_documents(docs):
        """分割文档"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=50
        )
        return splitter.split_documents(docs)

    @staticmethod
    def add_to_qdrant(documents, user_id: int):
        """写入用户专属 Collection"""
        qdrant_config = config.get_qdrant_config()# todo 要删除
        embedding_config = config.get_embedding_config()

        user_qdrant_path = os.path.join(KnowledgeService.BASE_QDRANT_DIR, f"user_{user_id}")
        collection_name = KnowledgeService.get_user_collection_name(user_id)

        Qdrant.from_documents(
            documents,
            OllamaEmbeddings(**embedding_config),
            path=user_qdrant_path,
            collection_name=collection_name,
        )
        server_logger.info(f"数据已成功添加到用户 {user_id} 的知识库 (collection: {collection_name})")
        return {"response": f"数据已成功添加到用户 {user_id} 的知识库 (collection: {collection_name})"}

    @staticmethod
    def process_file(file: UploadFile, user_id: int):
        """处理上传文件"""
        docs, _ = KnowledgeService.load_from_file(file, user_id)
        documents = KnowledgeService.split_documents(docs)
        return KnowledgeService.add_to_qdrant(documents, user_id)

    @staticmethod
    def process_url(url: str, user_id: int):
        """处理 URL"""
        docs, _ = KnowledgeService.load_from_url(url)
        documents = KnowledgeService.split_documents(docs)
        return KnowledgeService.add_to_qdrant(documents, user_id)
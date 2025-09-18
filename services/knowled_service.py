import os
import shutil

from fastapi import HTTPException, UploadFile
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader, Docx2txtLoader, UnstructuredExcelLoader
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import Qdrant
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.models import Filter, FieldCondition, MatchValue

from config.settings import config
from config.logger import server_logger
from utils.helpers import format_error_message


class KnowledgeService:
    """知识库写入服务"""

    BASE_UPLOAD_DIR = "./uploads"  # 所有用户上传文件根目录
    BASE_QDRANT_DIR = "./qdrant"   # 所有用户向量数据库根目录
    COLLECTION_NAME = "knowledge_base"  # 统一的知识库 collection 名

    @staticmethod
    def save_upload_file(file: UploadFile, session_id: str) -> str:
        """保存上传文件到用户目录"""
        user_dir = os.path.join(KnowledgeService.BASE_UPLOAD_DIR, f"{session_id}")
        os.makedirs(user_dir, exist_ok=True)
        file_path = os.path.join(user_dir, file.filename)

        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        return file_path

    @staticmethod
    def load_from_file(file: UploadFile, session_id: str):
        """加载文件内容"""
        file_path = KnowledgeService.save_upload_file(file, session_id)
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
    def add_to_qdrant(documents, session_id: str):
        """写入统一 Collection，按 session_id 区分"""
        embedding_config = config.get_embedding_config()

        # 为每个文档添加 session_id 元数据
        for doc in documents:
            doc.metadata["session_id"] = session_id

        Qdrant.from_documents(
            documents,
            OllamaEmbeddings(**embedding_config),
            path=KnowledgeService.BASE_QDRANT_DIR,
            collection_name=KnowledgeService.COLLECTION_NAME
        )
        server_logger.info(f"数据已成功添加到对话框 {session_id} 的知识库 (collection:{KnowledgeService.COLLECTION_NAME})")
        return {"response": f"数据已成功添加到对话框 {session_id} 的知识库 (collection:{KnowledgeService.COLLECTION_NAME})"}

    @staticmethod
    def process_file(file: UploadFile, session_id: str):
        """处理上传文件"""
        docs, _ = KnowledgeService.load_from_file(file, session_id)
        documents = KnowledgeService.split_documents(docs)
        return KnowledgeService.add_to_qdrant(documents, session_id)

    @staticmethod
    def process_url(url: str, session_id: str):
        """处理 URL"""
        docs, _ = KnowledgeService.load_from_url(url)
        documents = KnowledgeService.split_documents(docs)
        return KnowledgeService.add_to_qdrant(documents, session_id)

    @staticmethod
    def search_user_knowledge(query: str, session_id: str, k: int = 1) -> str:
        """在用户专属向量数据库中检索相关内容"""
        try:
            embedding_config = config.get_embedding_config()
            embeddings = OllamaEmbeddings(**embedding_config)

            # 创建 Qdrant 实例 (使用正确的初始化方式)
            qdrant = Qdrant.from_existing_collection(
                embedding=embeddings,
                path=KnowledgeService.BASE_QDRANT_DIR,
                collection_name=KnowledgeService.COLLECTION_NAME
            )

            # 使用过滤器只检索该用户的数据
            filter_condition = Filter(
                must=[
                    FieldCondition(
                        key="metadata.session_id",
                        match=MatchValue(value=session_id)
                    )
                ]
            )

            # 执行相似性搜索
            retriever = qdrant.as_retriever(
                search_type="similarity_score_threshold",  # 使用基于阈值的相似度搜索
                search_kwargs={
                    "score_threshold": .5,  # 相似度阈值设为0.5
                    "k": k  # 最多返回k个结果
                },
                filter=filter_condition  # 还要满足用户ID过滤条件
            )
            docs = retriever.invoke(query)

            # 格式化返回结果
            if docs:
                formatted_docs = "\n\n".join([
                    f"来源: {doc.metadata.get('source', '未知')}\n内容: {doc.page_content}"
                    for doc in docs
                ])
                return formatted_docs
            else:
                return "未找到相关信息"

        except Exception as e:
            error_msg = format_error_message(e, f"检索用户当前对话框 {session_id} 的知识库")
            server_logger.error(error_msg)
            raise HTTPException(status_code=500, detail="知识库检索失败")

import os
import shutil

from fastapi import HTTPException, UploadFile
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader, Docx2txtLoader, UnstructuredExcelLoader
from langchain_qdrant import Qdrant
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.models import Filter, FieldCondition, MatchValue

from config.settings import config
from config.logger import server_logger
from utils.helpers import format_error_message


class KnowledgeService:
    """知识库写入服务"""
    def __init__(self):
        self.qdrant_config = config.get_qdrant_config()
        self.BASE_UPLOAD_DIR = self.qdrant_config["base_upload_dir"]
        self.BASE_QDRANT_DIR = self.qdrant_config["path"]
        self.COLLECTION_NAME = self.qdrant_config["collection_name"]

    def save_upload_file(self, file: UploadFile, session_id: str) -> str:
        """保存上传文件到用户目录"""
        user_dir = os.path.join(self.BASE_UPLOAD_DIR, f"{session_id}")
        os.makedirs(user_dir, exist_ok=True)
        file_path = os.path.join(user_dir, file.filename)

        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        return file_path

    def load_from_file(self, file: UploadFile, session_id: str):
        """加载文件内容"""
        file_path = self.save_upload_file(file, session_id)
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

    def add_to_qdrant(self, documents, session_id: str):
        """写入统一 Collection，按 session_id 区分"""
        try:
            embeddings = config.get_embedding_model()

            # 为每个文档添加 session_id 元数据
            for doc in documents:
                doc.metadata["session_id"] = session_id

            # 添加文档到 Qdrant
            Qdrant.from_documents(
                documents,
                embeddings,
                path=self.BASE_QDRANT_DIR,
                collection_name=self.COLLECTION_NAME
            )

            server_logger.info(f"数据已成功添加到对话框 {session_id} 的知识库 (collection:{self.COLLECTION_NAME})")
            return {"response": f"数据已成功添加到对话框 {session_id} 的知识库 (collection:{self.COLLECTION_NAME})"}

        except Exception as e:
            # 处理其他所有异常
            error_msg = format_error_message(e, f"添加文档到知识库: session_id={session_id}")
            server_logger.error(error_msg)
            raise HTTPException(status_code=500, detail="添加文档到知识库失败，请稍后再试")

    def process_file(self, file: UploadFile, session_id: str):
        """处理上传文件"""
        docs, _ = self.load_from_file(file, session_id)
        documents = KnowledgeService.split_documents(docs)
        return self.add_to_qdrant(documents, session_id)

    def process_url(self, url: str, session_id: str):
        """处理 URL"""
        docs, _ = KnowledgeService.load_from_url(url)
        documents = KnowledgeService.split_documents(docs)
        return self.add_to_qdrant(documents, session_id)

    def search_user_knowledge(self, query: str, session_id: str, k: int = 1) -> str:
        """在用户专属向量数据库中检索相关内容"""
        try:
            embeddings = config.get_embedding_model()

            # 创建 Qdrant 实例
            qdrant = Qdrant.from_existing_collection(
                embedding=embeddings,
                path=self.BASE_QDRANT_DIR,
                collection_name=self.COLLECTION_NAME
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
                    "k": k,  # 最多返回k个结果
                    "filter": filter_condition  # 还要满足用户ID过滤条件
                },
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


    def delete_user_knowledge(self, session_id: str) -> dict:
        """删除用户专属向量数据库中的内容"""
        try:
            embeddings = config.get_embedding_model()

            # 创建 Qdrant 实例
            qdrant = Qdrant.from_existing_collection(
                embedding=embeddings,
                path=self.BASE_QDRANT_DIR,
                collection_name=self.COLLECTION_NAME
            )

            # 构建过滤条件，匹配指定 session_id 的数据
            filter_condition = Filter(
                must=[
                    FieldCondition(
                        key="metadata.session_id",
                        match=MatchValue(value=session_id)
                    )
                ]
            )

            # 获取要删除的点ID
            # 注意：Qdrant 删除操作需要点ID，所以我们需要先查询再删除
            search_result = qdrant.client.scroll(
                collection_name=self.COLLECTION_NAME,
                scroll_filter=filter_condition,
                limit=10000,  # 设置一个较大的限制以获取所有匹配项
                with_payload=True,
                with_vectors=False
            )

            # 提取点ID
            point_ids = [point.id for point in search_result[0]]

            if point_ids:
                # 执行删除操作
                qdrant.client.delete(
                    collection_name=self.COLLECTION_NAME,
                    points_selector=point_ids
                )

                server_logger.info(f"已删除 session_id={session_id} 的 {len(point_ids)} 条向量数据")
                return {
                    "response": f"已成功删除对话框 {session_id} 的 {len(point_ids)} 条知识库数据",
                    "deleted_count": len(point_ids)
                }
            else:
                server_logger.info(f"未找到 session_id={session_id} 的向量数据")
                return {
                    "response": f"未找到对话框 {session_id} 的知识库数据",
                    "deleted_count": 0
                }

        except Exception as e:
            error_msg = format_error_message(e, f"删除用户当前对话框 {session_id} 的知识库")
            server_logger.error(error_msg)
            raise HTTPException(status_code=500, detail="知识库删除失败")

    def delete_upload_files(self, session_id: str) -> dict:
        """删除指定 session_id 的上传文件"""
        try:
            # 构建用户目录路径
            user_dir = os.path.join(self.BASE_UPLOAD_DIR, f"{session_id}")

            # 检查目录是否存在
            if os.path.exists(user_dir) and os.path.isdir(user_dir):
                # 删除整个用户目录及其内容
                shutil.rmtree(user_dir)
                server_logger.info(f"已删除 session_id={session_id} 的上传文件目录: {user_dir}")
                return {
                    "response": f"已成功删除对话框 {session_id} 的上传文件",
                    "deleted": True
                }
            else:
                server_logger.info(f"未找到 session_id={session_id} 的上传文件目录: {user_dir}")
                return {
                    "response": f"未找到对话框 {session_id} 的上传文件",
                    "deleted": False
                }

        except Exception as e:
            error_msg = format_error_message(e, f"删除用户当前对话框 {session_id} 的上传文件")
            server_logger.error(error_msg)
            raise HTTPException(status_code=500, detail="文件删除失败")

# 全局 TTS 服务实例
knowledge_service = KnowledgeService()
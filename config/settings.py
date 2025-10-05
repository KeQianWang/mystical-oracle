"""
配置管理模块
统一管理所有配置项，包括模型参数、数据库连接、API 配置等
"""
import os
from typing import Dict, Any, Optional, Union

from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

from config.logger import logger

# 加载 .env 文件
load_dotenv()

class BotConfig:
    """机器人配置类"""

    # === 基础配置 ===
    MODEL_TEMPERATURE: float = float(os.getenv("MODEL_TEMPERATURE", 0.7))
    MAX_HISTORY_MESSAGES: int = int(os.getenv("MAX_HISTORY_MESSAGES", 20))

    # === 模型配置 ===
    OLLAMA_BASE_URL: Optional[str] = os.getenv("OLLAMA_BASE_URL")
    OLLAMA_MODEL_NAME: Optional[str] = os.getenv("OLLAMA_MODEL_NAME")

    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_API_BASE: Optional[str] = os.getenv("OPENAI_API_BASE")
    OPENAI_MODEL: Optional[str] = os.getenv("OPENAI_MODEL")

    OLLAMA_EMBEDDINGS: Optional[str] = os.getenv("EMBEDDING_MODEL_NAME")
    OPEN_AI_EMBEDDINGS: Optional[str] = os.getenv("OPEN_AI_EMBEDDINGS")

    # === 存储配置 ===
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    QDRANT_PATH: Optional[str] = os.getenv("QDRANT_PATH")
    QDRANT_COLLECTION_NAME: Optional[str] = os.getenv("QDRANT_COLLECTION_NAME")
    BASE_UPLOAD_DIR: Optional[str] = os.getenv("BASE_UPLOAD_DIR")

    MYSQL_HOST: Optional[str] = os.getenv("MYSQL_HOST")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER: Optional[str] = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD: Optional[str] = os.getenv("MYSQL_PASSWORD")
    MYSQL_DATABASE: Optional[str] = os.getenv("MYSQL_DATABASE")

    # === JWT 配置 ===
    JWT_SECRET_KEY: Optional[str] = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", 720))

    # === API 配置 ===
    SERPAPI_API_KEY: Optional[str] = os.getenv("SERPAPI_API_KEY")
    YUANFENJU_API_KEY: Optional[str] = os.getenv("YUANFENJU_API_KEY")
    MICROSOFT_TTS_KEY: Optional[str] = os.getenv("MICROSOFT_TTS_KEY")

    # === TTS 配置 ===
    TTS_ENDPOINT: Optional[str] = os.getenv("TTS_ENDPOINT")
    TTS_VOICE_NAME: Optional[str] = os.getenv("TTS_VOICE_NAME")
    TTS_OUTPUT_FORMAT: Optional[str] = os.getenv("TTS_OUTPUT_FORMAT")
    AUDIO_OUTPUT_DIR: Optional[str] = os.getenv("AUDIO_OUTPUT_DIR")

    YUANFENJU_ENDPOINTS = {
        "bazi_cesuan": "https://api.yuanfenju.com/index.php/v1/Bazi/cesuan",
        "yaoyigua": "https://api.yuanfenju.com/index.php/v1/Zhanbu/meiri",
        "jiemeng": "https://api.yuanfenju.com/index.php/v1/Gongju/zhougong",
    }

    # === 缓存对象 ===
    _cached_model: Optional[Union[ChatOllama, ChatOpenAI]] = None
    _cached_embedding_model: Optional[Union[OllamaEmbeddings, OpenAIEmbeddings]] = None

    # ========= 公共方法 =========
    @classmethod
    def _lazy_init(cls, attr_name: str, factory):
        """通用懒加载 + 缓存工具"""
        if getattr(cls, attr_name) is None:
            try:
                setattr(cls, attr_name, factory())
            except Exception as e:
                logger.error(f"{attr_name} 初始化失败: {e}")
        return getattr(cls, attr_name)

    # === 模型获取 ===
    @classmethod
    def get_model(cls) -> Optional[Union[ChatOllama, ChatOpenAI]]:
        return cls._lazy_init("_cached_model", lambda: cls._create_chat_model())

    @classmethod
    def _create_chat_model(cls):
        if cls.OPENAI_MODEL and cls.OPENAI_API_KEY:
            return ChatOpenAI(
                model=cls.OPENAI_MODEL,
                temperature=cls.MODEL_TEMPERATURE,
                api_key=cls.OPENAI_API_KEY,
                base_url=cls.OPENAI_API_BASE or None,
                streaming=True,
            )
        elif cls.OLLAMA_MODEL_NAME and cls.OLLAMA_BASE_URL:
            return ChatOllama(
                model=cls.OLLAMA_MODEL_NAME,
                temperature=cls.MODEL_TEMPERATURE,
                base_url=cls.OLLAMA_BASE_URL,
            )
        raise RuntimeError("未配置可用的聊天模型")

    # === 嵌入模型获取 ===
    @classmethod
    def get_embedding_model(cls) -> Optional[Union[OllamaEmbeddings, OpenAIEmbeddings]]:
        return cls._lazy_init("_cached_embedding_model", lambda: cls._create_embedding_model())

    @classmethod
    def _create_embedding_model(cls):
        if cls.OPEN_AI_EMBEDDINGS and cls.OPENAI_API_KEY:
            return OpenAIEmbeddings(
                model=cls.OPEN_AI_EMBEDDINGS,
                api_key=cls.OPENAI_API_KEY,
                base_url=cls.OPENAI_API_BASE or None,
            )
        elif cls.OLLAMA_EMBEDDINGS and cls.OLLAMA_BASE_URL:
            return OllamaEmbeddings(
                model=cls.OLLAMA_EMBEDDINGS,
                base_url=cls.OLLAMA_BASE_URL,
            )
        raise RuntimeError("未配置可用的嵌入模型")

    # === 其他配置获取 ===
    @classmethod
    def get_qdrant_config(cls) -> Dict[str, Any]:
        return {
            "path": cls.QDRANT_PATH,
            "collection_name": cls.QDRANT_COLLECTION_NAME,
            "base_upload_dir": cls.BASE_UPLOAD_DIR,
        }

    @classmethod
    def get_redis_config(cls) -> Dict[str, Any]:
        return {"url": cls.REDIS_URL}

    @classmethod
    def get_mysql_config(cls) -> Dict[str, Any]:
        return {
            "host": cls.MYSQL_HOST,
            "port": cls.MYSQL_PORT,
            "user": cls.MYSQL_USER,
            "password": cls.MYSQL_PASSWORD,
            "database": cls.MYSQL_DATABASE,
        }

    @classmethod
    def get_jwt_config(cls) -> Dict[str, Any]:
        return {
            "secret_key": cls.JWT_SECRET_KEY,
            "algorithm": cls.JWT_ALGORITHM,
            "expire_minutes": cls.JWT_EXPIRE_MINUTES,
        }

    @classmethod
    def validate_config(cls) -> bool:
        """验证关键配置完整性"""
        required_keys = ["SERPAPI_API_KEY", "YUANFENJU_API_KEY", "MICROSOFT_TTS_KEY"]
        missing = [key for key in required_keys if not os.getenv(key)]
        if missing:
            logger.warning(f"缺少环境变量: {', '.join(missing)}")
            return False
        return True


# 全局配置实例
config = BotConfig()
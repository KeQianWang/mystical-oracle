"""
配置管理模块
统一管理所有配置项，包括模型参数、数据库连接、API 配置等
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

# 加载环境变量
load_dotenv()


class BotConfig:
    """机器人配置类"""
    
    # ollama模型配置
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
    OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME")

    #openAi模型配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL")

    #embedding模型配置
    OLLAMA_EMBEDDINGS = os.getenv("OLLAMA_EMBEDDINGS")
    OPEN_AI_EMBEDDINGS = os.getenv("OPEN_AI_EMBEDDINGS")


    MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE"))
    
    # 数据库配置
    REDIS_URL = os.getenv("REDIS_URL")
    QDRANT_PATH = os.getenv("QDRANT_PATH")
    QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME")
    BASE_UPLOAD_DIR = os.getenv("BASE_UPLOAD_DIR")


    # MySQL 数据库配置
    MYSQL_HOST = os.getenv("MYSQL_HOST")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
    
    # JWT 配置
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 720))  # 12小时
    
    # Agent 配置
    MEMORY_KEY = os.getenv("MEMORY_KEY")
    MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES"))  # 超过此数量会进行摘要
    
    # API 配置
    SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
    YUANFENJU_API_KEY = os.getenv("YUANFENJU_API_KEY")
    MICROSOFT_TTS_KEY = os.getenv("MICROSOFT_TTS_KEY")
    
    # TTS 配置
    TTS_ENDPOINT = os.getenv("TTS_ENDPOINT")
    TTS_VOICE_NAME = os.getenv("TTS_VOICE_NAME")
    TTS_OUTPUT_FORMAT = os.getenv("TTS_OUTPUT_FORMAT")
    AUDIO_OUTPUT_DIR = os.getenv("AUDIO_OUTPUT_DIR")
    
    # 缘分居 API 端点
    YUANFENJU_ENDPOINTS = {
        "bazi_cesuan": "https://api.yuanfenju.com/index.php/v1/Bazi/cesuan",
        "yaoyigua": "https://api.yuanfenju.com/index.php/v1/Zhanbu/meiri", 
        "jiemeng": "https://api.yuanfenju.com/index.php/v1/Gongju/zhougong"
    }
    
    # 情绪列表
    MOOD_TYPES = ["default", "upbeat", "angry", "depressed", "friendly", "cheerful"]
    
    @classmethod
    def get_model_config(cls) -> None | ChatOllama | ChatOpenAI:
        """获取聊天模型配置"""
        temperature = cls.MODEL_TEMPERATURE
        if cls.OPENAI_MODEL:
            model_name = cls.OPENAI_MODEL
            return ChatOpenAI(model=model_name,temperature=temperature)
        elif cls.OLLAMA_MODEL_NAME:
            model_name = cls.OLLAMA_MODEL_NAME
            return ChatOllama(model=model_name,temperature=temperature)
        return None

    @classmethod
    def get_embedding_model(cls) -> None | OllamaEmbeddings | OpenAIEmbeddings:
        """获取嵌入模型配置"""
        if cls.OPEN_AI_EMBEDDINGS:
            model_name = cls.OPEN_AI_EMBEDDINGS
            return OpenAIEmbeddings(model=model_name)
        elif cls.OLLAMA_EMBEDDINGS:
            model_name = cls.OLLAMA_EMBEDDINGS
            return OllamaEmbeddings(model=model_name)
        return None

    @classmethod
    def get_qdrant_config(cls) -> Dict[str, Any]:
        """获取 Qdrant 配置"""
        return {
            "path": cls.QDRANT_PATH,
            "collection_name": cls.QDRANT_COLLECTION_NAME,
            "base_upload_dir":cls.BASE_UPLOAD_DIR,
        }
    
    @classmethod
    def get_redis_config(cls) -> Dict[str, Any]:
        """获取 Redis 配置"""
        return {
            "url": cls.REDIS_URL
        }

    @classmethod
    def get_mysql_config(cls) -> Dict[str, Any]:
        """获取 MySQL 配置"""
        return {
            "host": cls.MYSQL_HOST,
            "port": cls.MYSQL_PORT,
            "user": cls.MYSQL_USER,
            "password": cls.MYSQL_PASSWORD,
            "database": cls.MYSQL_DATABASE
        }

    @classmethod
    def get_jwt_config(cls) -> Dict[str, Any]:
        """获取 JWT 配置"""
        return {
            "secret_key": cls.JWT_SECRET_KEY,
            "algorithm": cls.JWT_ALGORITHM,
            "expire_minutes": cls.JWT_EXPIRE_MINUTES
        }

    @classmethod
    def validate_config(cls) -> bool:
        """验证配置完整性"""
        required_keys = ["SERPAPI_API_KEY", "YUANFENJU_API_KEY", "MICROSOFT_TTS_KEY"]
        missing_keys = [key for key in required_keys if not os.getenv(key)]
        
        if missing_keys:
            import logging
            logging.warning(f"缺少环境变量: {', '.join(missing_keys)}")
            return False
        return True


# 全局配置实例
config = BotConfig()
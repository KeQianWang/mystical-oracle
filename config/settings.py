"""
配置管理模块
统一管理所有配置项，包括模型参数、数据库连接、API 配置等
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class BotConfig:
    """机器人配置类"""
    
    # 模型配置
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
    CHAT_MODEL_NAME = os.getenv("CHAT_MODEL_NAME")
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")
    MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE"))
    
    # 数据库配置
    QDRANT_PATH = os.getenv("QDRANT_PATH")
    QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME")
    REDIS_URL = os.getenv("REDIS_URL")
    
    # Agent 配置
    DEFAULT_SESSION_ID = os.getenv("DEFAULT_SESSION_ID")
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
    
    # 缘分居 API 端点
    YUANFENJU_ENDPOINTS = {
        "bazi_cesuan": "https://api.yuanfenju.com/index.php/v1/Bazi/cesuan",
        "yaoyigua": "https://api.yuanfenju.com/index.php/v1/Zhanbu/meiri", 
        "jiemeng": "https://api.yuanfenju.com/index.php/v1/Gongju/zhougong"
    }
    
    # 情绪列表
    MOOD_TYPES = ["default", "upbeat", "angry", "depressed", "friendly", "cheerful"]
    
    @classmethod
    def get_model_config(cls) -> Dict[str, Any]:
        """获取模型配置"""
        return {
            "base_url": cls.OLLAMA_BASE_URL,
            "model": cls.CHAT_MODEL_NAME,
            "temperature": cls.MODEL_TEMPERATURE
        }
    
    @classmethod
    def get_embedding_config(cls) -> Dict[str, Any]:
        """获取嵌入模型配置"""
        return {
            "model": cls.EMBEDDING_MODEL_NAME
        }
    
    @classmethod
    def get_qdrant_config(cls) -> Dict[str, Any]:
        """获取 Qdrant 配置"""
        return {
            "path": cls.QDRANT_PATH,
            "collection_name": cls.QDRANT_COLLECTION_NAME
        }
    
    @classmethod
    def get_redis_config(cls) -> Dict[str, Any]:
        """获取 Redis 配置"""
        return {
            "url": cls.REDIS_URL
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
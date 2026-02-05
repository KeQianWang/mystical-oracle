"""
系统接口路由器
包含根路径和健康检查接口
"""
from fastapi import APIRouter

from config.settings import config
from database.connection import check_database_connection

router = APIRouter(tags=["系统接口"])


@router.get("/")
def get_root():
    """根路径"""
    return {"response": "AI 卜卦服务正在运行", "service": "Mystical Oracle"}


@router.get("/health")
def health_check():
    """健康检查"""
    try:
        # 检查配置
        config_valid = config.validate_config()
        db_available = False
        
        # 检查数据库连接
        try:
            db_available = check_database_connection()
        except:
            db_available = False
        
        return {
            "status": "healthy" if config_valid and db_available else "warning",
            "config_valid": config_valid,
            "database_available": db_available,
            "version": "2.1.0",
            "features": {
                "chat": True,
                "knowledge_base": True,
                "websocket": True,
                "authentication": True
            }
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
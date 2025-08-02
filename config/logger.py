"""
日志配置模块
提供统一的日志管理功能，替代项目中的 print 语句
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

# 从环境变量获取日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "mystical_oracle.log")


class Logger:
    """统一日志管理类"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str, log_file: Optional[str] = None) -> logging.Logger:
        """获取或创建日志器"""
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器（带轮转）
        file_name = log_file or LOG_FILE
        file_handler = RotatingFileHandler(
            file_name,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 缓存日志器
        cls._loggers[name] = logger
        
        return logger


# 为各个模块提供专用日志器
agent_logger = Logger.get_logger('agent')
server_logger = Logger.get_logger('server')
tools_logger = Logger.get_logger('tools')
tts_logger = Logger.get_logger('tts')
config_logger = Logger.get_logger('config')

# 默认日志器
logger = Logger.get_logger('mystical_oracle')
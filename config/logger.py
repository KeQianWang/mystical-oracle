"""
日志配置模块
提供统一的日志管理功能，替代项目中的 print 语句
"""
import os
import logging
import glob
from datetime import datetime, timedelta
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# 从环境变量获取日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", "30"))

# 确保日志目录存在
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)


class Logger:
    """统一日志管理类"""
    
    _loggers = {}
    
    @classmethod
    def _cleanup_old_logs(cls) -> None:
        """清理超过指定天数的日志文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=LOG_RETENTION_DAYS)
            log_pattern = os.path.join(LOG_DIR, "*.log*")
            
            for log_file in glob.glob(log_pattern):
                file_path = Path(log_file)
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    file_path.unlink()
                    print(f"已删除过期日志文件: {log_file}")
        except Exception as e:
            print(f"清理日志文件时出错: {e}")
    
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
        
        # 文件处理器（带轮转），使用日期命名
        if not log_file:
            date_str = datetime.now().strftime("%Y%m%d")
            log_file = os.path.join(LOG_DIR, f"mystical_oracle_{date_str}.log")
        else:
            log_file = os.path.join(LOG_DIR, log_file)
            
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 清理旧日志文件
        cls._cleanup_old_logs()
        
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
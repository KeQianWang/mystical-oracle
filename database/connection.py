"""
Mystical Oracle Database Connection - 数据库连接
提供数据库连接和会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from typing import Generator
from config.settings import config
from config.logger import server_logger
from sqlalchemy import text


# 创建数据库引擎
def get_database_url():
    """获取数据库连接URL"""
    mysql_config = config.get_mysql_config()
    return f"mysql+pymysql://{mysql_config['user']}:{mysql_config['password']}@{mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}"


# 创建数据库引擎
engine = create_engine(
    get_database_url(),
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False  # 设置为True可以查看SQL日志
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        server_logger.error(f"数据库会话错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context():
    """获取数据库会话上下文管理器"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        server_logger.error(f"数据库会话错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_database_if_not_exists():
    """如果数据库不存在则创建"""
    try:
        mysql_config = config.get_mysql_config()
        # 连接到MySQL服务器（不指定数据库）
        temp_engine = create_engine(
            f"mysql+pymysql://{mysql_config['user']}:{mysql_config['password']}@{mysql_config['host']}:{mysql_config['port']}",
            pool_pre_ping=True
        )
        
        with temp_engine.connect() as conn:
            # 检查数据库是否存在
            result = conn.execute(text(f"SHOW DATABASES LIKE '{mysql_config['database']}'"))
            if not result.fetchone():
                # 创建数据库
                conn.execute(text(f"CREATE DATABASE {mysql_config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                server_logger.info(f"数据库 {mysql_config['database']} 创建成功")
            else:
                server_logger.info(f"数据库 {mysql_config['database']} 已存在")
        
        return True
    except Exception as e:
        server_logger.error(f"创建数据库失败: {e}")
        return False


def create_tables():
    """创建数据库表"""
    try:
        # 先确保数据库存在
        create_database_if_not_exists()
        
        from models.database import Base
        Base.metadata.create_all(bind=engine)
        server_logger.info("数据库表创建成功")
    except Exception as e:
        server_logger.error(f"创建数据库表失败: {e}")
        raise


def drop_tables():
    """删除数据库表"""
    from models.database import Base
    try:
        Base.metadata.drop_all(bind=engine)
        server_logger.info("数据库表删除成功")
    except Exception as e:
        server_logger.error(f"删除数据库表失败: {e}")
        raise


def check_database_connection():
    """检查数据库连接"""
    try:
        # 先确保数据库存在
        create_database_if_not_exists()
        
        with get_db_context() as db:
            db.execute(text('SELECT 1'))
        server_logger.info("数据库连接正常")
        return True
    except Exception as e:
        server_logger.error(f"数据库连接失败: {e}")
        return False
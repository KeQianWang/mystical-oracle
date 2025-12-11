"""
Mystical Oracle Database Models - 数据库模型
定义用户和聊天历史相关的数据库模型
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import JSON


Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, index=True, nullable=True, comment="邮箱")
    phone = Column(String(20), unique=True, index=True, nullable=False, comment="手机号")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    avatar_url = Column(String(255), nullable=True, comment="头像URL")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_admin = Column(Boolean, default=False, comment="是否管理员")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    
    # 关联关系
    chat_histories = relationship("ChatHistory", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class ChatHistory(Base):
    """聊天历史表"""
    __tablename__ = "chat_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    session_id = Column(String(100), nullable=False, comment="会话ID")
    user_message = Column(Text, nullable=False, comment="用户消息")
    assistant_message = Column(Text, nullable=False, comment="助手回复")
    mood = Column(String(20), nullable=True, comment="对话情绪")
    message_type = Column(String(20), default="text", comment="消息类型：text/image/audio")
    metadata_data = Column(JSON, nullable=True, comment="元数据")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    
    # 关联关系
    user = relationship("User", back_populates="chat_histories")
    
    # 索引
    __table_args__ = (
        Index('idx_user_session', 'user_id', 'session_id'),
        Index('idx_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ChatHistory(id={self.id}, user_id={self.user_id}, session_id='{self.session_id}')>"


class ChatSession(Base):
    """聊天会话表"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    session_id = Column(String(100), unique=True, nullable=False, comment="会话ID")
    title = Column(String(255), nullable=True, comment="会话标题")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间")
    
    # 索引
    __table_args__ = (
        Index('idx_user_sessions', 'user_id', 'session_id'),
    )
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, session_id='{self.session_id}')>"
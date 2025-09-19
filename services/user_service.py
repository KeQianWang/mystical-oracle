"""
Mystical Oracle User Service - 用户服务
提供用户相关的业务逻辑
"""
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.database import User
from models.user import UserCreate, UserUpdate, UserResponse
from services.auth import get_password_hash, verify_password
from config.logger import server_logger


class UserService:
    """用户服务类"""
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """创建用户"""
        # 检查用户名是否已存在
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )
        
        # 创建用户
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            nickname=user_data.nickname,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        server_logger.info(f"用户创建成功: {user_data.username}")
        return db_user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """更新用户信息"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return None
        
        # 更新用户信息
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        
        server_logger.info(f"用户信息更新成功: {user.username}")
        return user
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """删除用户"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return False
        
        db.delete(user)
        db.commit()
        
        server_logger.info(f"用户删除成功: {user.username}")
        return True
    
    @staticmethod
    def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> list[type[User]]:
        """获取所有用户"""
        return db.query(User).offset(skip).limit(limit).all()
    
    @staticmethod
    def activate_user(db: Session, user_id: int) -> Optional[User]:
        """激活用户"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return None
        
        user.is_active = True
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        
        server_logger.info(f"用户激活成功: {user.username}")
        return user
    
    @staticmethod
    def deactivate_user(db: Session, user_id: int) -> Optional[User]:
        """停用用户"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return None
        
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        
        server_logger.info(f"用户停用成功: {user.username}")
        return user
    
    @staticmethod
    def change_password(db: Session, user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return False
        
        # 验证旧密码
        if not verify_password(old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="旧密码错误"
            )
        
        # 更新密码
        user.password_hash = get_password_hash(new_password)
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        server_logger.info(f"用户密码修改成功: {user.username}")
        return True
    
    @staticmethod
    def to_response(user: User) -> UserResponse:
        """转换为响应模型"""
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )
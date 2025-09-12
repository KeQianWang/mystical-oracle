"""
Mystical Oracle Authentication - 认证服务
提供JWT认证和密码哈希功能
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config.settings import config
from database.connection import get_db
from models.database import User
from models.user import TokenData
from config.logger import server_logger


# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer认证
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        jwt_config = config.get_jwt_config()
        expire = datetime.now(timezone.utc) + timedelta(minutes=jwt_config["expire_minutes"])
    
    to_encode.update({"exp": expire})
    jwt_config = config.get_jwt_config()
    encoded_jwt = jwt.encode(to_encode, jwt_config["secret_key"], algorithm=jwt_config["algorithm"])
    return encoded_jwt


def verify_token(token: str, credentials_exception: HTTPException) -> TokenData:
    """验证JWT令牌"""
    try:
        jwt_config = config.get_jwt_config()
        payload = jwt.decode(token, jwt_config["secret_key"], algorithms=[jwt_config["algorithm"]])
        
        user_id: Optional[int] = payload.get("user_id")
        username: Optional[str] = payload.get("username")
        
        if user_id is None or username is None:
            raise credentials_exception
        
        token_data = TokenData(user_id=user_id, username=username)
        return token_data
        
    except JWTError:
        raise credentials_exception


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """验证用户凭据"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = verify_token(credentials.credentials, credentials_exception)
        user = db.query(User).filter(User.id == token_data.user_id).first()
        if user is None:
            raise credentials_exception
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户已被禁用"
            )
        return user
    except Exception as e:
        server_logger.error(f"认证失败: {e}")
        raise credentials_exception


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已被禁用"
        )
    return current_user


def create_user_token(user: User) -> dict:
    """为用户创建访问令牌"""
    jwt_config = config.get_jwt_config()
    access_token_expires = timedelta(minutes=jwt_config["expire_minutes"])
    access_token = create_access_token(
        data={"user_id": user.id, "username": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": jwt_config["expire_minutes"] * 60
    }


def update_last_login(db: Session, user: User) -> None:
    """更新用户最后登录时间"""
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    server_logger.info(f"用户 {user.username} 最后登录时间已更新")
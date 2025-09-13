"""
用户认证接口路由器
包含用户注册、登录、信息管理接口
"""
from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from sqlalchemy.orm import Session

from models.user import UserCreate, UserLogin, UserResponse, UserUpdate, Token
from services.auth import (
    authenticate_user, 
    create_user_token, 
    get_current_active_user,
    update_last_login
)
from services.user_service import UserService
from utils.helpers import format_error_message
from config.logger import server_logger
from database.connection import get_db

router = APIRouter(prefix="/auth", tags=["用户认证"])


@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    try:
        user = UserService.create_user(db, user_data)
        return UserService.to_response(user)
    except HTTPException:
        raise
    except Exception as e:
        error_msg = format_error_message(e, "用户注册")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="注册失败，请稍后再试")


@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    try:
        # 验证用户
        user = authenticate_user(db, user_data.username, user_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 更新最后登录时间
        update_last_login(db, user)
        
        # 创建访问令牌
        return create_user_token(user)
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = format_error_message(e, "用户登录")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="登录失败，请稍后再试")


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return UserService.to_response(current_user)


@router.put("/update_me", response_model=UserResponse)
def update_current_user(
    user_data: UserUpdate, 
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新当前用户信息"""
    try:
        updated_user = UserService.update_user(db, current_user.id, user_data)
        return UserService.to_response(updated_user)
    except HTTPException:
        raise
    except Exception as e:
        error_msg = format_error_message(e, "更新用户信息")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="更新失败，请稍后再试")
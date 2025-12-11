"""
Mystical Oracle User Model - 用户数据模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, constr, Field, ConfigDict
from config.settings import config
import re

class User(BaseModel):
    """用户信息模型 - 用于八字查询"""
    api_key: str  # API key
    name: str  # 姓名
    sex: int  # 0表示男，1表示女
    type: int = 1  # 日历类型，0农历，1公历，默认1
    year: int  # 出生年份
    month: int  # 出生月份
    day: int  # 出生日期
    hours: int  # 出生小时
    minute: int  # 出生分钟

    @field_validator('api_key')
    @classmethod
    def set_default_api_key(cls, v):
        """设置默认 API key"""
        if not v:
            return config.YUANFENJU_API_KEY
        return v

    @field_validator('sex')
    @classmethod
    def validate_sex(cls, v):
        """验证性别参数"""
        if v not in [0, 1]:
            raise ValueError('性别必须是 0（男）或 1（女）')
        return v

    @field_validator('type')
    @classmethod
    def validate_calendar_type(cls, v):
        """验证日历类型"""
        if v not in [0, 1]:
            raise ValueError('日历类型必须是 0（农历）或 1（公历）')
        return v

    @field_validator('year')
    @classmethod
    def validate_year(cls, v):
        """验证年份"""
        if not (1900 <= v <= 2030):
            raise ValueError('年份必须在 1900-2030 之间')
        return v

    @field_validator('month')
    @classmethod
    def validate_month(cls, v):
        """验证月份"""
        if not (1 <= v <= 12):
            raise ValueError('月份必须在 1-12 之间')
        return v

    @field_validator('day')
    @classmethod
    def validate_day(cls, v):
        """验证日期"""
        if not (1 <= v <= 31):
            raise ValueError('日期必须在 1-31 之间')
        return v

    @field_validator('hours')
    @classmethod
    def validate_hours(cls, v):
        """验证小时"""
        if not (0 <= v <= 23):
            raise ValueError('小时必须在 0-23 之间')
        return v

    @field_validator('minute')
    @classmethod
    def validate_minute(cls, v):
        """验证分钟"""
        if not (0 <= v <= 59):
            raise ValueError('分钟必须在 0-59 之间')
        return v

class UserCreate(BaseModel):
    """用户注册模型"""
    username: constr(min_length=2, max_length=50)
    password: constr(min_length=6, max_length=100)
    phone: constr(min_length=11, max_length=20) = Field(example="13812345678")

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """验证手机号格式"""
        # 简单的中国手机号验证
        phone_pattern = re.compile(r'^1[3-9]\d{9}$')
        if not phone_pattern.match(v):
            raise ValueError('请输入有效的手机号码')
        return v


class UserLogin(BaseModel):
    """用户登录模型"""
    username: constr(min_length=2, max_length=50)
    password: constr(min_length=6, max_length=100)


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    phone: str
    email: Optional[str]
    avatar_url: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """用户更新模型"""
    username: Optional[constr(max_length=50)] = None
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None


class Token(BaseModel):
    """JWT令牌模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """JWT令牌数据模型"""
    user_id: Optional[int] = None
    username: Optional[str] = None

class ChatSessionCreate(BaseModel):
    """创建聊天会话模型"""
    title: str

class ChatSessionUpdate(BaseModel):
    """更新聊天会话模型"""
    title: Optional[str] = None

class ChatSessionResponse(BaseModel):
    """聊天会话响应模型"""
    id: int
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """聊天请求模型"""
    query: str
    session_id: Optional[str] = ""
    enable_tts: bool = False
    async_mode: bool = False

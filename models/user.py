"""
Mystical Oracle User Model - 用户数据模型
优化后的数据模型，使用配置管理
"""
from pydantic import BaseModel, field_validator
from config.settings import config


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

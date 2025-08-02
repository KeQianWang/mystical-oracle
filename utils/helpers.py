"""
工具函数模块
优化后的工具函数，移除硬编码配置
"""
import re
from typing import Any


def delete_think(text: str) -> str:
    """
    清洗模型输出，移除 <think>...</think> 结构
    
    Args:
        text: 原始文本
        
    Returns:
        清洗后的文本
    """
    if not isinstance(text, str):
        return str(text)
    
    # 移除 <think>...</think> 标签及其内容
    cleaned_text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    
    # 移除多余的空白字符
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    return cleaned_text


def format_error_message(error: Exception, context: str = "") -> str:
    """
    格式化错误消息
    
    Args:
        error: 异常对象
        context: 错误上下文
        
    Returns:
        格式化的错误消息
    """
    error_msg = f"{context}: {str(error)}" if context else str(error)
    return f"发生错误 - {error_msg}"


def validate_user_input(input_text: str, min_length: int = 1, max_length: int = 1000) -> bool:
    """
    验证用户输入
    
    Args:
        input_text: 用户输入文本
        min_length: 最小长度
        max_length: 最大长度
        
    Returns:
        是否有效
    """
    if not isinstance(input_text, str):
        return False
    
    input_text = input_text.strip()
    return min_length <= len(input_text) <= max_length


def safe_get_dict_value(dictionary: dict, key: str, default: Any = None) -> Any:
    """
    安全地从字典中获取值
    
    Args:
        dictionary: 目标字典
        key: 键名
        default: 默认值
        
    Returns:
        字典中的值或默认值
    """
    try:
        return dictionary.get(key, default)
    except (AttributeError, TypeError):
        return default

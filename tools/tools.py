"""
Mystical Oracle Tools - AI 卜卦工具集
使用配置管理和更好的错误处理
"""
from typing import Optional

import requests

from langchain.agents import tool
from langchain_community.utilities import SerpAPIWrapper
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from models.user import User
from services.knowledge_service import knowledge_service
from utils.helpers import delete_think
from config.settings import config
from config.logger import tools_logger
from prompts.system_prompts import SystemPrompts


@tool
def search(query: str) -> str:
    """只有需要了解实时信息或不知道的事情的时候才会使用这个工具。"""
    try:
        serp = SerpAPIWrapper()
        result = serp.run(query)
        tools_logger.info(f"实时搜索结果: {result}")
        return result
    except Exception as e:
        tools_logger.error(f"搜索工具出错: {e}")
        return "搜索服务暂时不可用，请稍后再试。"

@tool
def get_info_from_knowledge( query: str,callbacks: Optional[CallbackManagerForToolRun] = None) -> str:
    """
    如果用户上传了文件或者输入了url，或者说了知识库，文件，url相关词汇，会使用这个工具
    """
    session_id = callbacks.metadata['session_id']
    knowledge_result = knowledge_service.search_user_knowledge(query, session_id)
    tools_logger.info(f"知识库返回的结果: {knowledge_result}")
    return knowledge_result


@tool
def bazi_cesuan(query: str) -> str:
    """
    只有做八字排查的时候才会使用这个工具，需要输入用户姓名和出生年月时，如果缺少用户姓名和出生年月时则不可用
    """
    try:
        api_key = config.YUANFENJU_API_KEY
        url = config.YUANFENJU_ENDPOINTS["bazi_cesuan"]
        
        # 设置解析器
        parser = JsonOutputParser(pydantic_object=User)
        
        # 直接使用统一管理的模板
        prompt_template = SystemPrompts.BAZI_PARAM_EXTRACTION_PROMPT
        
        # 使用 partial 方法安全地预填充静态变量
        prompt = ChatPromptTemplate.from_template(prompt_template).partial(
            api_key=api_key,
            format_instructions=parser.get_format_instructions()
        )
        
        # 创建模型
        base_model = config.get_model()
        # 用 bind 临时绑定添加json格式
        if isinstance(base_model, ChatOpenAI):
            model = base_model.bind(response_format={"type": "json_object"})
        elif isinstance(base_model, ChatOllama):
            model = base_model.bind(format="json") # ChatOllama 支持的参数

        # 构建处理链
        chain = prompt | model | parser
        data = chain.invoke({"query": query})

        tools_logger.debug(f'八字查询请求参数: {data}')

        # 调用 API
        result = requests.post(url, data=data)
        if result.status_code == 200:
            tools_logger.debug(f'八字查询返回数据: {result.json()}')
            try:
                data_json = result.json()
                return f"八字排盘完成：{data_json['data']['bazi_info']['bazi']}"
            except Exception as e:
                tools_logger.error(f"解析八字结果失败: {e}")
                return "八字查询失败，可能是你忘记询问用户姓名或者出生年月日时了。"
        else:
            return "技术错误，请告诉用户稍后再试。"
            
    except Exception as e:
        tools_logger.error(f"八字查询工具出错: {e}")
        return "八字查询服务暂时不可用，请稍后再试。"


@tool
def yaoyigua() -> str:
    """只要用户想要摇卦占卜抽签的时候才会使用这个工具"""
    try:
        api_key = config.YUANFENJU_API_KEY
        url = config.YUANFENJU_ENDPOINTS["yaoyigua"]
        
        result = requests.post(url, data={'api_key': api_key})
        if result.status_code == 200:
            tools_logger.debug(f"摇卦返回数据: {result.json()}")
            data_json = result.json()
            return data_json.get("data", "摇卦失败")
        else:
            return "技术错误，请告诉用户稍后再试。"
            
    except Exception as e:
        tools_logger.error(f"摇卦工具出错: {e}")
        return "摇卦服务暂时不可用，请稍后再试。"


@tool
def jiemeng(query: str) -> str:
    """只有用户想要解梦的时候才会使用这个工具，需要输入用户梦境的内容，如果缺少用户梦境的内容则不可用。"""
    try:
        api_key = config.YUANFENJU_API_KEY
        url = config.YUANFENJU_ENDPOINTS["jiemeng"]
        
        # 创建关键词提取模型
        llm = config.get_model()

        # 直接使用统一管理的模板
        dream_prompt_template = SystemPrompts.DREAM_KEYWORD_EXTRACTION_PROMPT
        
        # 构建关键词提取链
        prompt = PromptTemplate.from_template(dream_prompt_template)
        chain = prompt | llm | StrOutputParser() | RunnableLambda(delete_think)
        
        # 提取关键词
        keyword = chain.invoke({"query": query})
        tools_logger.debug(f"提取的关键词: {keyword}")
        
        # 调用解梦 API
        result = requests.post(url, data={
            "api_key": api_key, 
            "title_zhougong": keyword
        })
        
        if result.status_code == 200:
            tools_logger.debug(f"解梦返回数据: {result.json()}")
            data_json = result.json()
            return data_json.get("data", "解梦失败")
        else:
            return "技术错误，请告诉用户稍后再试。"
            
    except Exception as e:
        tools_logger.error(f"解梦工具出错: {e}")
        return "解梦服务暂时不可用，请稍后再试。"




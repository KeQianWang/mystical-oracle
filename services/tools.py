"""
Mystical Oracle Tools - 神秘预言师工具集
使用配置管理和更好的错误处理
"""
import requests
from typing import Optional

from langchain.agents import tool
from langchain_community.utilities import SerpAPIWrapper
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_ollama import OllamaEmbeddings, ChatOllama, OllamaLLM
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from models.user import User
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
def get_info_from_local_db(query: str) -> str:
    """
    只有回答与2025年运势相关的问题的时候，会使用这个工具
    只有回答与生肖运势相关的问题的时候，会使用这个工具
    只有回答与星座(比如水瓶座,等等其他星座)相关的问题的时候，会使用这个工具
    """
    try:
        # 获取 Qdrant 配置
        qdrant_config = config.get_qdrant_config()
        embedding_config = config.get_embedding_config()
        
        # 连接本地 Qdrant 数据库
        qdrant_client = QdrantClient(path=qdrant_config["path"])
        vectorstore = QdrantVectorStore(
            client=qdrant_client,
            collection_name=qdrant_config["collection_name"],
            embedding=OllamaEmbeddings(**embedding_config)
        )
        
        # 检索相关文档
        retriever = vectorstore.as_retriever(search_type="mmr")
        docs = retriever.get_relevant_documents(query)
        
        # 格式化文档为字符串
        if docs:
            formatted_docs = "\n\n".join([
                f"来源: {doc.metadata.get('source', '未知')}\n内容: {doc.page_content}"
                for doc in docs
            ])
            return formatted_docs
        else:
            return "未找到相关信息"
            
    except Exception as e:
        tools_logger.error(f"本地知识库查询出错: {e}")
        return "知识库暂时不可用，请稍后再试。"


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
        model_config = config.get_model_config()
        model = ChatOllama(**model_config, format="json")
        
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
        model_config = config.get_model_config()
        llm = OllamaLLM(**model_config)
        
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




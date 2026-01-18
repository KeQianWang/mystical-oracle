"""
Mystical Oracle Agent - 神秘预言师核心模块
将配置、提示词模板分离，提高代码可维护性，并集成语音合成功能
"""
from typing import Optional, Dict, Any, AsyncGenerator, Generator

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableWithMessageHistory, RunnableConfig
from langchain_core.messages import SystemMessage

from services.redis_service import RedisService
from tools.tools import bazi_cesuan, search, yaoyigua, jiemeng, get_info_from_knowledge
from utils.helpers import delete_think
from config.settings import config
from prompts.system_prompts import SystemPrompts
from prompts.mood_prompts import MoodPrompts
from services.tts_service import tts_service
from config.logger import agent_logger


class Master:
    """算命大师 Agent 类 - 优化版本"""
    
    def __init__(self, session_id: Optional[str] = None, user_id: Optional[int] = None):
        """初始化算命大师"""
        # 基础配置
        self.session_id = session_id
        self.user_id = user_id
        self.memory_key = "chat_history"
        self.current_mood = MoodPrompts.get_default_mood()
        
        # 初始化聊天模型
        self.chat_model = config.get_model()
        
        # 缓存 Agent 组件，避免重复初始化
        self._agent_executor = None
        
        # 初始化 Agent 执行器
        self.agent_executor = self._init_agent_executor()
    
    def _init_agent_executor(self) -> RunnableWithMessageHistory:
        """初始化 Agent 执行器"""
        # 创建提示词模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", SystemPrompts.get_master_prompt(
                MoodPrompts.get_mood_role_set(self.current_mood)
            )),
            MessagesPlaceholder(self.memory_key),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # 工具列表
        tools = [search, get_info_from_knowledge, bazi_cesuan, yaoyigua, jiemeng]
        
        # 创建 Agent
        agent = create_openai_tools_agent(self.chat_model, tools, prompt, strict=True)
        
        # 创建 Agent 执行器
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True
        ) | RunnableLambda(lambda x: {**x, "output": delete_think(x["output"])})
        
        # 添加记忆功能
        return RunnableWithMessageHistory(
            agent_executor,
            self._get_memory,
            output_messages_key="output",
            history_messages_key=self.memory_key,
        )

    def run_stream(self, query: str) -> Generator[str, None, None]:
        """流式运行算命师对话 - 字符级输出"""
        try:
            # 情绪分析
            self._analyze_emotion(query)

            # 更新提示词（仅在情绪变化时）
            self._update_prompt_if_needed()

            # 配置会话
            config_obj = RunnableConfig(configurable={"session_id": self.session_id})

            # 执行流式对话 - 直接获取模型输出的token
            for chunk in self.agent_executor.stream({'input': query}, config=config_obj):
                # 处理不同类型的chunk
                if 'output' in chunk and chunk['output']:
                    # 直接yield每个token/字符
                    yield chunk['output']
                elif 'messages' in chunk:
                    # 处理消息类型的chunk
                    for msg in chunk['messages']:
                        if hasattr(msg, 'content') and msg.content:
                            yield msg.content

        except Exception as e:
            agent_logger.error(f"流式对话执行出错: {e}")
            yield "老夫此时无法为你算卦，请稍后再试。"

    async def run_stream_async(self, query: str) -> AsyncGenerator[str, None]:
        """异步流式运行算命师对话 - 字符级输出"""
        try:
            # 情绪分析
            self._analyze_emotion(query)

            # 更新提示词（仅在情绪变化时）
            self._update_prompt_if_needed()

            # 配置会话
            config_obj = RunnableConfig(configurable={"session_id": self.session_id})

            # 执行异步流式对话 - 直接获取模型输出的token
            async for chunk in self.agent_executor.astream({'input': query}, config=config_obj):
                # 处理不同类型的chunk
                if 'output' in chunk and chunk['output']:
                    # 直接yield每个token/字符
                    yield chunk['output']
                elif 'messages' in chunk:
                    # 处理消息类型的chunk
                    for msg in chunk['messages']:
                        if hasattr(msg, 'content') and msg.content:
                            yield msg.content

        except Exception as e:
            agent_logger.error(f"异步流式对话执行出错: {e}")
            yield "老夫此时无法为你算卦，请稍后再试。"

    def run(self, query: str) -> Dict[str, Any]:
        """运行算命师对话"""
        try:
            # 情绪分析
            self._analyze_emotion(query)
            
            # 更新提示词（仅在情绪变化时）
            self._update_prompt_if_needed()
            
            # 配置会话
            config_obj = RunnableConfig(configurable={"session_id": self.session_id})
            
            # 执行对话
            result = self.agent_executor.invoke({'input': query}, config=config_obj)
            
            # 保存聊天历史记录（如果提供了用户ID）
            if self.user_id:
                self._save_chat_history(query, result.get("output", ""))
            
            return result
            
        except Exception as e:
            agent_logger.error(f"对话执行出错: {e}")
            return {"output": "老夫此时无法为你算卦，请稍后再试。"}
    
    def _save_chat_history(self, user_message: str, assistant_message: str) -> None:
        """保存聊天历史记录到数据库"""
        try:
            from database.connection import get_db_context
            from services.chat_history_service import ChatHistoryService
            
            with get_db_context() as db:
                ChatHistoryService.add_chat_history(
                    db=db,
                    user_id=self.user_id,
                    session_id=self.session_id,
                    user_message=user_message,
                    assistant_message=assistant_message,
                    mood=self.current_mood,
                    message_type="text"
                )
            
            agent_logger.debug(f"聊天历史已保存: user_id={self.user_id}, session_id={self.session_id}")
            
        except Exception as e:
            agent_logger.error(f"保存聊天历史失败: {e}")
            # 不影响主要功能，只是记录错误
    
    def _analyze_emotion(self, query: str) -> str:
        """分析用户情绪"""
        try:
            emotion_prompt = SystemPrompts.get_emotion_prompt(query)
            chain = (
                ChatPromptTemplate.from_template(emotion_prompt) |
                self.chat_model |
                StrOutputParser() |
                RunnableLambda(delete_think)
            )
            
            result = chain.invoke({"query": query})
            emotion = result.strip()
            
            # 验证情绪有效性
            if MoodPrompts.is_valid_mood(emotion):
                old_mood = self.current_mood
                self.current_mood = emotion
                # 只在情绪变化时记录
                if old_mood != self.current_mood:
                    agent_logger.info(f"情绪变化: {old_mood} -> {self.current_mood}")
            else:
                self.current_mood = MoodPrompts.get_default_mood()
            
            return self.current_mood
            
        except Exception as e:
            agent_logger.error(f"情绪分析失败: {e}")
            self.current_mood = MoodPrompts.get_default_mood()
            return self.current_mood
    
    def _needs_prompt_update(self) -> bool:
        """检查是否需要更新提示词 - 基于情绪变化优化"""
        # 更精细的逻辑：只在情绪实际改变时更新
        if hasattr(self, '_last_mood'):
            return self._last_mood != self.current_mood
        return True

    def _update_prompt_if_needed(self) -> None:
        """根据情绪更新提示词（仅在需要时） - 优化版本"""
        if self._needs_prompt_update():
            self._last_mood = self.current_mood  # 记录当前情绪
            self._agent_executor = None  # 清空缓存
            self.agent_executor = self._init_agent_executor()
            agent_logger.debug(f"提示词已更新，当前情绪: {self.current_mood}")

    def _get_memory(self) -> RedisChatMessageHistory:
        """获取和管理聊天记录"""
        try:
            stored_messages = RedisService.get_chat_messages(self.session_id)

            # 如果历史消息过多，进行摘要
            if len(stored_messages) > config.MAX_HISTORY_MESSAGES:
                self._summarize_history(stored_messages)

            return RedisService.get_chat_history(self.session_id)

        except Exception as e:
            agent_logger.error(f"获取聊天记录失败: {e}")
            # 返回一个默认的历史记录
            return RedisService.get_chat_history(self.session_id)

    def _summarize_history(self, messages: list) -> None:
        """摘要历史对话"""
        try:
            summary_prompt = ChatPromptTemplate.from_messages([
                ("system", SystemPrompts.MASTER_SYSTEM_PROMPT + "\n" + 
                 SystemPrompts.CONVERSATION_SUMMARY_PROMPT),
                ("user", "{input}")
            ])
            
            chain = (
                summary_prompt |
                self.chat_model |
                StrOutputParser() |
                RunnableLambda(delete_think)
            )
            
            summary = chain.invoke({
                "input": messages,
                "who_are_you": MoodPrompts.get_mood_role_set(self.current_mood)
            })
            
            agent_logger.info(f'历史对话大于{config.MAX_HISTORY_MESSAGES}条，总结历史对话: {summary}')
            
            # 清空历史记录并添加摘要
            RedisService.clear_chat_history(self.session_id)
            if summary:
                RedisService.add_message(self.session_id,SystemMessage(content=str(summary)))
                
        except Exception as e:
            agent_logger.error(f"摘要历史对话失败: {e}")
    
    def set_session_id(self, session_id: str) -> None:
        """设置会话 ID"""
        self.session_id = session_id
    
    def get_current_mood(self) -> str:
        """获取当前情绪"""
        return self.current_mood
    
    def get_mood_description(self) -> str:
        """获取当前情绪描述"""
        return MoodPrompts.get_mood_description(self.current_mood)
    
    async def synthesize_speech_background(self, text: str, uid: str) -> None:
        """统一的语音合成后台任务，支持同步和异步调用"""
        if tts_service.is_available():
            await tts_service.synthesize_speech(text, uid, self.current_mood)
        else:
            agent_logger.warning("TTS 服务不可用，跳过语音合成")
    
    def get_voice_style(self) -> str:
        """获取当前情绪对应的语音风格"""
        return MoodPrompts.get_voice_style(self.current_mood)


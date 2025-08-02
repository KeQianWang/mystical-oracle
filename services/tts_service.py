"""
Mystical Oracle TTS Service - 文字转语音服务模块
使用微软 Azure TTS API 进行语音合成
"""
import asyncio
import requests
from typing import Optional
from pathlib import Path

from config.settings import config
from config.logger import tts_logger
from prompts.mood_prompts import MoodPrompts


class TTSService:
    """文字转语音服务类"""
    
    def __init__(self):
        self.api_key = config.MICROSOFT_TTS_KEY
        self.endpoint = config.TTS_ENDPOINT
        self.voice_name = config.TTS_VOICE_NAME
        self.output_format = config.TTS_OUTPUT_FORMAT
    
    def synthesize_speech_background(self, text: str, uid: str, mood: str = "default") -> None:
        """后台语音合成任务"""
        try:
            asyncio.run(self._synthesize_speech(text, uid, mood))
        except Exception as e:
            tts_logger.error(f"语音合成失败: {e}")
    
    async def _synthesize_speech(self, text: str, uid: str, mood: str = "default") -> Optional[str]:
        """异步语音合成"""
        try:
            tts_logger.info(f"开始语音合成: {text[:50]}...")
            tts_logger.debug(f"用户ID: {uid}, 情绪: {mood}")
            
            # 获取语音风格
            voice_style = MoodPrompts.get_voice_style(mood)
            
            # 构建请求头
            headers = {
                "Ocp-Apim-Subscription-Key": self.api_key,
                "Content-Type": "application/ssml+xml",
                "X-Microsoft-OutputFormat": self.output_format,
                "User-Agent": "King's Fortune Teller Bot"
            }
            
            # 构造 SSML 请求体
            ssml = self._build_ssml(text, voice_style)
            
            # 发送请求
            response = requests.post(
                self.endpoint,
                headers=headers,
                data=ssml.encode("utf-8"),
                timeout=30
            )
            
            if response.status_code == 200:
                # 保存音频文件
                audio_path = f"{uid}.mp3"
                with open(audio_path, "wb") as f:
                    f.write(response.content)
                
                tts_logger.info(f"语音合成成功，音频已保存为: {audio_path}")
                return audio_path
            else:
                tts_logger.error(f"TTS API 请求失败: {response.status_code}")
                tts_logger.error(f"错误信息: {response.text}")
                return None
                
        except Exception as e:
            tts_logger.error(f"语音合成过程中出现错误: {e}")
            return None
    
    def _build_ssml(self, text: str, voice_style: str) -> str:
        """构建 SSML 格式的语音合成请求体"""
        return f"""<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang='zh-CN'>
            <voice name='{self.voice_name}'>
                <mstts:express-as style="{voice_style}" role="SeniorMale">{text}</mstts:express-as>
            </voice>
        </speak>"""
    
    def is_available(self) -> bool:
        """检查 TTS 服务是否可用"""
        return bool(self.api_key)
    
    def get_audio_file_path(self, uid: str) -> Path:
        """获取音频文件路径"""
        return Path(f"{uid}.mp3")


# 全局 TTS 服务实例
tts_service = TTSService()
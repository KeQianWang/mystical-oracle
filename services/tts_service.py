"""
Mystical Oracle TTS Service - 文字转语音服务模块
使用 edge-tts 进行语音合成
"""
import re
import tempfile
from typing import Optional
from pathlib import Path

import edge_tts
from edge_tts import exceptions as edge_tts_exceptions

from config.settings import config
from config.logger import tts_logger


class TTSService:
    """文字转语音服务类"""
    
    def __init__(self):
        self.voice_name = config.EDGE_TTS_VOICE or "zh-CN-XiaoxiaoNeural"
        self.rate = self._normalize_rate(config.EDGE_TTS_RATE)
        self.volume = self._normalize_volume(config.EDGE_TTS_VOLUME)
        self.pitch = self._normalize_pitch(config.EDGE_TTS_PITCH)
        self.proxy = config.EDGE_TTS_PROXY
        self.max_chars = config.EDGE_TTS_MAX_CHARS or 2000
        self.timeout = config.EDGE_TTS_TIMEOUT or 60
        if self.max_chars <= 0:
            self.max_chars = 2000
        if self.timeout <= 0:
            self.timeout = 60
        
        # 确保音频目录存在
        self.audio_dir = Path(config.AUDIO_OUTPUT_DIR or "./audio")
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    async def synthesize_speech(self, text: str, uid: str, mood: str = "default") -> Optional[str]:
        """异步语音合成"""
        try:
            text = (text or "").strip()
            if not text:
                tts_logger.warning("语音合成文本为空，跳过生成")
                return None

            tts_logger.info(f"开始语音合成: {text[:50]}...")
            tts_logger.debug(f"用户ID: {uid}, 情绪: {mood}")

            if not self.is_available():
                tts_logger.error("edge-tts 模块不可用，无法执行语音合成")
                return None

            audio_path = self.audio_dir / f"{uid}.mp3"
            chunks = self._split_text(text)
            if len(chunks) == 1:
                if not await self._run_tts(chunks[0], audio_path):
                    return None
            else:
                with tempfile.TemporaryDirectory(dir=self.audio_dir) as temp_dir:
                    part_paths = []
                    for index, chunk in enumerate(chunks, start=1):
                        part_path = Path(temp_dir) / f"{uid}.part{index}.mp3"
                        if not await self._run_tts(chunk, part_path):
                            return None
                        part_paths.append(part_path)
                    if not self._concat_audio(part_paths, audio_path):
                        return None

            tts_logger.info(f"语音合成成功，音频已保存为: {audio_path}")
            return str(audio_path)
                
        except Exception as e:
            tts_logger.error(f"语音合成过程中出现错误: {e}")
            return None
    
    async def _run_tts(self, text: str, audio_path: Path) -> bool:
        """执行 edge-tts 命令并返回是否成功"""
        voice = self.voice_name or "zh-CN-XiaoxiaoNeural"
        if await self._run_tts_with_voice(text, audio_path, voice):
            return True
        if voice != "zh-CN-XiaoxiaoNeural":
            tts_logger.warning("使用指定音色失败，回退到默认音色 zh-CN-XiaoxiaoNeural")
            return await self._run_tts_with_voice(text, audio_path, "zh-CN-XiaoxiaoNeural")
        return False

    async def _run_tts_with_voice(self, text: str, audio_path: Path, voice: str) -> bool:
        """使用指定音色执行 edge-tts"""
        try:
            communicate = edge_tts.Communicate(
                text,
                voice,
                rate=self.rate,
                volume=self.volume,
                pitch=self.pitch,
                proxy=self.proxy,
                connect_timeout=10,
                receive_timeout=self.timeout,
            )
            await communicate.save(str(audio_path))
        except edge_tts_exceptions.NoAudioReceived as e:
            tts_logger.error(f"edge-tts 未收到音频: {e}")
            return False
        except Exception as e:
            tts_logger.error(f"edge-tts 执行失败: {e}")
            return False

        if not audio_path.exists():
            tts_logger.error("edge-tts 执行完成但未生成音频文件")
            return False

        return True

    def _split_text(self, text: str) -> list:
        """按标点与长度切分文本，避免过长导致 TTS 无响应"""
        if len(text) <= self.max_chars:
            return [text]

        segments = re.split(r"(?<=[。！？!?；;])", text)
        chunks = []
        buffer = ""
        for segment in segments:
            if not segment:
                continue
            if len(buffer) + len(segment) <= self.max_chars:
                buffer += segment
                continue
            if buffer:
                chunks.append(buffer)
                buffer = ""
            if len(segment) <= self.max_chars:
                buffer = segment
            else:
                for idx in range(0, len(segment), self.max_chars):
                    chunks.append(segment[idx : idx + self.max_chars])
        if buffer:
            chunks.append(buffer)
        return chunks

    def _concat_audio(self, part_paths: list, output_path: Path) -> bool:
        """拼接多个音频片段（mp3 二进制拼接）"""
        try:
            if output_path.exists():
                output_path.unlink()
            with open(output_path, "wb") as output_file:
                for part_path in part_paths:
                    with open(part_path, "rb") as part_file:
                        output_file.write(part_file.read())
            return True
        except Exception as e:
            tts_logger.error(f"拼接音频失败: {e}")
            return False

    def _normalize_rate(self, value: Optional[str]) -> str:
        return self._normalize_param(value, r"^[+-]\d+%$", "+0%", "rate")

    def _normalize_volume(self, value: Optional[str]) -> str:
        return self._normalize_param(value, r"^[+-]\d+%$", "+0%", "volume")

    def _normalize_pitch(self, value: Optional[str]) -> str:
        return self._normalize_param(value, r"^[+-]\d+Hz$", "+0Hz", "pitch")

    def _normalize_param(self, value: Optional[str], pattern: str, default: str, name: str) -> str:
        if not value:
            return default
        if re.match(pattern, value):
            return value
        tts_logger.warning(f"edge-tts 参数 {name} 非法，已回退到默认值 {default}")
        return default
    
    def is_available(self) -> bool:
        """检查 TTS 服务是否可用"""
        return True
    
    def get_audio_file_path(self, uid: str) -> Path:
        """获取音频文件路径"""
        return self.audio_dir / f"{uid}.mp3"


# 全局 TTS 服务实例
tts_service = TTSService()

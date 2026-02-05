"""
Mystical Oracle TTS Service - 文字转语音服务模块
"""
import asyncio
import base64
import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import requests
from tenacity import retry, wait_exponential, stop_after_attempt

from config.settings import config
from config.logger import tts_logger
from prompts.mood_prompts import MoodPrompts


class TTSService:
    """文字转语音服务类"""

    ENDPOINT_URL = "https://dev.microsofttranslator.com/apps/endpoint?api-version=1.0"
    VOICES_LIST_URL = "https://eastus.api.speech.microsoft.com/cognitiveservices/voices/list"
    USER_AGENT = "okhttp/4.5.0"
    CLIENT_VERSION = "4.0.530a 5fe1dc6c"
    USER_ID = "0f04d16a175c411e"
    HOME_GEOGRAPHIC_REGION = "zh-Hans-CN"
    CLIENT_TRACE_ID = "aab069b9-70a7-4844-a734-96cd78d94be9"
    VOICE_DECODE_KEY = (
        "oik6PdDdMnOXemTbwvMn9de/h9lFnfBaCWbGMMZqqoSaQaqUOqjVGm5NqsmjcBI1x+sS9ugjB55HEJWRiFXYFw=="
    )
    DEFAULT_VOICE_NAME = "zh-CN-YunzeNeural"
    DEFAULT_RATE = "0"
    DEFAULT_PITCH = "0"
    DEFAULT_OUTPUT_FORMAT = "audio-24khz-48kbitrate-mono-mp3"
    DEFAULT_STYLE = "general"
    REQUEST_TIMEOUT = 30
    ENDPOINT_REFRESH_SAFETY = 60
    VOICE_LIST_CACHE_TTL = 3600
    
    def __init__(self):
        # Endpoint 缓存
        self._endpoint: Optional[dict] = None
        self._expired_at: Optional[int] = None
        self._voice_list_cache: Optional[list] = None
        self._voice_list_expires_at: Optional[int] = None
        self._audio_dir: Optional[Path] = None

    async def synthesize_speech(self, text: str, uid: str, mood: str = "default") -> Optional[str]:
        """异步语音合成"""
        try:
            tts_logger.info(f"开始语音合成: {text[:50]}...")
            tts_logger.debug(f"用户ID: {uid}, 情绪: {mood}")
            
            # 获取语音风格
            voice_style = MoodPrompts.get_voice_style(mood) or self.DEFAULT_STYLE

            audio_bytes = await asyncio.to_thread(
                self.get_voice,
                text,
                style=voice_style,
            )

            # 保存音频文件到统一目录
            audio_path = self._write_audio_file(uid, audio_bytes)
            
            tts_logger.info(f"语音合成成功，音频已保存为: {audio_path}")
            return str(audio_path)
                
        except Exception as e:
            tts_logger.exception(f"语音合成过程中出现错误: {e}")
            return None

    def _get_endpoint(self) -> dict:
        signature = self._sign(self.ENDPOINT_URL)
        headers = {
            "Accept-Language": "zh-Hans",
            "X-ClientVersion": self.CLIENT_VERSION,
            "X-UserId": self.USER_ID,
            "X-HomeGeographicRegion": self.HOME_GEOGRAPHIC_REGION,
            "X-ClientTraceId": self.CLIENT_TRACE_ID,
            "X-MT-Signature": signature,
            "User-Agent": self.USER_AGENT,
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": "0",
            "Accept-Encoding": "gzip",
        }

        response = requests.post(self.ENDPOINT_URL, headers=headers, timeout=self.REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def _ensure_endpoint(self) -> dict:
        current_time = int(time.time())
        if self._endpoint and self._expired_at and current_time <= self._expired_at - self.ENDPOINT_REFRESH_SAFETY:
            return self._endpoint

        self._endpoint = self._get_endpoint()
        try:
            payload = self._decode_jwt_payload(self._endpoint.get("t", ""))
            self._expired_at = int(payload.get("exp", 0)) or None
        except Exception as e:
            tts_logger.warning(f"解析 TTS token 过期时间失败: {e}")
            self._expired_at = None
        return self._endpoint

    def _sign(self, url_str: str) -> str:
        url_body = url_str.split("://")[1]
        encoded_url = quote(url_body, safe="")
        uuid_str = str(uuid.uuid4()).replace("-", "")
        formatted_date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S").lower() + "gmt"
        bytes_to_sign = (
            f"MSTranslatorAndroidApp{encoded_url}{formatted_date}{uuid_str}".lower().encode("utf-8")
        )

        decode = base64.b64decode(self.VOICE_DECODE_KEY)
        hmac_sha256 = hmac.new(decode, bytes_to_sign, hashlib.sha256)
        secret_key = hmac_sha256.digest()
        sign_base64 = base64.b64encode(secret_key).decode()

        return f"MSTranslatorAndroidApp::{sign_base64}::{formatted_date}::{uuid_str}"

    @staticmethod
    def _decode_jwt_payload(token: str) -> dict:
        if not token or "." not in token:
            raise ValueError("无效的 JWT token")
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        decoded = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
        return json.loads(decoded.decode("utf-8"))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=5))
    def get_voice(
        self,
        text: str,
        voice_name: str = "",
        rate: str = "",
        pitch: str = "",
        output_format: str = "",
        style: str = "",
    ) -> bytes:
        endpoint = self._ensure_endpoint()

        voice_name = voice_name or self.DEFAULT_VOICE_NAME
        rate = rate or self.DEFAULT_RATE
        pitch = pitch or self.DEFAULT_PITCH
        output_format = output_format or self.DEFAULT_OUTPUT_FORMAT
        style = style or self.DEFAULT_STYLE

        url = f"https://{endpoint['r']}.tts.speech.microsoft.com/cognitiveservices/v1"
        headers = {
            "Authorization": endpoint["t"],
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": output_format,
        }

        ssml = self._get_ssml(text, voice_name, rate, pitch, style)
        response = requests.post(url, headers=headers, data=ssml.encode("utf-8"), timeout=self.REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.content

    def _get_ssml(self, text: str, voice_name: str, rate: str, pitch: str, style: str) -> str:
        return f"""
                <speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" version="1.0" xml:lang="zh-CN">
                <voice name="{voice_name}">
                    <mstts:express-as style="{style}" styledegree="1.0" role="default">
                        <prosody rate="{rate}%" pitch="{pitch}%">
                            {text}
                        </prosody>
                    </mstts:express-as>
                </voice>
                </speak>
                """

    def get_voice_list(self) -> Optional[list]:
        """获取可用的语音列表"""
        current_time = int(time.time())
        if (
            self._voice_list_cache is not None
            and self._voice_list_expires_at is not None
            and current_time <= self._voice_list_expires_at
        ):
            return self._voice_list_cache

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.26"
            ),
            "X-Ms-Useragent": "SpeechStudio/2021.05.001",
            "Content-Type": "application/json",
            "Origin": "https://azure.microsoft.com",
            "Referer": "https://azure.microsoft.com",
        }

        try:
            response = requests.get(self.VOICES_LIST_URL, headers=headers, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            self._voice_list_cache = response.json()
            self._voice_list_expires_at = current_time + self.VOICE_LIST_CACHE_TTL
            return self._voice_list_cache
        except requests.exceptions.RequestException as e:
            tts_logger.error(f"获取语音列表失败: {e}")
            if self._voice_list_cache is not None:
                tts_logger.warning("语音列表拉取失败，返回缓存的旧数据")
                return self._voice_list_cache
            return None

    
    def _ensure_audio_dir(self) -> Path:
        if self._audio_dir is None:
            audio_dir = Path(config.AUDIO_OUTPUT_DIR or "audio")
            audio_dir.mkdir(parents=True, exist_ok=True)
            self._audio_dir = audio_dir
        return self._audio_dir

    def _ensure_user_audio_dir(self, uid: str) -> Path:
        audio_dir = self._ensure_audio_dir()
        user_dir = audio_dir / uid
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    def _build_timestamp_key(self) -> str:
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        nanos = time.time_ns() % 1_000_000_000
        return f"{timestamp}-{nanos:09d}"

    def _build_audio_filename(self, output_extension: str) -> str:
        return f"{self._build_timestamp_key()}.{output_extension}"

    def _write_audio_file(self, uid: str, audio_bytes: bytes) -> Path:
        user_dir = self._ensure_user_audio_dir(uid)
        output_extension = self._infer_extension(self.DEFAULT_OUTPUT_FORMAT)
        for _ in range(5):
            audio_path = user_dir / self._build_audio_filename(output_extension)
            try:
                with open(audio_path, "xb") as f:
                    f.write(audio_bytes)
                return audio_path
            except FileExistsError:
                continue
        fallback_name = f"{self._build_timestamp_key()}-{uuid.uuid4().hex}.{output_extension}"
        audio_path = user_dir / fallback_name
        with open(audio_path, "xb") as f:
            f.write(audio_bytes)
        return audio_path

    def get_audio_file_path(self, uid: str) -> Path:
        """获取音频文件路径"""
        user_dir = self._ensure_user_audio_dir(uid)
        output_extension = self._infer_extension(self.DEFAULT_OUTPUT_FORMAT)
        return user_dir / self._build_audio_filename(output_extension)

    @staticmethod
    def _infer_extension(output_format: str) -> str:
        if not output_format:
            return "mp3"
        fmt = output_format.lower()
        if "mp3" in fmt:
            return "mp3"
        if "ogg" in fmt:
            return "ogg"
        if "wav" in fmt or "riff" in fmt or "pcm" in fmt:
            return "wav"
        return "audio"


# 全局 TTS 服务实例
tts_service = TTSService()

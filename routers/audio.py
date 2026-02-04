"""
音频接口路由器
包含语音合成文件相关接口
"""
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from utils.helpers import format_error_message
from config.logger import server_logger
from config.settings import config

router = APIRouter(prefix="/audio", tags=["音频接口"])


@router.get("/{audio_id}")
def get_audio(audio_id: str):
    """获取生成的音频文件"""
    try:
        audio_dir = Path(config.AUDIO_OUTPUT_DIR or "./audio")
        audio_path = audio_dir / f"{audio_id}.mp3"

        if not audio_path.exists():
            raise HTTPException(status_code=404, detail="音频文件不存在")
        
        return FileResponse(
            path=audio_path,
            media_type="audio/mpeg",
            filename=f"{audio_id}.mp3"
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="音频文件不存在")
    except Exception as e:
        error_msg = format_error_message(e, f"获取音频文件: {audio_id}")
        server_logger.error(error_msg)
        raise HTTPException(status_code=500, detail="获取音频文件失败")

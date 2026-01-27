"""
头像处理工具
"""
import base64
import binascii
from io import BytesIO
from typing import Optional, Tuple

from PIL import Image, ImageOps


def _split_data_url(data_url: str) -> Tuple[Optional[str], str]:
    if not data_url.startswith("data:"):
        return None, data_url
    parts = data_url.split(",", 1)
    if len(parts) != 2:
        return None, data_url
    return parts[0], parts[1]


def compress_avatar_base64(avatar_base64: Optional[str]) -> Optional[str]:
    """
    压缩头像 base64，返回与输入一致的格式（data URL 或纯 base64）
    """
    if not avatar_base64:
        return avatar_base64

    if avatar_base64.startswith("http://") or avatar_base64.startswith("https://"):
        return avatar_base64

    header, data_part = _split_data_url(avatar_base64)
    try:
        image_bytes = base64.b64decode(data_part)
    except (binascii.Error, ValueError):
        return avatar_base64

    try:
        image = Image.open(BytesIO(image_bytes))
    except Exception:
        return avatar_base64

    image = ImageOps.exif_transpose(image)
    max_size = (256, 256)
    image.thumbnail(max_size)

    output = BytesIO()
    format_hint = (header or "").lower()
    if "image/png" in format_hint or image.mode in ("RGBA", "LA"):
        image.save(output, format="PNG", optimize=True, compress_level=9)
        mime = "image/png"
    else:
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        image.save(output, format="JPEG", optimize=True, quality=75)
        mime = "image/jpeg"

    new_base64 = base64.b64encode(output.getvalue()).decode("ascii")
    if header is not None:
        return f"data:{mime};base64,{new_base64}"
    return new_base64

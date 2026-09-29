import os
from maxapi import Bot
from maxapi.types.attachments.upload import AttachmentUpload
from maxapi.types.input_media import InputMedia

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
WELCOME_IMAGE = os.path.join(ASSETS_DIR, "welcome.png")
STREAK_IMAGE = os.path.join(ASSETS_DIR, "streak.png")

# загружаем картинку и кешим
_cache: dict[str, AttachmentUpload] = {}

async def get_image(bot: Bot, path: str) -> AttachmentUpload | None:
    if path in _cache:
        return _cache[path]
    try:
        att = await bot.upload_media(InputMedia(path))
    except Exception:
        return None
    _cache[path] = att
    return att

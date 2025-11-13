import logging
from aiogram import types
from utils.vk_client import post_to_vk, upload_photo_to_vk, upload_video_to_vk
from db.database import get_user_tokens
from utils.crypto import decrypt

logger = logging.getLogger(__name__)

# ИСПРАВЛЕНО: имя функции + параметр bot
async def repost_channel_post(message: types.Message, bot):
    logger.info(f"[REPOST] Получено сообщение из канала: {message.chat.id}")

    user_data = get_user_tokens(channel_id=message.chat.id)
    if not user_data:
        logger.warning(f"[REPOST] Нет токенов для канала {message.chat.id}")
        return

    try:
        vk_token = decrypt(user_data["vk_token"])
    except Exception as e:
        logger.error(f"[REPOST] Ошибка расшифровки токена: {e}")
        return

    group_id = user_data["group_id"]
    logger.info(f"[GROUP] VK Group ID: {group_id}")

    # === ТЕКСТ ===
    text = (message.text or message.caption or "").strip()
    if len(text) > 4096:
        text = text[:4093] + "..."
        logger.info("[TEXT] Обрезан до 4096 символов")

    attachments = []

    # === ФОТО ===
    if message.photo:
        try:
            photo = message.photo[-1]
            file = await bot.get_file(photo.file_id)
            file_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
            logger.info(f"[PHOTO] Загружаем: {file_url}")

            photo_id = upload_photo_to_vk(vk_token, group_id, file_url)
            if photo_id:
                attachments.append(photo_id)
                logger.info(f"[PHOTO] Успешно: {photo_id}")
            else:
                logger.warning("[PHOTO] Не удалось загрузить")
        except Exception as e:
            logger.error(f"[PHOTO] Ошибка: {e}")

    # === ВИДЕО ===
    if message.video:
        try:
            video = message.video
            file = await bot.get_file(video.file_id)
            file_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
            logger.info(f"[VIDEO] Загружаем: {file_url}")

            video_id = upload_video_to_vk(vk_token, group_id, file_url)
            if video_id:
                attachments.append(video_id)
                logger.info(f"[VIDEO] Успешно: {video_id}")
            else:
                logger.warning("[VIDEO] Не удалось загрузить")
        except Exception as e:
            logger.error(f"[VIDEO] Ошибка: {e}")

    # === ПУБЛИКАЦИЯ ===
    logger.info(f"[VK] Публикуем: {len(text)} символов, вложений: {len(attachments)}")

    try:
        response = post_to_vk(vk_token, group_id, text, attachments)
        if "error" in response:
            logger.error(f"[VK] Ошибка: {response['error']}")
        else:
            post_id = response.get("response", {}).get("post_id")
            logger.info(f"[VK] Успешно! post_id = {post_id}")
    except Exception as e:
        logger.error(f"[VK] Критическая ошибка: {e}") 
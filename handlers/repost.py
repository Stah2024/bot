import logging
from aiogram import types
from utils.vk_client import post_to_vk, upload_photo_to_vk, upload_video_to_vk
from db.database import get_user_tokens_by_channel

logger = logging.getLogger(__name__)

async def repost_channel_post(message: types.Message, bot):
    logger.info(f"[REPOST] Получено сообщение из канала: {message.chat.id}")

    user_data = get_user_tokens_by_channel(channel_id=message.chat.id)
    if not user_data:
        logger.warning(f"[REPOST] Нет токенов для канала {message.chat.id}")
        return

    vk_token = user_data["vk_token"]
    group_id = user_data["vk_group_id"]
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
            file_path = file.file_path
            file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"
            logger.info(f"[PHOTO] Загружаем: {file_url}")

            photo_id = upload_photo_to_vk(vk_token, group_id, file_url)
            if photo_id:
                attachments.append(photo_id)
                logger.info(f"[PHOTO] Успешно: {photo_id}")
            else:
                logger.warning("[PHOTO] Не удалось загрузить")
        except Exception as e:
            logger.exception(f"[PHOTO] Ошибка загрузки: {e}")

    # === ВИДЕО ===
    if message.video:
        try:
            video = message.video
            file = await bot.get_file(video.file_id)
            file_path = file.file_path
            file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"
            logger.info(f"[VIDEO] Загружаем: {file_url}")

            # ВАЖНО: видео загружается без wallpost=1, чтобы избежать автопоста
            video_id = upload_video_to_vk(vk_token, group_id, file_url)
            if video_id:
                attachments.append(video_id)
                logger.info(f"[VIDEO] Успешно: {video_id}")
            else:
                logger.warning("[VIDEO] Не удалось загрузить")
        except Exception as e:
            logger.exception(f"[VIDEO] Ошибка загрузки: {e}")

    # === ПУБЛИКАЦИЯ ===
    if not text and not attachments:
        logger.warning("[VK] Нет контента для публикации (ни текста, ни вложений)")
        return

    logger.info(f"[VK] Публикуем: {len(text)} символов, вложений: {len(attachments)}")

    try:
        response = post_to_vk(vk_token, group_id, text, attachments)
        if "error" in response:
            logger.error(f"[VK] Ошибка публикации: {response['error']}")
        else:
            post_id = response.get("response", {}).get("post_id")
            logger.info(f"[VK] Успешно опубликовано! post_id = {post_id}")
    except Exception as e:
        logger.exception(f"[VK] Критическая ошибка при публикации: {e}")
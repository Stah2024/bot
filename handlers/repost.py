# handlers/repost.py
import logging
from aiogram import types
from utils.vk_client import post_to_vk, upload_photo_to_vk, upload_video_to_vk
from db.database import get_subscriptions_by_channel

logger = logging.getLogger(__name__)


async def repost_channel_post(message: types.Message, bot):
    logger.info(f"[REPOST] Получено сообщение из канала: {message.chat.id}")

    subscriptions = get_subscriptions_by_channel(message.chat.id)
    if not subscriptions:
        logger.warning(f"[REPOST] Нет активных подписок для канала {message.chat.id}")
        return

    # Текст (общий)
    text = (message.text or message.caption or "").strip()
    if len(text) > 4096:
        text = text[:4093] + "..."

    # === Публикация в каждую группу отдельно (так надёжнее и правильно) ===
    for sub in subscriptions:
        vk_token = sub["vk_token"]
        group_id = str(sub["vk_group_id"])  # ВК требует строку
        group_name = sub.get("vk_group_name", "Группа ВК")

        logger.info(f"[VK] Публикация в {group_id} ({group_name})")

        attachments = []

        # Фото — загружаем отдельно для этой группы
        if message.photo:
            try:
                file = await bot.get_file(message.photo[-1].file_id)
                file_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
                photo_id = upload_photo_to_vk(vk_token, group_id, file_url)
                if photo_id:
                    attachments.append(photo_id)
                    logger.info(f"[PHOTO] Успешно в {group_id}: {photo_id}")
            except Exception as e:
                logger.exception(f"[PHOTO] Ошибка в {group_id}: {e}")

        # Видео — аналогично
        if message.video:
            try:
                file = await bot.get_file(message.video.file_id)
                file_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
                video_id = upload_video_to_vk(vk_token, group_id, file_url)
                if video_id:
                    attachments.append(video_id)
                    logger.info(f"[VIDEO] Успешно в {group_id}: {video_id}")
            except Exception as e:
                logger.exception(f"[VIDEO] Ошибка в {group_id}: {e}")

        # Если нет ни текста, ни вложений — пропускаем
        if not text and not attachments:
            logger.warning(f"[VK] Нет контента для публикации в {group_id}")
            continue

        # ПУБЛИКУЕМ
        try:
            response = post_to_vk(vk_token, group_id, text or "", attachments)
            if "error" in response:
                logger.error(f"[VK] Ошибка в {group_id}: {response['error']}")
            else:
                post_id = response.get("response", {}).get("post_id")
                logger.info(f"[VK] Успешно опубликовано в {group_id}: post_id={post_id}")
        except Exception as e:
            logger.exception(f"[VK] Критическая ошибка при публикации в {group_id}: {e}")
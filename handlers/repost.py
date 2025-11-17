import logging
from aiogram import types
from utils.vk_client import post_to_vk, upload_photo_to_vk, upload_video_to_vk
from db.database import get_subscriptions_by_channel   # ← изменил импорт

logger = logging.getLogger(__name__)


async def repost_channel_post(message: types.Message, bot):
    logger.info(f"[REPOST] Получено сообщение из канала: {message.chat.id}")

    # Теперь возвращается список (может быть 0, 1 или много подписок)
    subscriptions = get_subscriptions_by_channel(message.chat.id)

    if not subscriptions:
        logger.warning(f"[REPOST] Нет активных подписок для канала {message.chat.id}")
        return

    # === ТЕКСТ (общий для всех групп) ===
    text = (message.text or message.caption or "").strip()
    if len(text) > 4096:
        text = text[:4093] + "..."
        logger.info("[TEXT] Текст обрезан до 4096 символов")

    # Один раз скачиваем вложения (чтобы не делать это для каждой группы заново)
    attachments = []

    # === ФОТО (один раз) ===
    if message.photo:
        try:
            photo = message.photo[-1]
            file = await bot.get_file(photo.file_id)
            file_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
            logger.info(f"[PHOTO] Скачиваем фото: {file_url}")

            # Загружаем фото ОДИН раз — получаем список owner_id + media_id для всех групп
            photo_ids = []
            for sub in subscriptions:
                photo_id = upload_photo_to_vk(sub["vk_token"], sub["vk_group_id"], file_url)
                if photo_id:
                    photo_ids.append(photo_id)
                else:
                    photo_ids.append(None)

            # Добавляем только успешные
            for i, photo_id in enumerate(photo_ids):
                if photo_id:
                    attachments.append(photo_id)
                    logger.info(f"[PHOTO] Успешно для группы {subscriptions[i]['vk_group_id']}: {photo_id}")
        except Exception as e:
            logger.exception(f"[PHOTO] Ошибка загрузки: {e}")

    # === ВИДЕО (один раз) ===
    if message.video:
        try:
            file = await bot.get_file(message.video.file_id)
            file_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
            logger.info(f"[VIDEO] Скачиваем видео: {file_url}")

            video_ids = []
            for sub in subscriptions:
                video_id = upload_video_to_vk(sub["vk_token"], sub["vk_group_id"], file_url)
                if video_id:
                    video_ids.append(video_id)
                else:
                    video_ids.append(None)

            for i, video_id in enumerate(video_ids):
                if video_id:
                    attachments.append(video_id)
                    logger.info(f"[VIDEO] Успешно для группы {subscriptions[i]['vk_group_id']}: {video_id}")
        except Exception as e:
            logger.exception(f"[VIDEO] Ошибка загрузки видео: {e}")

    # === ПУБЛИКАЦИЯ В КАЖДУЮ ГРУППУ ===
    for idx, sub in enumerate(subscriptions):
        vk_token = sub["vk_token"]
        group_id = sub["vk_group_id"]
        group_name = sub.get("vk_group_name", "Группа ВК")

        logger.info(f"[VK] Публикуем в группу {group_id} ({group_name})")

        # Берём только те вложения, которые успешно загрузились для этой группы
        current_attachments = []
        if message.photo and len(photo_ids) > idx and photo_ids[idx]:
            current_attachments.append(photo_ids[idx])
        if message.video and len(video_ids) > idx and video_ids[idx]:
            current_attachments.append(video_ids[idx])

        if not text and not current_attachments:
            logger.warning(f"[VK] Нет контента для группы {group_id}")
            continue

        try:
            response = post_to_vk(vk_token, group_id, text, current_attachments)
            if "error" in response:
                logger.error(f"[VK] Ошибка в {group_id}: {response['error']}")
            else:
                post_id = response.get("response", {}).get("post_id")
                logger.info(f"[VK] Успешно в {group_id}: post_id = {post_id}")
        except Exception as e:
            logger.exception(f"[VK] Критическая ошибка в группе {group_id}: {e}")
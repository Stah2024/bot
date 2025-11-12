from aiogram import types, Bot
from config import BOT_TOKEN
from db.database import get_user_tokens_by_channel
from utils.vk_client import post_to_vk, upload_photo_to_vk, upload_video_to_vk
import logging

bot = Bot(token=BOT_TOKEN)
logging.basicConfig(level=logging.INFO)

async def repost_channel_post(message: types.Message):
    print("[REPOST] Получено сообщение из канала:", message.chat.id)

    user = get_user_tokens_by_channel(message.chat.id)
    if not user:
        print("[REPOST] Нет токенов для chat.id =", message.chat.id)
        return

    vk_token = user["vk_token"]
    group_id = int(user["vk_group_id"])  # ← УБЕДИСЬ, что в БД хранится с минусом!
    print("[TOKENS] VK:", vk_token)
    print("[GROUP] VK Group ID:", group_id)

    # Текст: берём полный, но обрезаем до 4096 (лимит VK)
    text = (message.text or message.caption or "").strip()
    if len(text) > 4096:
        text = text[:4093] + "..."
        print("[TEXT] Обрезан до 4096 символов")

    attachments = []

    # === ФОТО ===
    if message.photo:
        try:
            file = await bot.get_file(message.photo[-1].file_id)
            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
            print("[PHOTO] Загружаем фото:", file_url)

            photo_id = upload_photo_to_vk(vk_token, group_id, file_url)
            if photo_id:
                print("[PHOTO] Успешно загружено:", photo_id)
                attachments.append(photo_id)
            else:
                print("[PHOTO] Ошибка загрузки — пропускаем")
        except Exception as e:
            logging.error(f"[PHOTO] Критическая ошибка: {e}")

    # === ВИДЕО ===
    if message.video:
        try:
            file = await bot.get_file(message.video.file_id)
            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
            print("[VIDEO] Загружаем видео:", file_url)

            video_id = upload_video_to_vk(vk_token, group_id, file_url)
            if video_id:
                print("[VIDEO] Успешно загружено:", video_id)
                attachments.append(video_id)
            else:
                print("[VIDEO] Ошибка загрузки — пропускаем")
        except Exception as e:
            logging.error(f"[VIDEO] Критическая ошибка: {e}")

    # === ДОКУМЕНТЫ (если нужно — добавь позже) ===
    # elif message.document: ...

    print("[VK] Публикуем пост:", text)
    print("[VK] Вложения:", attachments)

    # Публикуем
    try:
        response = post_to_vk(vk_token, group_id, text, attachments)
        print("[VK] Ответ от API:", response)
    except Exception as e:
        logging.error(f"[VK] Ошибка публикации: {e}")
        print("[VK] Пост НЕ опубликован")
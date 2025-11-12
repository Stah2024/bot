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

    # Standalone-токен — уже расшифрован в БД
    vk_token = user["vk_token"]
    # group_id хранится как строка с минусом: "-12345678"
    group_id = user["vk_group_id"]  # ← ОСТАВЛЯЕМ СТРОКОЙ С МИНУСОМ!
    print("[TOKENS] VK:", vk_token)
    print("[GROUP] VK Group ID:", group_id)

    # Текст
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
                print("[PHOTO] Успешно:", photo_id)
                attachments.append(photo_id)
            else:
                print("[PHOTO] Ошибка — пропускаем")
        except Exception as e:
            logging.error(f"[PHOTO] Ошибка: {e}")

    # === ВИДЕО ===
    if message.video:
        try:
            file = await bot.get_file(message.video.file_id)
            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
            print("[VIDEO] Загружаем видео:", file_url)

            video_id = upload_video_to_vk(vk_token, group_id, file_url)
            if video_id:
                print("[VIDEO] Успешно:", video_id)
                attachments.append(video_id)
            else:
                print("[VIDEO] Ошибка — пропускаем")
        except Exception as e:
            logging.error(f"[VIDEO] Ошибка: {e}")

    print("[VK] Публикуем:", text)
    print("[VK] Вложения:", attachments)

    # Публикация
    try:
        response = post_to_vk(vk_token, group_id, text, attachments)
        print("[VK] Ответ:", response)
    except Exception as e:
        logging.error(f"[VK] Публикация не удалась: {e}") 
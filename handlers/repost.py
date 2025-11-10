from aiogram import types, Bot
from config import BOT_TOKEN
from db.database import get_user_tokens
from utils.crypto import decrypt
from utils.vk_client import post_to_vk, upload_photo_to_vk, upload_video_to_vk

bot = Bot(token=BOT_TOKEN)

async def repost_channel_post(message: types.Message):
    print("[REPOST] Получено сообщение из канала:", message.chat.id)

    user = get_user_tokens(message.chat.id)
    if not user:
        print("[REPOST] Нет токенов для chat.id =", message.chat.id)
        return

    tg_token = decrypt(user.tg_token.encode())
    vk_token = decrypt(user.vk_token.encode())
    group_id = user.vk_group_id

    print("[TOKENS] TG:", tg_token)
    print("[TOKENS] VK:", vk_token)
    print("[GROUP] VK Group ID:", group_id)

    text = message.text or message.caption or ""
    attachments = []

    if message.photo:
        file = await bot.get_file(message.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{tg_token}/{file.file_path}"
        print("[PHOTO] Загружаем фото:", file_url)
        photo_id = upload_photo_to_vk(vk_token, group_id, file_url)
        if photo_id:
            print("[PHOTO] Загружено:", photo_id)
            attachments.append(photo_id)
        else:
            print("[PHOTO] Ошибка загрузки фото")

    if message.video:
        file = await bot.get_file(message.video.file_id)
        file_url = f"https://api.telegram.org/file/bot{tg_token}/{file.file_path}"
        print("[VIDEO] Загружаем видео:", file_url)
        video_id = upload_video_to_vk(vk_token, group_id, file_url)
        if video_id:
            print("[VIDEO] Загружено:", video_id)
            attachments.append(video_id)
        else:
            print("[VIDEO] Ошибка загрузки видео")

    print("[VK] Публикуем пост:", text)
    print("[VK] Вложения:", attachments)
    response = post_to_vk(vk_token, group_id, text, attachments)
    print("[VK] Ответ:", response)
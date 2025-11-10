from aiogram import types, Bot
from config import BOT_TOKEN
from db.database import get_user_tokens
from utils.crypto import decrypt
from utils.vk_client import post_to_vk, upload_photo_to_vk, upload_video_to_vk

bot = Bot(token=BOT_TOKEN)

async def repost_channel_post(message: types.Message):
    user = get_user_tokens(message.chat.id)
    if not user:
        return

    tg_token = decrypt(user.tg_token.encode())
    vk_token = decrypt(user.vk_token.encode())
    group_id = user.vk_group_id
    text = message.text or message.caption or ""
    attachments = []

    if message.photo:
        file = await bot.get_file(message.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{tg_token}/{file.file_path}"
        photo_id = upload_photo_to_vk(vk_token, group_id, file_url)
        if photo_id:
            attachments.append(photo_id)

    if message.video:
        file = await bot.get_file(message.video.file_id)
        file_url = f"https://api.telegram.org/file/bot{tg_token}/{file.file_path}"
        video_id = upload_video_to_vk(vk_token, group_id, file_url)
        if video_id:
            attachments.append(video_id)

    post_to_vk(vk_token, group_id, text, attachments)
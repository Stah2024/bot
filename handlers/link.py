from aiogram import types, Router
from aiogram.filters import Command
from db.database import get_user_tokens, save_user_tokens
from utils.crypto import encrypt

router = Router()

@router.message(Command("link"))
async def link_channel(message: types.Message):
    if message.chat.type != "channel":
        await message.answer("Эта команда работает только в канале.")
        return

    channel_id = message.chat.id
    user_id = message.from_user.id  # ← если не работает, можно запросить отдельно

    user = get_user_tokens(user_id)
    if not user:
        await message.answer("Сначала пройди настройку в личке.")
        return

    save_user_tokens(
        user_id=user_id,
        tg_token=None,
        vk_token=encrypt(user["vk_token"]),
        group_id=user["vk_group_id"],
        channel_id=channel_id
    )

    await message.answer("Канал успешно привязан! Репосты будут идти в VK.")
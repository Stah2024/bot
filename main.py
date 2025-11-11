import logging
import asyncio
import re
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram import types
from config import BOT_TOKEN
from db.database import init_db, get_user_tokens, save_user_tokens
from utils.crypto import encrypt
from handlers.start import get_main_keyboard
from handlers.settings import (
    connect_callback, get_vk_token,
    get_group_id, ConnectStates
)
from handlers.repost import repost_channel_post

logging.basicConfig(level=logging.INFO)

init_db()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Я репост-бот TG → VK\nВыбери действие:",
        reply_markup=get_main_keyboard()
    )

# FSM
dp.callback_query.register(connect_callback, lambda c: c.data == "connect")
dp.message.register(get_vk_token, ConnectStates.waiting_vk_token)
dp.message.register(get_group_id, ConnectStates.waiting_group_id)

# Репост из канала
dp.channel_post.register(repost_channel_post)

# Команда /link_<user_id> из канала
@dp.channel_post()
async def link_channel(message: types.Message):
    if not message.text:
        return

    match = re.match(r"/link_(\d+)", message.text.strip())
    if not match:
        return

    channel_id = message.chat.id
    user_id = int(match.group(1))

    user = get_user_tokens(user_id)
    if not user:
        await message.answer("❌ Сначала пройди настройку в личке.")
        return

    save_user_tokens(
        user_id=user_id,
        vk_token=encrypt(user["vk_token"]),
        group_id=user["vk_group_id"],
        channel_id=channel_id
    )

    await message.answer("✅ Канал привязан! Репосты будут идти в VK.")

# Заглушки для кнопок
@dp.callback_query(lambda c: c.data == "pay")
async def pay_callback(call: types.CallbackQuery):
    await call.message.answer("💳 Оплата пока не подключена. 7 дней бесплатно.")
    await call.answer()

@dp.callback_query(lambda c: c.data == "help")
async def help_callback(call: types.CallbackQuery):
    await call.message.answer(
        "📌 Инструкция:\n\n"
        "1. Нажми «Подключить»\n"
        "2. Введи VK Community Token\n"
        "3. Укажи ID группы ВКонтакте\n"
        "4. Напиши /link_<user_id> в канале\n\n"
        "После этого бот начнёт репостить из канала в VK."
    )
    await call.answer()

async def main():
    print("Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
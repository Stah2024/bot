import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram import types
import os

from handlers.start import get_main_keyboard
from handlers.settings import (
    connect_callback, get_tg_token, get_vk_token,
    ConnectStates
)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN missing!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хендлер команды /start
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Я репост-бот TG → VK\nВыбери действие:",
        reply_markup=get_main_keyboard()
    )

# Регистрация хендлеров из settings
dp.callback_query.register(connect_callback, lambda c: c.data == "connect")
dp.message.register(get_tg_token, ConnectStates.waiting_tg_token)
dp.message.register(get_vk_token, ConnectStates.waiting_vk_token)

async def main():
    print("Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
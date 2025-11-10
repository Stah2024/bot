import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram import types
from config import BOT_TOKEN
from db.database import init_db
from handlers.start import get_main_keyboard
from handlers.settings import (
    connect_callback, get_tg_token, get_vk_token,
    get_group_id, ConnectStates
)

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

dp.callback_query.register(connect_callback, lambda c: c.data == "connect")
dp.message.register(get_tg_token, ConnectStates.waiting_tg_token)
dp.message.register(get_vk_token, ConnectStates.waiting_vk_token)
dp.message.register(get_group_id, ConnectStates.waiting_group_id)

async def main():
    print("Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
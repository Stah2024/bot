import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import os

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN missing!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Бот жив! Тест через GitHub Actions.\nНапиши /test")

@dp.message_handler(commands=['test'])
async def test(message: types.Message):
    await message.answer("Работает! 🚀")

if name == "main":
    print("Bot started...")
    executor.start_polling(dp, skip_updates=True)

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
from handlers.repost import repost_channel_post
from handlers.link import router as link_router  # 👈 ДОБАВЛЕНО

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
dp.message.register(get_tg_token, ConnectStates.waiting_tg_token)
dp.message.register(get_vk_token, ConnectStates.waiting_vk_token)
dp.message.register(get_group_id, ConnectStates.waiting_group_id)

# Репост из канала
dp.channel_post.register(repost_channel_post)

# Команда /link из канала
dp.include_router(link_router)  # 👈 ДОБАВЛЕНО

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
        "2. Введи токен Telegram-бота\n"
        "3. Введи VK Community Token\n"
        "4. Укажи ID группы ВКонтакте\n\n"
        "После этого бот начнёт репостить из канала в VK."
    )
    await call.answer()

async def main():
    print("Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
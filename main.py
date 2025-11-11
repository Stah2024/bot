import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
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

# FSM: настройка VK
dp.callback_query.register(connect_callback, lambda c: c.data == "connect")
dp.message.register(get_vk_token, ConnectStates.waiting_vk_token)
dp.message.register(get_group_id, ConnectStates.waiting_group_id)

# Репост из канала (бот как админ)
dp.channel_post.register(repost_channel_post)

# Вариант 1: пересланное сообщение из канала
@dp.message(lambda m: m.forward_from_chat and m.forward_from_chat.type == "channel")
async def handle_forwarded_channel(message: types.Message, state):
    channel_id = message.forward_from_chat.id
    user_id = message.from_user.id

    await state.clear()
    await state.update_data(channel_id=channel_id)
    await message.answer(
        f"Канал `{channel_id}` обнаружен и привязан к вашему аккаунту.\n\n"
        "Теперь введи Community Token ВК:"
    )
    await state.set_state(ConnectStates.waiting_vk_token)

# Вариант 2: ручная привязка через команду
@dp.message(Command("link_channel"))
async def link_channel_manual(message: types.Message):
    args = message.text.strip().split()
    if len(args) != 2:
        await message.answer("❌ Используй: /link_channel <channel_id>")
        return

    try:
        channel_id = int(args[1])
    except ValueError:
        await message.answer("❌ channel_id должен быть числом.")
        return

    user_id = message.from_user.id
    user = get_user_tokens(user_id)
    if not user:
        await message.answer("❌ Сначала пройди настройку: /start")
        return

    save_user_tokens(
        user_id=user_id,
        vk_token=encrypt(user["vk_token"]),
        group_id=user["vk_group_id"],
        channel_id=channel_id
    )

    await message.answer(f"✅ Канал {channel_id} привязан! Репосты будут идти в VK.")

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
        "4. Перешли сообщение из канала или напиши /link_channel <channel_id>\n\n"
        "После этого бот начнёт репостить из канала в VK."
    )
    await call.answer()

async def main():
    print("Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
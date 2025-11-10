from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.crypto import encrypt
from utils.vk_client import validate_vk_token
from db.database import save_user_tokens

class ConnectStates(StatesGroup):
    waiting_tg_token = State()
    waiting_vk_token = State()
    waiting_group_id = State()

async def connect_callback(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Введи токен своего Telegram-бота (@BotFather):")
    await state.set_state(ConnectStates.waiting_tg_token)
    await call.answer()

async def get_tg_token(message: types.Message, state: FSMContext):
    try:
        test_bot = types.Bot(token=message.text)
        me = await test_bot.get_me()
        await state.update_data(tg_token=message.text, tg_bot_name=me.username)
        await message.answer(f"✅ Бот @{me.username} найден!\n\nТеперь введи Community Token ВК:")
        await state.set_state(ConnectStates.waiting_vk_token)
    except:
        await message.answer("❌ Неверный Telegram токен. Попробуй ещё:")

async def get_vk_token(message: types.Message, state: FSMContext):
    vk_token = message.text.strip()
    check = validate_vk_token(vk_token)

    if "error" in check:
        await message.answer("❌ Неверный VK токен. Попробуй ещё:")
        return

    await state.update_data(vk_token=vk_token)
    await message.answer("✅ VK токен принят!\n\nТеперь введи ID группы ВКонтакте (без минуса):")
    await state.set_state(ConnectStates.waiting_group_id)

async def get_group_id(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        group_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ ID группы должен быть числом. Попробуй ещё:")
        return

    encrypted_tg = encrypt(data["tg_token"]).decode()
    encrypted_vk = encrypt(data["vk_token"]).decode()

    save_user_tokens(
        user_id=message.from_user.id,
        tg_token=encrypted_tg,
        vk_token=encrypted_vk,
        group_id=group_id
    )

    await message.answer(
        f"✅ Все данные сохранены и зашифрованы!\n\n"
        f"TG: @{data['tg_bot_name']}\n"
        f"VK Group ID: {group_id}\n\n"
        "7 дней бесплатно. Дальше — 200 ₽ или 100 ⭐"
    )
    await state.clear()
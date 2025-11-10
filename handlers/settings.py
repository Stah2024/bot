from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.crypto import encrypt
from db.database import save_user_tokens

class ConnectStates(StatesGroup):
    waiting_tg_token = State()
    waiting_vk_token = State()

async def connect_callback(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Введи токен своего Telegram-бота (@BotFather):")
    await state.set_state(ConnectStates.waiting_tg_token)
    await call.answer()

async def get_tg_token(message: types.Message, state: FSMContext):
    try:
        test_bot = types.Bot(token=message.text)
        me = await test_bot.get_me()
        await state.update_data(tg_token=message.text, tg_bot_name=me.username)
        await message.answer(f"Бот @{me.username} найден!\n\nВведи Community Token ВК:")
        await state.set_state(ConnectStates.waiting_vk_token)
    except:
        await message.answer("Неверный токен. Попробуй ещё:")

async def get_vk_token(message: types.Message, state: FSMContext):
    data = await state.get_data()
    encrypted_tg = encrypt(data["tg_token"])
    encrypted_vk = encrypt(message.text)
    
    save_user_tokens(
        user_id=message.from_user.id,
        tg_token=encrypted_tg,
        vk_token=encrypted_vk
    )
    
    await message.answer(
        "Токены сохранены и зашифрованы!\n\n"
        "7 дней бесплатно. Дальше — 200 ₽ или 100 ⭐️"
    )
    await state.clear()

# handlers/settings.py
import requests
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.crypto import encrypt
from utils.vk_client import validate_vk_token
from db.database import save_user_tokens
import logging

logger = logging.getLogger(__name__)

class ConnectStates(StatesGroup):
    waiting_tg_token = State()
    waiting_vk_token = State()
    waiting_group_id = State()


async def connect_callback(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Введи токен своего Telegram-бота (@BotFather):")
    await state.set_state(ConnectStates.waiting_tg_token)
    await call.answer()


async def get_tg_token(message: types.Message, state: FSMContext):
    token = message.text.strip()
    url = f"https://api.telegram.org/bot{token}/getMe"

    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if not data.get("ok") or "username" not in data.get("result", {}):
            raise ValueError("Invalid token")
    except Exception as e:
        logger.error(f"Ошибка проверки TG токена: {e}")
        await message.answer("Неверный Telegram токен. Попробуй ещё:")
        return

    await state.update_data(tg_token=token, tg_bot_name=data["result"]["username"])
    await message.answer(f"Бот @{data['result']['username']} найден!\n\nТеперь введи Community Token ВК:")
    await state.set_state(ConnectStates.waiting_vk_token)


async def get_vk_token(message: types.Message, state: FSMContext):
    vk_token = message.text.strip()
    check = validate_vk_token(vk_token)

    if "error" in check:
        await message.answer("Неверный VK токен. Попробуй ещё:")
        return

    await state.update_data(vk_token=vk_token)
    await message.answer("VK токен принят!\n\nТеперь введи ID группы ВКонтакте (без минуса):")
    await state.set_state(ConnectStates.waiting_group_id)


async def get_group_id(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    # ← ПРОВЕРКА: токены должны быть строками!
    tg_token = data.get("tg_token")
    vk_token = data.get("vk_token")
    tg_bot_name = data.get("tg_bot_name")

    if not all(isinstance(x, str) for x in [tg_token, vk_token]):
        await message.answer("Ошибка: данные повреждены. Начни заново: /start")
        await state.clear()
        return

    try:
        group_id_input = int(message.text.strip())
    except ValueError:
        await message.answer("ID группы должен быть числом. Попробуй ещё:")
        return

    vk_group_id = f"-{group_id_input}"

    try:
        encrypted_tg = encrypt(tg_token)
        encrypted_vk = encrypt(vk_token)

        save_user_tokens(
            user_id=message.from_user.id,
            tg_token=encrypted_tg,
            vk_token=encrypted_vk,
            group_id=vk_group_id
        )

        logger.info(f"Токены сохранены для user_id={message.from_user.id}, группа: {vk_group_id}")

        await message.answer(
            f"Все данные сохранены и зашифрованы!\n\n"
            f"TG: @{tg_bot_name}\n"
            f"VK Group ID: {group_id_input}\n\n"
            "7 дней бесплатно. Дальше — 200 ₽ или 100 ⭐"
        )
    except Exception as e:
        logger.error(f"Ошибка сохранения токенов: {e}")
        await message.answer("Ошибка при сохранении. Попробуй позже.")
    
    await state.clear()
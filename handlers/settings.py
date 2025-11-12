from aiogram import types, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.crypto import encrypt
from utils.vk_client import validate_vk_token
from db.database import save_user_tokens
import logging

logger = logging.getLogger(__name__)
router = Router()

class ConnectStates(StatesGroup):
    waiting_vk_token = State()
    waiting_group_id = State()

# Привязка канала через пересланное сообщение
@router.message(lambda m: m.forward_from_chat and m.forward_from_chat.type == "channel")
async def handle_forwarded_channel(message: types.Message, state: FSMContext):
    channel_id = message.forward_from_chat.id
    user_id = message.from_user.id

    await state.clear()
    await state.update_data(channel_id=channel_id)
    await message.answer(
        f"Канал `{channel_id}` обнаружен и привязан к вашему аккаунту.\n\n"
        "Теперь введи Community Token ВК:"
    )
    await state.set_state(ConnectStates.waiting_vk_token)

# Репост из канала (бот как админ)
@router.channel_post()
async def handle_channel_post(message: types.Message):
    channel_id = message.chat.id
    logger.info(f"[CHANNEL POST] Получено сообщение из канала {channel_id}")

# Кнопка "Подключить"
@router.callback_query(lambda c: c.data == "connect")
async def connect_callback(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer(
        "📌 Настройка подключения:\n\n"
        "1️⃣ Добавь меня (бота) в свой канал **в Telegram** как администратора.\n"
        "🔒 Обязательно выдай права:\n"
        "• Читать сообщения\n"
        "• Публиковать сообщения\n"
        "• Управлять подписчиками (если доступно)\n\n"
        "2️⃣ Перешли **любое сообщение из этого канала** мне в личку — это нужно, чтобы я сохранил ID канала.\n\n"
        "3️⃣ Введи **VK Community Token** — это токен из приложения типа *Standalone*, а не токен группы.\n"
        "📎 Как получить токен — инструкция будет добавлена позже.\n\n"
        "4️⃣ Введи **ID группы ВКонтакте** (без минуса).\n\n"
        "✅ После этого бот начнёт репостить из Telegram-канала в VK."
    )
    await call.answer()

# Получение VK токена
@router.message(ConnectStates.waiting_vk_token)
async def get_vk_token(message: types.Message, state: FSMContext):
    vk_token = message.text.strip()
    print("[FSM] vk_token получен:", vk_token)

    check = validate_vk_token(vk_token)
    print("[FSM] validate_vk_token вернул:", check)

    if "error" in check:
        await message.answer("❌ Неверный VK токен. Попробуй ещё:")
        return

    await state.update_data(vk_token=vk_token)
    await message.answer("✅ VK токен принят!\n\nТеперь введи ID группы ВКонтакте (без минуса):")
    await state.set_state(ConnectStates.waiting_group_id)

# Получение VK group_id и сохранение связки
@router.message(ConnectStates.waiting_group_id)
async def get_group_id(message: types.Message, state: FSMContext):
    data = await state.get_data()
    vk_token = data.get("vk_token")
    channel_id = data.get("channel_id") or (
        message.chat.id if message.chat.type == "channel" else None
    )

    if not vk_token or not isinstance(vk_token, str):
        await message.answer("Ошибка: данные повреждены. Начни заново: /start")
        await state.clear()
        return

    if not channel_id:
        await message.answer("❌ Сначала перешли сообщение из канала, чтобы я знал, куда репостить.")
        await state.clear()
        return

    try:
        group_id_input = int(message.text.strip())
    except ValueError:
        await message.answer("ID группы должен быть числом. Попробуй ещё:")
        return

    vk_group_id = f"-{group_id_input}"

    try:
        encrypted_vk = encrypt(vk_token)

        save_user_tokens(
            user_id=message.from_user.id,
            vk_token=encrypted_vk,
            group_id=vk_group_id,
            channel_id=channel_id
        )

        logger.info(f"Токены сохранены: user_id={message.from_user.id}, группа={vk_group_id}, канал={channel_id}")

        await message.answer(
            f"✅ Все данные сохранены и зашифрованы!\n\n"
            f"VK Group ID: {group_id_input}\n\n"
            "🔓 Бот работает условно бесплатно.\n"
            "💡 В будущем будет символическая подписка."
        )
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        await message.answer("Ошибка при сохранении. Попробуй позже.")

    await state.clear()
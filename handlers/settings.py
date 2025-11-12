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
        f"Канал `{channel_id}` обнаружен и привязан.\n\n"
        "Теперь пришли **Community Token** из **настроек группы ВК**:\n"
        "→ Управление → Работа с API → Создать ключ\n"
        "→ Отметь: `wall`, `photos`, `video`, `docs`\n"
        "→ Скопируй токен и пришли сюда."
    )
    await state.set_state(ConnectStates.waiting_vk_token)


# Репост из канала (бот как админ)
@router.channel_post()
async def handle_channel_post(message: types.Message):
    channel_id = message.chat.id
    logger.info(f"[CHANNEL POST] Сообщение из канала {channel_id}")


# Кнопка "Подключить"
@router.callback_query(lambda c: c.data == "connect")
async def connect_callback(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer(
        "Настройка подключения:\n\n"
        "1. Добавь бота в **Telegram-канал** как админа:\n"
        "   • Читать сообщения\n"
        "   • Публиковать сообщения\n\n"
        "2. Перешли **любое сообщение из канала** в личку боту.\n\n"
        "3. В **VK-группе**:\n"
        "   → Управление → Работа с API → Создать ключ\n"
        "   → Отметь: `wall`, `photos`, `video`, `docs`\n"
        "   → Скопируй токен → пришли боту\n\n"
        "4. Введи **ID группы ВК** (без минуса, например: `12345678`)\n\n"
        "После этого бот начнёт репостить из TG в VK."
    )
    await call.answer()


# Получение VK токена
@router.message(ConnectStates.waiting_vk_token)
async def get_vk_token(message: types.Message, state: FSMContext):
    vk_token = message.text.strip()
    logger.info(f"[FSM] Получен VK токен от user {message.from_user.id}")

    # Проверяем токен
    check = validate_vk_token(vk_token)
    logger.info(f"[FSM] validate_vk_token: {check}")

    if "error" in check:
        await message.answer(
            f"Неверный токен:\n`{check['error']}`\n\n"
            "Попробуй снова:",
            parse_mode="Markdown"
        )
        return

    # Сохраняем токен
    await state.update_data(vk_token=vk_token)

    # Автоопределение группы из токена (если сервисный)
    if check.get("ok"):
        group_id = check["group_id"]
        await state.update_data(auto_group_id=f"-{group_id}")
        await message.answer(
            f"Токен принят!\n"
            f"Группа найдена: `{check['name']}` (ID: {group_id})\n\n"
            "Подтверди ID (или введи другой, без минуса):",
            parse_mode="Markdown"
        )
    else:
        await message.answer("Токен принят!\n\nВведи ID группы ВК (без минуса):")

    await state.set_state(ConnectStates.waiting_group_id)


# Получение group_id и сохранение
@router.message(ConnectStates.waiting_group_id)
async def get_group_id(message: types.Message, state: FSMContext):
    data = await state.get_data()
    vk_token = data.get("vk_token")
    channel_id = data.get("channel_id")

    if not vk_token:
        await message.answer("Ошибка: токен потерян. Начни заново: /start")
        await state.clear()
        return

    if not channel_id:
        await message.answer("Сначала перешли сообщение из канала.")
        await state.clear()
        return

    # Авто-ID из токена
    auto_id = data.get("auto_group_id")

    try:
        input_text = message.text.strip()
        if input_text.lower() in ["да", "ok", "подтвердить"] and auto_id:
            group_id = auto_id
        else:
            raw_id = int(input_text)
            group_id = f"-{raw_id}"
    except ValueError:
        await message.answer("ID должен быть числом. Попробуй ещё:")
        return

    try:
        encrypted_token = encrypt(vk_token)

        save_user_tokens(
            user_id=message.from_user.id,
            vk_token=encrypted_token,
            group_id=group_id,
            channel_id=channel_id
        )

        logger.info(f"Сохранено: user={message.from_user.id}, группа={group_id}, канал={channel_id}")

        await message.answer(
            f"Всё подключено!\n\n"
            f"VK Group: `{group_id}`\n"
            f"Telegram Channel: `{channel_id}`\n\n"
            "Бот начнёт репостить новые посты.",
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        await message.answer("Ошибка при сохранении. Попробуй позже.")

    await state.clear()
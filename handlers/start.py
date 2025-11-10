from aiogram import types

def get_main_keyboard():
    keyboard = [
        [types.InlineKeyboardButton(text="Подключить", callback_data="connect")],
        [types.InlineKeyboardButton(text="Оплатить", callback_data="pay")],
        [types.InlineKeyboardButton(text="Инструкция", callback_data="help")]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard)
from aiogram import types

def get_main_keyboard():
    buttons = [
        [types.InlineKeyboardButton("Подключить", callback_data="connect")],
        [types.InlineKeyboardButton("Оплатить", callback_data="pay")],
        [types.InlineKeyboardButton("Инструкция", callback_data="help")]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)
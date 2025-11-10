from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Подключить", callback_data="connect")],
            [InlineKeyboardButton(text="Оплатить", callback_data="pay")],
            [InlineKeyboardButton(text="Инструкция", callback_data="help")]
        ]
    )
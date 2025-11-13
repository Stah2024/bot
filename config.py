import os
from dotenv import load_dotenv

load_dotenv()

# === БОТ ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env")

# === КЛЮЧ ШИФРОВАНИЯ ===
raw_key = os.getenv("CRYPTO_KEY")
if not raw_key:
    raise ValueError("CRYPTO_KEY не найден в .env")

# Приводим ключ к bytes (для cryptography)
if isinstance(raw_key, str):
    CRYPTO_KEY = raw_key.encode()
elif isinstance(raw_key, bytes):
    CRYPTO_KEY = raw_key
else:
    raise TypeError("CRYPTO_KEY должен быть строкой или байтами")
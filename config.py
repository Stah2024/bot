import os
from dotenv import load_dotenv

load_dotenv()

# === БОТ ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env")

# === КЛЮЧ ШИФРОВАНИЯ ===
CRYPTO_KEY = os.getenv("CRYPTO_KEY")
if not CRYPTO_KEY:
    raise ValueError("CRYPTO_KEY не найден в .env")

# Приводим ключ к bytes (для cryptography)
try:
    CRYPTO_KEY = CRYPTO_KEY.encode()  # ← bytes, как нужно
except Exception as e:
    raise ValueError(f"CRYPTO_KEY должен быть строкой: {e}")
from cryptography.fernet import Fernet
from config import CRYPTO_KEY  # ← CRYPTO_KEY уже bytes!

# ← УБРАЛ .encode()! ОШИБКА БЫЛА ЗДЕСЬ
fernet = Fernet(CRYPTO_KEY)

def encrypt(text: str) -> bytes:
    return fernet.encrypt(text.encode())

def decrypt(token: bytes) -> str:
    return fernet.decrypt(token).decode()
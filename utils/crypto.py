from cryptography.fernet import Fernet
from config import CRYPTO_KEY

fernet = Fernet(CRYPTO_KEY)  # ✅ ключ уже bytes, encode не нужен

def encrypt(text: str) -> bytes:
    return fernet.encrypt(text.encode())

def decrypt(token: bytes) -> str:
    return fernet.decrypt(token).decode()
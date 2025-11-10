from cryptography.fernet import Fernet
import os

fernet = Fernet(os.getenv("CRYPTO_KEY").encode())

def encrypt(text: str) -> bytes:
    return fernet.encrypt(text.encode())

def decrypt(token: bytes) -> str:
    return fernet.decrypt(token).decode()

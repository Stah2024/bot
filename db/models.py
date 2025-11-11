from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, LargeBinary, DateTime, BigInteger
from datetime import datetime

class Base(DeclarativeBase):
    pass

class UserConnection(Base):
    __tablename__ = "user_connections"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, nullable=False, unique=True, index=True)

    # ТОКЕН ВК — ЗАШИФРОВАННЫЙ (bytes)
    vk_token = Column(LargeBinary, nullable=False)

    # ID группы ВК — СТРОКА с минусом
    vk_group_id = Column(String, nullable=False)

    # ID Telegram-канала, откуда идёт репост
    channel_id = Column(BigInteger, nullable=True, unique=True)

    created_at = Column(DateTime, default=datetime.utcnow)
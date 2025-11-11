from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, LargeBinary, DateTime, BigInteger
from datetime import datetime, timedelta

class Base(DeclarativeBase):
    pass

class UserConnection(Base):
    __tablename__ = "user_connections"

    id = Column(Integer, primary_key=True, index=True)

    # Telegram user ID
    telegram_id = Column(BigInteger, nullable=False, unique=True, index=True)

    # VK токен (зашифрованный)
    vk_token = Column(LargeBinary, nullable=False)

    # VK group ID (строка с минусом)
    vk_group_id = Column(String, nullable=False)

    # Telegram channel ID (откуда идёт репост)
    channel_id = Column(BigInteger, nullable=True, unique=True, index=True)

    # Дата создания записи
    created_at = Column(DateTime, default=datetime.utcnow)

    # Дата оплаты
    paid_at = Column(DateTime, default=datetime.utcnow)

    # Срок действия подписки
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))
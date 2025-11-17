# db/models.py
from sqlalchemy import (
    Column, Integer, BigInteger, Text, DateTime, Boolean, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    telegram_id = Column(BigInteger, primary_key=True)
    vk_token = Column(Text, nullable=True)           # один токен на пользователя
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False, index=True)
    tg_channel_id = Column(BigInteger, nullable=False)      # откуда берём посты
    vk_group_id = Column(BigInteger, nullable=False)        # отрицательное число = группа ВК
    vk_group_name = Column(Text, nullable=True)             # для красоты в /list
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
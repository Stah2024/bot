from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

class Base(DeclarativeBase):
    pass

class UserConnection(Base):
    __tablename__ = "user_connections"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False, unique=True)
    tg_token = Column(String, nullable=False)
    vkken = Column(String, nullable=False)
    vk_group_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
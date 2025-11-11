# db/models.py
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, LargeBinary, DateTime
from datetime import datetime

class Base(DeclarativeBase):
    pass

class UserConnection(Base):
    __tablename__ = "user_connections"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, nullable=False, unique=True, index=True)
    
    # ТОКЕНЫ — ЗАШИФРОВАННЫЕ (bytes)
    tg_token = Column(LargeBinary, nullable=False)    # ← зашифровано
    vk_token = Column(LargeBinary, nullable=False)    # ← зашифровано
    
    # ID группы ВК — СТРОКА с минусом
    vk_group_id = Column(String, nullable=False)      # ← "-123456789"
    
    created_at = Column(DateTime, default=datetime.utcnow)
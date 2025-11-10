from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class UserConnection(Base):
    tablename = "user_connections"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False, unique=True)
    tg_token = Column(String, nullable=False)
    vk_token = Column(String, nullable=False)
    vk_group_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

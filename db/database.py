# db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, UserConnection
from utils.crypto import encrypt, decrypt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = create_engine("sqlite:///bot.db", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("БД инициализирована: bot.db")
    except Exception as e:
        logger.error(f"Ошибка БД: {e}")
        raise

def save_user_tokens(user_id: int, tg_token: str, vk_token: str, group_id: str):
    session = SessionLocal()
    try:
        existing = session.query(UserConnection).filter_by(telegram_id=user_id).first()
        enc_tg = encrypt(tg_token)
        enc_vk = encrypt(vk_token)

        if existing:
            existing.tg_token = enc_tg
            existing.vk_token = enc_vk
            existing.vk_group_id = group_id
        else:
            user = UserConnection(
                telegram_id=user_id,
                tg_token=enc_tg,
                vk_token=enc_vk,
                vk_group_id=group_id
            )
            session.add(user)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка сохранения: {e}")
        raise
    finally:
        session.close()

def get_user_tokens(user_id: int):
    session = SessionLocal()
    try:
        user = session.query(UserConnection).filter_by(telegram_id=user_id).first()
        if user:
            return {
                "tg_token": decrypt(user.tg_token),
                "vk_token": decrypt(user.vk_token),
                "vk_group_id": user.vk_group_id
            }
        return None
    except Exception as e:
        logger.error(f"Ошибка чтения: {e}")
        return None
    finally:
        session.close()
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, UserConnection
from utils.crypto import decrypt
import logging
from datetime import datetime, timedelta

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

def save_user_tokens(user_id: int, vk_token: bytes, group_id: str, channel_id: int,
                     paid_at=None, expires_at=None):
    """
    Сохраняем токен для конкретного канала.
    Теперь у одного user_id может быть несколько каналов.
    """
    session = SessionLocal()
    try:
        existing = session.query(UserConnection).filter_by(channel_id=channel_id).first()

        if existing:
            # обновляем запись для конкретного канала
            existing.vk_token = vk_token
            existing.vk_group_id = group_id
            existing.telegram_id = user_id
            if paid_at:
                existing.paid_at = paid_at
            if expires_at:
                existing.expires_at = expires_at
        else:
            # создаём новую запись для нового канала
            user = UserConnection(
                telegram_id=user_id,
                vk_token=vk_token,
                vk_group_id=group_id,
                channel_id=channel_id,
                paid_at=paid_at or datetime.utcnow(),
                expires_at=expires_at or datetime.utcnow() + timedelta(days=7)
            )
            session.add(user)
        session.commit()
        logger.info(f"Токены успешно сохранены для user_id={user_id}, channel_id={channel_id}")
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка сохранения: {e}")
        raise
    finally:
        session.close()

def get_user_tokens(user_id: int):
    """
    Возвращает все каналы и группы, привязанные к user_id.
    """
    session = SessionLocal()
    try:
        users = session.query(UserConnection).filter_by(telegram_id=user_id).all()
        result = []
        for user in users:
            result.append({
                "vk_token": decrypt(user.vk_token),
                "vk_group_id": user.vk_group_id,
                "channel_id": user.channel_id,
                "paid_at": user.paid_at,
                "expires_at": user.expires_at
            })
        return result if result else None
    except Exception as e:
        logger.error(f"Ошибка чтения: {e}")
        return None
    finally:
        session.close()

def get_user_tokens_by_channel(channel_id: int):
    """
    Возвращает токен и группу для конкретного канала.
    """
    session = SessionLocal()
    try:
        user = session.query(UserConnection).filter_by(channel_id=channel_id).first()
        if user:
            return {
                "vk_token": decrypt(user.vk_token),
                "vk_group_id": user.vk_group_id,
                "telegram_id": user.telegram_id,
                "paid_at": user.paid_at,
                "expires_at": user.expires_at
            }
        return None
    except Exception as e:
        logger.error(f"Ошибка поиска по каналу: {e}")
        return None
    finally:
        session.close()

def check_subscription(user_id: int):
    """
    Проверяет подписку по user_id — если хотя бы один канал активен, возвращает True.
    """
    session = SessionLocal()
    try:
        users = session.query(UserConnection).filter_by(telegram_id=user_id).all()
        for user in users:
            if user.expires_at and user.expires_at > datetime.utcnow():
                return True
        return False
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return False
    finally:
        session.close()
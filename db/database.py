# db/database.py
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from db.models import Base, User, Subscription
from utils.crypto import encrypt, decrypt
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

engine = create_engine("sqlite:///bot.db", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def init_db():
    Base.metadata.create_all(bind=engine)
    logger.info("БД готова (новая схема: users + subscriptions)")

# 1. Сохранение/обновление токена и подписок
def save_or_update_user(telegram_id: int, vk_token: str):
    session = SessionLocal()
    try:
        user = session.query(User).get(telegram_id)
        if user:
            user.vk_token = encrypt(vk_token)
        else:
            user = User(telegram_id=telegram_id, vk_token=encrypt(vk_token))
            session.add(user)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка сохранения токена: {e}")
    finally:
        session.close()

def add_subscription(telegram_id: int, tg_channel_id: int, vk_group_id: int, vk_group_name: str = None):
    session = SessionLocal()
    try:
        # Проверяем, нет ли уже точно такой же подписки
        exists = session.query(Subscription).filter_by(
            telegram_id=telegram_id,
            tg_channel_id=tg_channel_id,
            vk_group_id=vk_group_id
        ).first()
        if exists:
            return False  # уже есть

        sub = Subscription(
            telegram_id=telegram_id,
            tg_channel_id=tg_channel_id,
            vk_group_id=vk_group_id,
            vk_group_name=vk_group_name or f"Группа {vk_group_id}"
        )
        session.add(sub)
        session.commit()
        logger.info(f"Добавлена подписка: {tg_channel_id} → {vk_group_id}")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка добавления подписки: {e}")
        return False
    finally:
        session.close()

# 2. Получение всех подписок для канала (именно то, что нужно repost.py)
def get_subscriptions_by_channel(tg_channel_id: int):
    session = SessionLocal()
    try:
        rows = session.query(Subscription, User.vk_token).join(
            User, Subscription.telegram_id == User.telegram_id
        ).filter(
            Subscription.tg_channel_id == tg_channel_id,
            Subscription.is_active == True
        ).all()

        result = []
        for sub, encrypted_token in rows:
            result.append({
                "vk_token": decrypt(encrypted_token),
                "vk_group_id": str(sub.vk_group_id),
                "vk_group_name": sub.vk_group_name or "Группа ВК"
            })
        return result
    except Exception as e:
        logger.error(f"Ошибка получения подписок: {e}")
        return []
    finally:
        session.close()

# 3. Для команды /list — все подписки пользователя
def get_user_subscriptions(telegram_id: int):
    session = SessionLocal()
    try:
        rows = session.query(Subscription).filter_by(telegram_id=telegram_id).all()
        return [
            {
                "tg_channel_id": s.tg_channel_id,
                "vk_group_id": s.vk_group_id,
                "vk_group_name": s.vk_group_name,
                "active": s.is_active
            } for s in rows
        ]
    finally:
        session.close()
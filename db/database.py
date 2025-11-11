# db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, UserConnection
from utils.crypto import encrypt, decrypt
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Подключение к SQLite (можно заменить на PostgreSQL)
engine = create_engine("sqlite:///bot.db", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db():
    """
    Инициализация БД: создаёт таблицу, если её нет.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("База данных инициализирована: bot.db")
    except Exception as e:
        logger.error(f"Ошибка при инициализации БД: {e}")
        raise


def save_user_tokens(user_id: int, tg_token: str, vk_token: str, group_id: str):
    """
    Сохраняет зашифрованные токены пользователя.
    """
    session = SessionLocal()
    try:
        # Проверяем, есть ли пользователь
        existing = session.query(UserConnection).filter_by(telegram_id=user_id).first()

        # Шифруем токены
        encrypted_tg = encrypt(tg_token)
        encrypted_vk = encrypt(vk_token)

        if existing:
            # Обновляем
            existing.tg_token = encrypted_tg
            existing.vk_token = encrypted_vk
            existing.vk_group_id = group_id
            logger.info(f"Токены обновлены для user_id={user_id}")
        else:
            # Создаём нового
            new_user = UserConnection(
                telegram_id=user_id,
                tg_token=encrypted_tg,
                vk_token=encrypted_vk,
                vk_group_id=group_id
            )
            session.add(new_user)
            logger.info(f"Новый пользователь добавлен: user_id={user_id}")

        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка сохранения токенов для user_id={user_id}: {e}")
        raise
    finally:
        session.close()


def get_user_tokens(user_id: int):
    """
    Возвращает расшифрованные токены или None.
    """
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
        logger.error(f"Ошибка чтения токенов для user_id={user_id}: {e}")
        return None
    finally:
        session.close()


def delete_user_tokens(user_id: int):
    """
    Удаляет пользователя (для отладки).
    """
    session = SessionLocal()
    try:
        user = session.query(UserConnection).filter_by(telegram_id=user_id).first()
        if user:
            session.delete(user)
            session.commit()
            logger.info(f"Пользователь удалён: user_id={user_id}")
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка удаления: {e}")
    finally:
        session.close()
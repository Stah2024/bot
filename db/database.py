from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, UserConnection

engine = create_engine("sqlite:///bot.db")
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def save_user_tokens(user_id, tg_token, vk_token, group_id):
    session = SessionLocal()
    existing = session.query(UserConnection).filter_by(telegram_id=user_id).first()
    if existing:
        existing.tg_token = tg_token
        existing.vk_token = vk_token
        existing.vk_group_id = group_id
    else:
        new_user = UserConnection(
            telegram_id=user_id,
            tg_token=tg_token,
            vk_token=vk_token,
            vk_group_id=group_id
        )
        session.add(new_user)
    session.commit()
    session.close()

def get_user_tokens(user_id):
    session = SessionLocal()
    user = session.query(UserConnection).filter_by(telegram_id=user_id).first()
    session.close()
    return user
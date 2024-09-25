from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config import DB_CONNECT

# Создание подключения к базе данных

engine = create_engine(DB_CONNECT)

# Создание фабрики сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создание всех таблиц в базе данных
# Base.metadata.create_all(engine)

# Функция для получения сессии базы данных
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
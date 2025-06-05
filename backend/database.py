import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError

DATABASE_URL = "sqlite:////app/data/plantastic_db.db"

try:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,  # Проверка соединения перед использованием
        echo=os.getenv("DB_ECHO", "false").lower() == "true"  # Логирование SQL запросов
    )
except Exception as e:
    logging.error(f"Ошибка создания движка БД: {e}")
    raise
    
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False  # Объекты остаются доступными после commit
)
Base = declarative_base()


# Функция для создания директории БД
def ensure_db_directory():
    """Создает директорию для БД если её нет"""
    if DATABASE_URL.startswith("sqlite"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logging.info(f"Создана директория для БД: {db_dir}")


# Функция для проверки подключения к БД
def check_db_connection():
    """Проверяет подключение к БД"""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logging.info("Подключение к БД успешно")
        return True
    except SQLAlchemyError as e:
        logging.error(f"Ошибка подключения к БД: {e}")
        return False
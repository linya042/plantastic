import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, select, func, update
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Optional, Any
from schemas import UserCreate, UserPlantCreate, UserPlantUpdate, TaskCreate, TaskUpdate, DiseaseWithSymptoms
from models import (Plant, Disease, DiseaseSymptom, PlantNNClass, DiseaseNNClass, 
                    User, UserPlant, SoilType, TaskType, Task, PlantImage, UserPlantImage)
from datetime import date, datetime, timedelta
import json

logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite+aiosqlite:////app/data/plantastic_db.db"

try:
    engine = create_async_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Проверка соединения перед использованием
        echo=os.getenv("DB_ECHO", "false").lower() == "true"  # Логирование SQL запросов
    )
except Exception as e:
    logger.error(f"Ошибка создания движка БД: {e}")
    raise
    
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,  # Объекты остаются доступными после commit
    class_=AsyncSession # Явно указываем класс сессии
)


# Функция для создания директории БД
def ensure_db_directory():
    """Создает директорию для БД если её нет"""
    if DATABASE_URL.startswith("sqlite"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Создана директория для БД: {db_dir}")


# Функция для проверки подключения к БД
async def check_db_connection(db: AsyncSession) -> bool:
    """Проверяет подключение к БД"""
    try:
        await db.execute(text("SELECT 1"))
        logger.info("Подключение к БД успешно")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Ошибка подключения к БД: {e}")
        return False


# Зависимость FastAPI для получения асинхронной сессии
async def get_async_db():
    """Зависимость для получения сессии базы данных"""
    async with AsyncSessionLocal() as session:
        yield session


async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int) -> Optional[User]:
    """
    Получает пользователя из БД по Telegram ID.

    Args:
        db: Асинхронная сессия базы данных
        telegram_id: Telegram ID пользователя
        
    Returns:
        Объект пользователя или None, если не найден
    """
    if not isinstance(telegram_id, int) or telegram_id <= 0:
        logger.warning(f"Невалидный telegram_id: {telegram_id}")
        return None
    
    try:
        stmt = select(User).where(User.user_id == telegram_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if user:
            logger.info(f"Пользователь с Telegram ID {telegram_id} найден в БД")
        else:
            logger.info(f"Пользователь с Telegram ID {telegram_id} не найден в БД")
        
        return user
    
    except Exception as e:
        logger.error(f"Ошибка при поиске пользователя с Telegram ID {telegram_id}: {e}", exc_info=True)
        return None


def tg_data_to_user_create(telegram_data: Dict[str, Any]) -> UserCreate:
    """
    Конвертирует данные от Telegram в схему UserCreate.
    
    Args:
        telegram_data: Валидированные данные от Telegram
        
    Returns:
        Объект UserCreate
    """
    # Создаем базовые настройки для нового пользователя
    default_settings = {
        # "notifications": True,
        # "language": "ru",
        # "theme": "light"
    }
    
    return UserCreate(
        user_id=telegram_data['id'],
            first_name=telegram_data.get('first_name'),
            username=telegram_data.get('username'),
            timezone="UTC+5",  # TODO: определять автоматически
            settings_json=json.dumps(default_settings, ensure_ascii=False)
    )


async def create_new_user(db: AsyncSession, user_data: UserCreate) -> Optional[User]:
    """
    Создает нового пользователя в БД на основе валидированных данных от Telegram.
    
    Args:
        db: Асинхронная сессия базы данных
        user_data: Данные пользователя от Telegram
        
    Returns:
        Созданный объект пользователя или None при ошибке
    """
    try:
        new_user = User(**user_data.model_dump())
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"Создан новый пользователь с Telegram ID {new_user.user_id}")
        return new_user
        
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при создании пользователя с Telegram ID {user_data.user_id}: {e}", exc_info=True)
        await db.rollback() # Откат транзакции при ошибке
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при создании пользователя с Telegram ID {user_data.user_id}: {e}", exc_info=True)
        await db.rollback()
        return None


async def update_user_activity(db: AsyncSession, user: User) -> bool:
    """
    Обновляет дату последней активности пользователя.
    
    Args:
        db: Асинхронная сессия базы данных
        user: Объект пользователя
        
    Returns:
        True при успешном обновлении, False при ошибке
    """
    try:
        user.last_activity_date = datetime.now()
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"Обновлена дата активности для пользователя {user.user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении активности пользователя {user.user_id}: {e}", exc_info=True)
        await db.rollback()
        return False


async def get_plant_from_db_by_nn(db: AsyncSession, class_names: List[str]) -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Получает информацию о растении из БД по имени класса нейронной сети.

    Args:
        db: Асинхронная cессия базы данных SQLAlchemy.
        class_name: Список имен класса, предсказанных нейронной сетью (class_label из PlantNNClass).

    Returns:
        Словарь, где ключ - class_label, а значение - словарь с полной информацией о растении,
        включая 'plant_id' как 'item_id' и 'common_name_ru' как 'item_name'.
        Возвращает только те растения, которые были найдены.
    """
    if not class_names:
        return None
    
    try:
        # Строим асинхронный запрос для получения PlantNNClass объектов
        # и связанных с ними объектов Plant
        stmt = select(PlantNNClass).options(
            selectinload(PlantNNClass.plant_nn_classes_images)
        ).where(
            PlantNNClass.class_label.in_(class_names)
        )

        result = await db.execute(stmt)
        nn_classes_found = result.scalars().unique().all() # .unique() для избежания дубликатов при join

        if nn_classes_found is None:
            logger.warning(f"Классы '{class_names}' не найдены в таблице 'plant_nn_class' БД.")
            return None

        variety_info_map: Dict[str, Dict[str, Any]] = {}
        for nn_class in nn_classes_found:

            if nn_class.plant_nn_classes_images:
                sorted_images = sorted(
                    nn_class.plant_nn_classes_images,
                    key=lambda img: not getattr(img, 'is_main_image', False)
                )
                images_urls = [img.image_url for img in sorted_images]

                variety_info_map[nn_class.class_label] = {
                    "item_id": nn_class.class_id,
                    "item_name": nn_class.variety_name,
                    "images": images_urls
                }

        return variety_info_map
    
    except Exception as e:
        logger.error(f"Ошибка при получении информации о сортах для имен классов '{class_names}': {e}")
        return None
    

async def get_variety_by_id(db: AsyncSession, variety_id: int) -> Optional[PlantNNClass]:
    """
    Получает информацию о сорте растения из БД по ID.

    Args:
        db: Асинхронная cессия базы данных SQLAlchemy.
        variety_id: ID сорта (class_id из таблицы plant_nn_classes).

    Returns:
        Словарь с полной информацией о сорте растения.
    """
    try:
        stmt = select(PlantNNClass).where(PlantNNClass.class_id == variety_id)
        result = await db.execute(stmt)
        variety_data = result.scalars().first()

        if variety_data is None:
            logger.warning(f"Сорт растения с ID '{variety_id}' не найдено в таблице 'plant_nn_classes' БД.")
            return None

        return variety_data
    
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при получении информации о сорте растении для class_id '{variety_id}': {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении информации о сорте растении для class_id '{variety_id}': {e}", exc_info=True)
        return None


async def get_plant_by_id(db: AsyncSession, plant_id: int) -> Optional[Plant]:
    """
    Получает информацию о растении из БД по ID, включая связанные изображения.

    Args:
        db: Асинхронная cессия базы данных SQLAlchemy.
        plant_id: ID растения (plant_id из таблицы plants).

    Returns:
        Словарь с полной информацией о растении.
        Возвращает только те растения, которые были найдены.
    """
    try:
        stmt = select(Plant).options(
            selectinload(Plant.nn_classes).options(
                selectinload(PlantNNClass.plant_nn_classes_images)
            )
        ).where(
            Plant.plant_id == plant_id
        )
        
        result = await db.execute(stmt)
        plant_data = result.scalars().first()

        if plant_data is None:
            logger.warning(f"Растение с ID '{plant_id}' не найдено в таблице 'plants' БД.")
            return None

        return plant_data
    
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при получении информации о растении для plant_id '{plant_id}': {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении информации о растении для plant_id '{plant_id}': {e}", exc_info=True)
        return None
    

async def get_plant_by_variety(db: AsyncSession, variety_id: int) -> Optional[Plant]:
    """
    Получает информацию о виде растении из БД по ID сорта растения, включая связанные изображения.

    Args:
        db: Асинхронная cессия базы данных SQLAlchemy.
        plant_id: ID растения (plant_id из таблицы plants).

    Returns:
        Словарь с полной информацией о растении.
        Возвращает только те растения, которые были найдены.
    """
    try:
        stmt = select(Plant).options(
            selectinload(Plant.nn_classes).options(
                selectinload(PlantNNClass.plant_nn_classes_images)
                )
            ).join(Plant.nn_classes
               ).where(
                   PlantNNClass.class_id == variety_id
        )
        
        result = await db.execute(stmt)
        plant_data = result.scalars().first()

        if plant_data is None:
            logger.warning(f"Вид растения по сорту ID='{variety_id}' не найдено.")
            return None

        return plant_data
    
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при получении информации о виде растения по сорту ID={variety_id}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении информации о виде растения  по сорту ID={variety_id}: {e}", exc_info=True)
        return None


async def get_diseases_from_db_by_nn(db: AsyncSession, class_labels: List[str]) -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Получает полную информацию о заболеваниях из БД по списку имен классов нейронной сети.

    Args:
        db: Асинхронная сессия базы данных SQLAlchemy.
        class_labels: Список имен классов, предсказанных нейронной сетью (class_label из DiseaseNNClass).

    Returns:
        Словарь, где ключ - class_label, а значение - словарь с полной информацией о заболевании,
        включая 'disease_id' как 'item_id' и 'disease_name_ru' как 'item_name'.
        Возвращает только те заболевания, которые были найдены.
    """
    if not class_labels:
        return None
    
    try:
        # Строим асинхронный запрос для получения DiseaseNNClass объектов
        # и связанных с ними объектов Disease
        stmt = select(DiseaseNNClass).options(
            selectinload(DiseaseNNClass.disease).selectinload(Disease.disease_images)
        ).where(
            DiseaseNNClass.class_label.in_(class_labels)
        )
        
        result = await db.execute(stmt)
        nn_classes_found = result.scalars().unique().all()

        diseases_info_map: Dict[str, Dict[str, Any]] = {}
        for nn_class in nn_classes_found:
            if nn_class.disease:
                disease_data = nn_class.disease

                images_urls = [
                    img.image_url 
                    for img in sorted(disease_data.disease_images, key=lambda x: not x.is_main_image)
                ]

                diseases_info_map[nn_class.class_label] = {
                    "item_id": disease_data.disease_id,
                    "item_name": disease_data.disease_name_ru,
                    "images": images_urls
                }
            else:
                logger.warning(f"Сведения о заболевании не найдены для class_label '{nn_class.class_label}' (disease_id={nn_class.disease_id}).")

        return diseases_info_map

    except Exception as e:
        logger.error(f"Ошибка при получении информации о заболевании для class_labels {class_labels}: {e}", exc_info=True)
        return None


async def get_disease_by_id(db: AsyncSession, disease_id: int) -> Optional[DiseaseWithSymptoms]:
    """
    Получает полную информацию об одном заболевании из БД по его disease_id.
    """
    try:
        stmt = select(Disease).options(
            selectinload(Disease.disease_images), # Изображения
            selectinload(Disease.disease_symptoms) # Связующая таблица
                .selectinload(DiseaseSymptom.symptom) # Затем сам симптом
        ).where(
            Disease.disease_id == disease_id
        )

        result = await db.execute(stmt)
        disease_data = result.scalars().first()

        if disease_data is None:
            logger.warning(f"Заболевание с ID '{disease_id}' не найдено в таблице 'diseases' БД.")
            return None

        return disease_data
    
    except Exception as e:
        logger.error(f"Ошибка при получении информации о заболевании для plant_id '{disease_id}': {e}", exc_info=True)
        return None
    

async def get_soil_type_by_id(db: AsyncSession, soil_type_id: int) -> Optional[SoilType]:
    """Получает тип грунта по его ID."""
    try:
        result = await db.execute(select(SoilType).where(SoilType.soil_type_id == soil_type_id))
        soil_type = result.scalars().first()
        if not soil_type:
            logger.warning(f"Тип грунта с ID {soil_type_id} не найден в БД.")
        else:
            logger.info(f"Тип грунта с ID {soil_type_id} найден.")
        return soil_type
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при поиске типа грунта с ID {soil_type_id}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при поиске типа грунта с ID {soil_type_id}: {e}", exc_info=True)
        return None


async def create_user_plant(db: AsyncSession, user_id: int, plant_data: UserPlantCreate) -> UserPlant:
    """Создает новое растение пользователя в базе данных."""
    try:
        user = await get_user_by_telegram_id(db, user_id)
        if not user:
            raise ValueError(f"Попытка создания растения пользователя для несуществующего пользователя с ID {user_id}.")
        
        variety = await get_variety_by_id(db, plant_data.plant_nn_classes_id)
        if not variety:
            raise ValueError(f"Попытка создания растения пользователя:  plant_nn_classes_id={plant_data.plant_nn_classes_id} не найдено в справочнике.")

        if plant_data.soil_type_id:
            soil_type = await get_soil_type_by_id(db, plant_data.soil_type_id)
            if not soil_type :
                raise ValueError(f"Попытка создания растения пользователя: Тип грунта с ID {plant_data.soil_type_id} не найден.")

        db_user_plant = UserPlant(user_id=user_id, **plant_data.model_dump(exclude_unset=True,  exclude='image_data_uri'))
        db.add(db_user_plant)
        await db.commit()
        await db.refresh(db_user_plant)
        logger.info(f"Растение {db_user_plant.user_plant_id} успешно добавлено пользователю {user_id}.")

        if plant_data.image_data_uri:
            logger.info(f"Обнаружено изображение для добавления к растению пользователя {user_id}.")
            await add_user_plant_image(db, db_user_plant.user_plant_id, plant_data.image_data_uri)
            
        return db_user_plant

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при создании растения пользователя для пользователя {user_id}: {e}", exc_info=True)
        await db.rollback()
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при создании растения пользователя для пользователя {user_id}: {e}", exc_info=True)
        await db.rollback()
        return None
    

async def add_user_plant_image(db: AsyncSession, user_plant_id: int, image_data_uri: str):
    try:
        new_image = UserPlantImage(
            user_plant_id=user_plant_id,
            image_url=image_data_uri,
            description=""
        )
        db.add(new_image)
        await db.commit()
        await db.refresh(new_image)
        return new_image
    except Exception as e:
        logger.error(f"Ошибка при добавлении записи об изображении для user_plant_id={user_plant_id}: {e}", exc_info=True)
        await db.rollback()
        return None


async def get_user_plant_by_id(db: AsyncSession, user_plant_id: int) -> Optional[UserPlant]:
    """Получает растение пользователя по его ID."""
    try:
        result = await db.execute(
            select(UserPlant).where(UserPlant.user_plant_id == user_plant_id)
        )
        user_plant = result.scalars().first()
        if user_plant:
            logger.info(f"Растение пользователя ID={user_plant_id} найдено.")
        else:
            logger.warning(f"Растение пользователя ID={user_plant_id} не найдено.")

        return user_plant
    
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при поиске растения пользователя ID={user_plant_id}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при поиске растения пользователя ID={user_plant_id}: {e}", exc_info=True)
        return None


async def get_user_plant_by_id_and_user_id(db: AsyncSession, user_plant_id: int, user_id: int) -> Optional[UserPlant]:
    """Получает растение пользователя по его ID и ID пользователя, чтобы убедиться в правах доступа."""
    try:
        result = await db.execute(
            select(UserPlant)
            .where(UserPlant.user_plant_id == user_plant_id, UserPlant.user_id == user_id)
        )
        user_plant = result.scalars().first()
        if user_plant:
            logger.info(f"Растение пользователя ID={user_plant_id} для пользователя ID={user_id} найдено.")
        else:
            logger.warning(f"Растение пользователя ID={user_plant_id} для пользователя ID={user_id} не найдено или не принадлежит этому пользователю.")
        return user_plant
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при поиске растения пользователя ID={user_plant_id} для пользователя ID={user_id}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при поиске растения пользователя ID={user_plant_id} для пользователя ID={user_id}: {e}", exc_info=True)
        return None


async def update_user_plant(db: AsyncSession, user_plant: UserPlant, plant_data: UserPlantUpdate) -> Optional[UserPlant]:
    """Обновляет информацию о растении пользователя."""
    try:
        update_data = plant_data.model_dump(exclude_unset=True, exclude='image_data_uri')
        if "soil_type_id" in update_data and update_data["soil_type_id"] is not None:
            soil_type = await get_soil_type_by_id(db, update_data["soil_type_id"])
            if not soil_type:
                logger.warning(f"Попытка обновления растения {user_plant.user_plant_id}: Тип грунта с ID {update_data['soil_type_id']} не найден.")
                return None

        if "plant_nn_classes_id" in update_data and update_data["plant_nn_classes_id"] != user_plant.user_plant_id:
            variety = await get_variety_by_id(db, plant_data.plant_nn_classes_id)
            if not variety:
                logger.warning(f"Попытка обновления растения пользователя {user_plant.user_plant_id}: plant_nn_classes_id={plant_data.plant_nn_classes_id} не найдено в справочнике.")
                return None
        
        # Обновляем только те поля, которые были переданы в plant_data
        # Копируем данные из Pydantic модели в ORM объект
        for field, value in update_data.items():
            setattr(user_plant, field, value)
        
        await db.commit()
        await db.refresh(user_plant)
        logger.info(f"Растение пользователя {user_plant.user_plant_id} успешно обновлено.")

        if plant_data.image_data_uri:
            logger.info(f"Обнаружено изображение для добавления к растению пользователя при обновлении ратсения ID={user_plant.user_plant_id}.")
            await add_user_plant_image(db, user_plant.user_plant_id, plant_data.image_data_uri)

        return user_plant
    
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при обновлении растения пользователя {user_plant.user_plant_id}: {e}", exc_info=True)
        await db.rollback()
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при обновлении растения пользователя {user_plant.user_plant_id}: {e}", exc_info=True)
        await db.rollback()
        return None


async def delete_user_plant_soft(db: AsyncSession, user_plant: UserPlant) -> Optional[UserPlant]:
    """Мягко удаляет растение пользователя (устанавливает флаг deleted=True)."""
    try:
        # Мягко удаляем все связанные задачи
        task_update_stmt = (
            update(Task)
            .values(deleted=True)
            .execution_options(synchronize_session=False)
            .where(Task.user_plant_id == user_plant.user_plant_id)
        )
        result = await db.execute(task_update_stmt)
        logger.info(f"Для мягко удаляемого растения {user_plant.user_plant_id} было мягко удалено {result.rowcount} задач.")

        # Мягко удаляем само растение
        user_plant.deleted = True
        await db.commit()
        await db.refresh(user_plant)
        logger.info(f"Растение пользователя {user_plant.user_plant_id} мягко удалено.")
        
        return user_plant
    
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при мягком удалении растения пользователя {user_plant.user_plant_id}: {e}", exc_info=True)
        await db.rollback()
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при мягком удалении растения пользователя {user_plant.user_plant_id}: {e}", exc_info=True)
        await db.rollback()
        return None


# async def delete_user_plant_hard(db: AsyncSession, user_plant: UserPlant) -> bool:
#     """Жестко удаляет растение пользователя из БД."""
#     try:
#         db.delete(user_plant)
#         await db.commit()
#         logger.info(f"Растение пользователя {user_plant.user_plant_id} жестко удалено.")
#         return True
#     except SQLAlchemyError as e:
#         logger.error(f"SQLAlchemyError при жестком удалении растения пользователя {user_plant.user_plant_id}: {e}", exc_info=True)
#         await db.rollback()
#         return False
#     except Exception as e:
#         logger.error(f"Неожиданная ошибка при жестком удалении растения пользователя {user_plant.user_plant_id}: {e}", exc_info=True)
#         await db.rollback()
#         return False


# Функции для Задач (Task)

async def create_task(db: AsyncSession, user_id: int, task_data: TaskCreate) -> Optional[Task]:
    """Создает новую задачу для пользователя."""
    try:
        user = await get_user_by_telegram_id(db, user_id)
        if not user:
            raise ValueError(f"Попытка создания задачи для несуществующего пользователя ID={user_id}.")

        user_plant = await get_user_plant_by_id_and_user_id(db, task_data.user_plant_id, task_data.user_id)
        if not user_plant:
            raise ValueError(f"Попытка создания задачи: растение пользователя с ID {task_data.user_plant_id} не найдено или не принадлежит пользователю {user_id}.")
        
        task_type_exists = await db.execute(select(TaskType.task_type_id).where(TaskType.task_type_id == task_data.task_type_id))
        if not task_type_exists.scalars().first():
            logger.warning(f"Попытка создания задачи: тип задачи с ID {task_data.task_type_id} не найден.")
            return None

        task_dict = task_data.model_dump(exclude_unset=True)
        task_dict['user_id'] = user_id
        db_task = Task(**task_dict)

        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)
        logger.info(f"Задача {db_task.id} успешно создана для пользователя {user_id}.")
        return db_task
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при создании задачи для пользователя {user_id}: {e}", exc_info=True)
        await db.rollback()
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при создании задачи для пользователя {user_id}: {e}", exc_info=True)
        await db.rollback()
        return None

async def get_task_by_id_and_user_id(db: AsyncSession, task_id: int, user_id: int) -> Optional[Task]:
    """Получает задачу по ID задачи и ID пользователя."""
    try:
        stmt = select(Task).options(
            selectinload(Task.task_type)
        ).where(
            Task.id == task_id,
            Task.user_id == user_id,
            Task.deleted == False
        )

        result = await db.execute(stmt)
        task = result.scalars().first()
        if task:
            logger.info(f"Задача {task_id} успешно получена для пользователя {user_id}.")
        else:
            logger.warning(f"Задача {task_id} не найдена или не принадлежит пользователю {user_id}.")
        return task
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при получении задачи {task_id}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении задачи {task_id}: {e}", exc_info=True)
        return None


async def get_tasks_for_date(db: AsyncSession, user_id: int, target_date: date) -> Optional[List[Task]]:
    """Получает все задачи пользователя на определенный день."""
    try:
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())

        stmt = select(Task).options(
            selectinload(Task.task_type)
        ).where(
            Task.user_id == user_id,
            Task.due_date.between(start_of_day, end_of_day),
            Task.deleted == False
        ).order_by(Task.due_date)
        
        result = await db.execute(stmt)
        tasks = result.scalars().all()
        logger.info(f"Найдено {len(tasks)} задач для пользователя {user_id} на дату {target_date}.")
        return tasks
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при получении задач для пользователя {user_id} на дату {target_date}: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении задач для пользователя {user_id} на дату {target_date}: {e}", exc_info=True)
        return []


async def get_tasks_for_week(db: AsyncSession, user_id: int, start_date: date) -> Optional[List[Task]]:
    """Получает все задачи пользователя на неделю, начиная с указанной даты."""
    try:
        start_of_week = datetime.combine(start_date, datetime.min.time())
        end_of_week = datetime.combine(start_date + timedelta(days=6), datetime.max.time())

        stmt = select(Task).options(
            selectinload(Task.task_type)
        ).where(
            Task.user_id == user_id,
            Task.due_date.between(start_of_week, end_of_week),
            Task.deleted == False
        ).order_by(Task.due_date)
        
        result = await db.execute(stmt)
        tasks = result.scalars().all()
        logger.info(f"Найдено {len(tasks)} задач для пользователя {user_id} на неделю с {start_date}.")
        return tasks
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при получении задач для пользователя {user_id} на неделю с {start_date}: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении задач для пользователя {user_id} на неделю с {start_date}: {e}", exc_info=True)
        return []


async def get_all_user_tasks_paginated(
    db: AsyncSession, 
    user_id: int, 
    page: int = 1, 
    per_page: int = 50,
    is_completed: Optional[bool] = None,
    user_plant_id: Optional[int] = None
) -> Dict[str, Any]:
    """Получает все задачи пользователя с пагинацией и фильтрацией."""
    try:
        offset = (page - 1) * per_page
        
        query = select(Task).where(
            Task.user_id == user_id,
            Task.deleted == False
        )
        
        if is_completed is not None:
            query = query.where(Task.is_completed == is_completed)
        
        if user_plant_id is not None:
            query = query.where(Task.user_plant_id == user_plant_id)

        # Подсчет общего количества задач
        total_tasks_stmt = select(func.count()).select_from(Task).where(
            Task.user_id == user_id,
            Task.deleted == False
        )
        if is_completed is not None:
            total_tasks_stmt = total_tasks_stmt.where(Task.is_completed == is_completed)
        if user_plant_id is not None:
            total_tasks_stmt = total_tasks_stmt.where(Task.user_plant_id == user_plant_id)
        
        total_tasks_result = await db.execute(total_tasks_stmt)
        total_tasks = total_tasks_result.scalar_one()

        # Загрузка задач с пагинацией
        tasks_stmt = query.options(
            selectinload(Task.task_type)
        ).order_by(Task.due_date).offset(offset).limit(per_page)
        
        tasks_result = await db.execute(tasks_stmt)
        tasks = tasks_result.scalars().all()
        
        total_pages = (total_tasks + per_page - 1) // per_page
        
        logger.info(f"Получено {len(tasks)} задач для пользователя {user_id} (страница {page}/{total_pages}).")
        return {
            "tasks": tasks,
            "total": total_tasks,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при получении пагинированного списка задач для пользователя {user_id}: {e}", exc_info=True)
        return {"tasks": [], "total": 0, "page": page, "per_page": per_page, "total_pages": 0}
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении пагинированного списка задач для пользователя {user_id}: {e}", exc_info=True)
        return {"tasks": [], "total": 0, "page": page, "per_page": per_page, "total_pages": 0}


async def update_task(db: AsyncSession, task_obj: Task, task_data: TaskUpdate) -> Optional[Task]:
    """Обновляет существующую задачу."""
    try:
        # Проверяем, что, если user_plant_id или task_type_id изменяются, они существуют
        if task_data.user_plant_id is not None and task_data.user_plant_id != task_obj.user_plant_id:
            user_plant_exists = await get_user_plant_by_id_and_user_id(db, task_data.user_plant_id, task_obj.user_id)
            if not user_plant_exists:
                logger.warning(f"При обновлении задачи {task_obj.id}: растение пользователя с ID {task_data.user_plant_id} не найдено или не принадлежит пользователю {task_obj.user_id}.")
                return None
        
        if task_data.task_type_id is not None and task_data.task_type_id != task_obj.task_type_id:
            task_type_exists = await db.execute(
                select(TaskType.task_type_id).where(TaskType.task_type_id == task_data.task_type_id)
            )
            if not task_type_exists.scalars().first():
                logger.warning(f"При обновлении задачи {task_obj.id}: тип задачи с ID {task_data.task_type_id} не найден.")
                return None

        update_data = task_data.model_dump(exclude_unset=True)
        
        # Специальная обработка для completion_date при изменении is_completed
        if 'is_completed' in update_data:
            if update_data['is_completed']:
                update_data['completion_date'] = datetime.now()
            else:
                update_data['completion_date'] = None
        
        for key, value in update_data.items():
            setattr(task_obj, key, value)
        
        await db.commit()
        await db.refresh(task_obj)
        logger.info(f"Задача {task_obj.id} успешно обновлена.")
        return task_obj
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при обновлении задачи {task_obj.id}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при обновлении задачи {task_obj.id}: {e}", exc_info=True)
        return None


async def mark_task_completed(db: AsyncSession, task_obj: Task) -> Optional[Task]:
    """Отмечает задачу как выполненную."""
    try:
        if task_obj.is_completed:
            logger.info(f"Задача {task_obj.id} уже выполнена.")
            return task_obj

        task_obj.is_completed = True
        task_obj.completion_date = datetime.now()
        
        await db.commit()
        await db.refresh(task_obj)
        logger.info(f"Задача {task_obj.id} отмечена как выполненная.")
        return task_obj
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при отметке задачи {task_obj.id} как выполненной: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при отметке задачи {task_obj.id} как выполненной: {e}", exc_info=True)
        return None


async def unmark_task_completed(db: AsyncSession, task_obj: Task) -> Optional[Task]:
    """Отменяет выполнение задачи."""
    try:
        if not task_obj.is_completed:
            logger.info(f"Задача {task_obj.id} уже не выполнена.")
            return task_obj

        task_obj.is_completed = False
        task_obj.completion_date = None
        
        await db.commit()
        await db.refresh(task_obj)
        logger.info(f"Выполнение задачи {task_obj.id} отменено.")
        return task_obj
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при отмене выполнения задачи {task_obj.id}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при отмене выполнения задачи {task_obj.id}: {e}", exc_info=True)
        return None


async def delete_task_hard(db: AsyncSession, task_obj: Task) -> bool:
    """Полностью удаляет задачу из БД."""
    try:
        db.delete(task_obj)
        await db.commit()
        logger.info(f"Задача {task_obj.id} полностью удалена из БД.")
        return True
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при жестком удалении задачи {task_obj.id}: {e}", exc_info=True)
        await db.rollback()
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка при жестком удалении задачи {task_obj.id}: {e}", exc_info=True)
        await db.rollback()
        return False
import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Optional, Any

from models import Plant, Disease, DiseaseSymptom, PlantNNClass, DiseaseNNClass

logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite+aiosqlite:////app/data/plantastic_db.db"

try:
    engine = create_async_engine(
        DATABASE_URL,
        # connect_args={"check_same_thread": False},
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

# # Зависимость
# def get_db():
#     """Зависимость для получения сессии базы данных"""
#     db = SessionLocal()

#         yield db
#     except SQLAlchemyError as e:
#         logger.error(f"Ошибка БД: {e}")
#         db.rollback()
#         raise HTTPException(status_code=500, detail="Ошибка базы данных")
#     finally:
#         db.close()

# Зависимость FastAPI для получения асинхронной сессии
async def get_async_db():
    """Зависимость для получения сессии базы данных"""
    async with AsyncSessionLocal() as session:
        yield session


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
        return {}
    
    try:
        # Строим асинхронный запрос для получения PlantNNClass объектов
        # и связанных с ними объектов Plant (используя relationship)
        stmt = select(PlantNNClass).filter(
            PlantNNClass.class_label.in_(class_names)
        ).options(
            # быстро загрузить объект Plant и PlantImage, чтобы избежать проблемы N+1
            # (то есть, загружаем Plant и PlantImage сразу, чтобы не делать по одному запросу на каждый PlantNNClass)
            selectinload(PlantNNClass.plant).selectinload(Plant.plant_images) # Цепочка selectinload!
        )
        result = await db.execute(stmt)
        nn_classes_found = result.scalars().unique().all() # .unique() для избежания дубликатов при join

        if nn_classes_found is None:
            logger.warning(f"Классы '{class_names}' не найдены в таблице 'plant_nn_class' БД.")
            return None

        # Используем plant_id как 'item_id' и common_name_ru как 'item_name'
        plants_info_map: Dict[str, Dict[str, Any]] = {}
        for nn_class in nn_classes_found:
            if nn_class.plant: # Убедимся, что связанное растение найдено
                plant_data = nn_class.plant

                # Подготавливаем список адресов изображений
                images_urls = [
                    img.image_url 
                    for img in sorted(plant_data.plant_images, key=lambda x: not x.is_main_image)
                ]
                
                plants_info_map[nn_class.class_label] = {
                    "item_id": plant_data.plant_id,
                    "item_name": plant_data.common_name_ru,
                    "images": images_urls
                }
            else:
                logger.warning(f"Сведения о растении не найдены для класса '{nn_class.class_label}' (plant_id={nn_class.plant_id}).")

        return plants_info_map
    
    except Exception as e:
        logger.error(f"Ошибка при получении информации о растениях для имени классов '{class_names}': {e}")
        return None
    

async def get_plant_by_id(db: AsyncSession, plant_id: List[str]) -> Optional[Dict[str, Any]]:
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
        stmt = select(Plant).filter(Plant.plant_id == plant_id).options(
            selectinload(Plant.plant_images)
        )
        result = await db.execute(stmt)
        plant_data = result.scalars().first()

        if plant_data is None:
            logger.warning(f"Растение с ID '{plant_id}' не найдено в таблице 'plant' БД.")
            return None
        
        # Подготавливаем список адресов изображений
        images_urls = [
            img.image_url 
            for img in sorted(plant_data.plant_images, key=lambda x: not x.is_main_image)
        ]

        result = {
            "plant_id": plant_data.plant_id,
            "common_name_ru": plant_data.common_name_ru,
            "scientific_name": plant_data.scientific_name,
            "synonyms": plant_data.synonyms,
            "family": plant_data.family,
            "genus": plant_data.genus,
            "description": plant_data.description,
            "max_height_cm": plant_data.max_height_cm,
            "growth_rate": plant_data.growth_rate,
            "light_requirements": plant_data.light_requirements,
            "temperature_range": plant_data.temperature_range,
            "humidity_requirements": plant_data.humidity_requirements,
            "soil_requirements": plant_data.soil_requirements,
            "repotting_frequency": plant_data.repotting_frequency,
            "propagation_methods": plant_data.propagation_methods,
            "toxicity": plant_data.toxicity,
            "care_features": plant_data.care_features,
            "watering_frequency": plant_data.watering_frequency,
            "watering_coefficient": plant_data.watering_coefficient,
            # Можно добавить другие связанные данные, если потребуется, например, изображения
            "plant_images": images_urls
        }

        return result
    
    except Exception as e:
        logger.error(f"шибка при получении информации о растении для plant_id '{plant_id}': {e}", exc_info=True)
        return None
    

async def get_diseases_from_db_by_nn(db: AsyncSession, class_labels: List[str]) -> Dict[str, Dict[str, Any]]:
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
        return {}
    
    try:
        # Строим асинхронный запрос для получения DiseaseNNClass объектов
        # и связанных с ними объектов Disease
        stmt = select(DiseaseNNClass).filter(
            DiseaseNNClass.class_label.in_(class_labels)
        ).options(
            selectinload(DiseaseNNClass.disease).selectinload(Disease.disease_images)
        )
        
        result = await db.execute(stmt)
        nn_classes_found = result.scalars().unique().all()

        diseases_info_map: Dict[str, Dict[str, Any]] = {}
        for nn_class in nn_classes_found:
            if nn_class.disease: # Убедимся, что связанное заболевание найдено
                disease_data = nn_class.disease

                # Подготавливаем список адресов изображений
                images_urls = [
                    img.image_url 
                    for img in sorted(disease_data.disease_images, key=lambda x: not x.is_main_image)
                ]

                diseases_info_map[nn_class.class_label] = {
                    "item_id": disease_data.disease_id,
                    "item_name": disease_data.disease_name_ru,
                    # "disease_name_en": disease_data.disease_name_en,
                    # "description": disease_data.description,
                    # "symptoms_description": disease_data.symptoms_description,
                    # "treatment": disease_data.treatment,
                    # "prevention": disease_data.prevention,
                    "images": images_urls
                }
            else:
                logger.warning(f"Сведения о заболевании не найдены для class_label '{nn_class.class_label}' (disease_id={nn_class.disease_id}).")

        return diseases_info_map

    except Exception as e:
        logger.error(f"Ошибка при получении информации о заболевании для class_labels {class_labels}: {e}", exc_info=True)
        return {}


async def get_disease_by_id(db: AsyncSession, disease_id: List[str]) -> Optional[Dict[str, Any]]:
    """
    Получает полную информацию об одном заболевании из БД по его disease_id.
    """
    try:
        stmt = select(Disease).filter(Disease.disease_id == disease_id).options(
            selectinload(Disease.disease_images), # Изображения
            selectinload(Disease.disease_symptoms) # Связующая таблица
                .selectinload(DiseaseSymptom.symptom) # Затем сам симптом
        )
        result = await db.execute(stmt)
        disease_data = result.scalars().first()

        if disease_data is None:
            logger.warning(f"Заболевание с ID '{disease_id}' не найдено в таблице 'diseases' БД.")
            return None
        
        # Подготавливаем список адресов изображений
        images_urls = [
            img.image_url 
            for img in sorted(disease_data.disease_images, key=lambda x: not x.is_main_image)
        ]

        # Подготавливаем список симптомов, проходя через связующую таблицу
        symptoms_list = []
        for ds in disease_data.disease_symptoms:
            if ds.symptom: # Убедимся, что симптом действительно подгружен
                symptoms_list.append(ds.symptom.symptom_name_ru)

        result_dict = {
            "disease_id": disease_data.disease_id,
            "disease_name_ru": disease_data.disease_name_ru,
            "disease_name_en": disease_data.disease_name_en,
            "description": disease_data.description,
            "symptoms_description": disease_data.symptoms_description,
            "treatment": disease_data.treatment,
            "prevention": disease_data.prevention,
            "symptoms": symptoms_list,
            "disease_images": images_urls,
            "disease_symptoms": symptoms_list
            }

        return result_dict
    
    except Exception as e:
        logger.error(f"Ошибка при получении информации о заболевании для plant_id '{disease_id}': {e}", exc_info=True)
        return None
import logging
from fastapi import (FastAPI, Depends, HTTPException, Query, UploadFile, 
                     File, status, Request, Path, Body)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from pydantic_core import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, or_
from datetime import date, timedelta
from typing import List, Dict, Optional, Any
import requests
import os
from contextlib import asynccontextmanager
import hashlib
import re

from plant_detector.plant_detector import PlantDetector
from models import Task, UserPlant, Base, SoilType, Plant, PlantNNClass, TaskType, PlantImage
from schemas import (MessageResponse, UserOut, TelegramInitData, AuthResponse, 
                     PlantOut, DiseaseWithSymptoms, TaskCreate, TaskUpdate, 
                     TaskOut, HealthResponse, PredictItem, IdentifyResponse, 
                     RawClassifierResponse, IdentifyResponse, TaskList, UserPlantOut,
                     UserPlantCreate, UserPlantWithDetails, UserPlantUpdate, 
                     SoilTypeOut, PlantOutForSearch, VarietyOutForSearch, TaskTypeOut,
                     GenusWateringCoefficient, TasksByDate
                     )
from database import (engine, check_db_connection, get_async_db,
                      get_user_by_telegram_id, tg_data_to_user_create, create_new_user,
                      update_user_activity, get_plant_by_id, get_disease_by_id,
                      get_plant_from_db_by_nn, get_diseases_from_db_by_nn,
                      create_user_plant, get_user_plant_by_id_and_user_id,
                      update_user_plant, delete_user_plant_soft, create_task,
                      get_tasks_for_date, get_tasks_grouped_by_date, get_task_by_id_and_user_id,
                      update_task, delete_task_hard, get_all_user_tasks_paginated,
                      mark_task_completed, unmark_task_completed, get_plant_by_variety
                      )
from telegram_validation import TelegramDataValidator

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

telegram_validator: TelegramDataValidator = None
plant_detector = PlantDetector()
security = HTTPBearer()

# Функция для создания базы данных и таблиц
async def create_db_and_tables():
    logger.info("Попытка создания таблиц базы данных...")
    # Используем 'engine.run_sync' для выполнения синхронной операции DDL в асинхронном контексте.
    # 'async with engine.begin() as conn' получает асинхронное соединение и начинает транзакцию.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Таблицы базы данных успешно созданы (или уже существуют).")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram_validator
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не установлен в переменных окружения!")
        raise ValueError("BOT_TOKEN обязателен для работы приложения")
    telegram_validator = TelegramDataValidator(BOT_TOKEN)

    await create_db_and_tables()
    logger.info("FastAPI приложение запущено и готово к работе.")
    yield
    logger.info("FastAPI приложение завершает работу.")


app = FastAPI(
    title="Plantastic Backend API",
    description="API для управления задачами по уходу за растениями",
    version="1.0.0",
    lifespan=lifespan
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://plantastic.space", "https://www.plantastic.space"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Обработчик ошибок валидации Pydantic
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = exc.errors()
    logger.error(f"Ошибка валидации запроса: {details}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": details},
    )

@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    details = exc.errors()
    logger.error(f"Ошибка валидации Pydantic: {details}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


@app.middleware("http")
async def verify_jwt_middleware(request: Request, call_next):
    """
    Промежуточное ПО для проверки JWT токена во всех запросах,
    кроме эндпоинта аутентификации.
    """
    # Эндпоинт аутентификации /auth разрешен без проверки JWT
    # Эндпоинты, разрешенные без проверки JWT
    allowed_paths = [
        "/auth", 
        "/health", 
        "/", 
        "/soil_types/", 
        "/task-types/", 
        "/user", 
        "/genus/", 
        "/variety-search/",
        "/plants-search/",
        "/plants/",
        "/plants/{plant_id}",
        "/plants-by-variety/{variety_id}",
        "/get_disease",
        "/get_disease/{disease_id}",
        "/identify_plant",
        "/identify_disease"
    ]

    is_allowed = False
    for path in allowed_paths:
        if "{" in path and "}" in path: # Если путь содержит параметры
            # Создаем шаблон для регулярного выражения, заменяя {param} на [^/]+
            regex_path = path.replace("{", "(?P<").replace("}", ">[^/]+)")
            if re.match(f"^{regex_path}$", request.url.path):
                is_allowed = True
                break
        elif request.url.path == path: # Для точных совпадений
            is_allowed = True
            break
    
    if is_allowed:
        response = await call_next(request)
        return response
    
    # Для всех остальных эндпоинтов требуем JWT токен
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Отсутствует или неверный заголовок авторизации Bearer.")
    
    token = auth_header.split(" ")[1]
    
    try:
        # Пытаемся верифицировать JWT токен, используя метод экземпляра telegram_validator
        telegram_validator.verify_jwt_token(token)
    except HTTPException as e:
        # Перехватываем HTTPException, выброшенные verify_jwt_token
        raise e
    except Exception as e:
        # Для любых других неожиданных ошибок при верификации токена
        raise HTTPException(status_code=500, detail=f"Ошибка при проверке токена в middleware: {str(e)}")
    
    # Продолжаем обработку запроса
    response = await call_next(request)
    return response


# --- Dependency для получения текущего пользователя из JWT ---
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Извлекает JWT токен из заголовка Authorization и верифицирует его.
    Возвращает данные пользователя, если токен действителен.
    """
    token = credentials.credentials
    return telegram_validator.verify_jwt_token(token)


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Hello from backend!",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, summary="Проверка подключения к БД")
async def health_check(db: AsyncSession = Depends(get_async_db)):
    """Проверка подключения к БД"""
    db_connected = await check_db_connection(db)
    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        database_connected=db_connected
    )


# async def validate_telegram_init_data(init_data: str) -> Optional[Dict[str, Any]]:
#     """
#     Валидирует initData от Telegram и возвращает данные пользователя.
    
#     Args:
#         init_data: Строка initData от Telegram WebApp
        
#     Returns:
#         Данные пользователя если валидация прошла успешно, None - если нет
#     """
#     logger.info("Валидация initData от Telegram")

#     if not init_data or not init_data.strip():
#         logger.warning("Получена пустая строка initData")
#         return None
    
#     try:
#         validated_data = telegram_validator.validate_init_data(init_data)
    
#         if validated_data:
#             user_id = validated_data.get('id')
#             if not isinstance(user_id, int) or user_id <= 0:
#                 logger.warning(f"Невалидный user_id: {user_id}")
#                 return None
                
#             logger.info(f"InitData успешно валидирована для пользователя {user_id}")
#             return validated_data
#         else:
#             logger.warning("Валидация initData не прошла")
#             return None
            
#     except Exception as e:
#         logger.error(f"Ошибка при валидации initData: {e}", exc_info=True)
#         return None
    

@app.post("/auth", response_model=AuthResponse, summary="Авторизация пользователя через Telegram")
@limiter.limit("5/minute")
async def telegram_auth(
    request: Request,
    init_data: TelegramInitData,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Авторизация пользователя через валидацию initData от Telegram.
    
    Логика работы:
    1. Валидирует initData от Telegram WebApp
    2. Проверяет, существует ли пользователь с данным Telegram ID
    3. Если не существует - создает нового пользователя
    4. Если существует - обновляет дату активности и загружает дополнительные данные
    5. Возвращает информацию о результате авторизациии
    
    Args:
        init_data: initData от Telegram WebApp
        db: Сессия базы данных
        
    Returns:
        Ответ с результатом авторизации и данными пользователя
    """
    logger.info("Запрос авторизации через Telegram.")

    try:
        # Используем метод telegram_validator.validate_init_data
        validated_user_data = telegram_validator.validate_init_data(init_data.initData)
    except HTTPException as e: # Перехватываем HTTPException, выброшенные из validate_init_data
        logger.warning(f"Валидация initData не прошла: {e.detail}")
        raise e # Перебрасываем HTTPException
    except Exception as e:
        logger.warning(f"Неожиданная ошибка при валидации initData: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера при валидации данных: {e}"
        )

    if validated_user_data is None: # Хотя validate_init_data теперь всегда выбрасывает исключение при неудаче, оставляем для безопасности
        logger.warning("Валидация initData вернула None - отказ в авторизации.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидные данные авторизации от Telegram"
        )
    
    user_id = validated_user_data.get('id')
    if not isinstance(user_id, int) or user_id <= 0:
        logger.warning(f"Невалидный user_id в проверенных данных: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Некорректные данные пользователя из Telegram"
        )

    logger.info(f"InitData валидирована для пользователя с Telegram ID: {user_id}")

    try:
        existing_user = await get_user_by_telegram_id(db, user_id)
        
        if existing_user is None:
            logger.info(f"Пользователь с ID {user_id} не найден. Создаем нового пользователя.")
            user_create_data = tg_data_to_user_create(validated_user_data)
            new_user = await create_new_user(db, user_create_data)
            
            if new_user is None:
                logger.error(f"Не удалось создать пользователя с ID {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Ошибка при создании пользователя"
                )
            user_for_token = validated_user_data
            returned_user_data = UserOut.model_validate(new_user)
            is_new = True
            message_text = "Новый пользователь успешно зарегистрирован"
            
        else:
            logger.info(f"Пользователь с ID {user_id} найден. Обновляем данные.")
            await update_user_activity(db, existing_user)
            user_for_token = validated_user_data
            returned_user_data = UserOut.model_validate(existing_user)
            is_new = False
            message_text = "Пользователь успешно авторизован"
        
        # Создаем JWT токен, используя метод telegram_validator
        access_token = telegram_validator.create_jwt_token(user_for_token)
        
        logger.info(f"Пользователь с ID {user_id} успешно авторизован. Токен выдан.")
        return AuthResponse(
            success=True,
            message=message_text,
            is_new_user=is_new,
            user_data=returned_user_data,
            access_token=access_token, # Возвращаем JWT токен
            token_type="bearer"
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при авторизации пользователя {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера при авторизации"
        )

@app.get("/user")
async def get_user():
    logger.info("DEBUG: Эндпоинт user был вызван.")
    return {"message": "Укажите id пользователя (/user/{user_id})"}


@app.get("/users/{user_id}", response_model=UserOut, summary="Получить информацию о пользователе")
async def get_user_info(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Получить полную информацию о пользователе по его Telegram ID.
    
    Args:
        user_id: Telegram ID пользователя
        db: Сессия базы данных
        
    Returns:
        Информация о пользователе
    """
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен. Вы можете просматривать только свою информацию.")

    logger.info(f"Запрос информации о пользователе с ID: {user_id}")
    
    user = await get_user_by_telegram_id(db, user_id)
    
    if user is None:
        logger.warning(f"Пользователь с ID {user_id} не найден.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    logger.info(f"Информация о пользователе с ID {user_id} успешно получена.")
    return user


@app.get("/plants-search/",
    response_model=List[PlantOutForSearch],
    summary="Список всех растений с возможностью поиска"
)
async def get_plants_search(
    search: Optional[str] = Query(None, description="Поиск по названию/синонимам"),
    db: AsyncSession = Depends(get_async_db)
):
    logger.info(f"Запрос краткой информации о растениях. Поиск по строке: {search}.")

    try:
        plant_query = select(Plant)

        if search:
            search_variations = [
                f"%{search}%",
                f"%{search.lower()}%", 
                f"%{search.upper()}%",
                f"%{search.capitalize()}%"
            ]
            
            conditions = []
            for pattern in search_variations:
                conditions.extend([
                    Plant.scientific_name.like(pattern),
                    Plant.common_name_ru.like(pattern),
                    Plant.synonyms.like(pattern)
                ])
            
            plant_query = plant_query.filter(or_(*conditions))

        plant_result = await db.execute(plant_query)
        plants = plant_result.scalars().all()
        
        plants_with_images = []
        for plant in plants:
            image_query = select(PlantImage.image_url).join(
                PlantNNClass, PlantImage.plant_nn_classes_id == PlantNNClass.class_id
            ).where(
                PlantNNClass.plant_id == plant.plant_id
            ).order_by(
                PlantImage.is_main_image.desc(),
                PlantImage.image_id.asc()
            ).limit(1)
            
            image_result = await db.execute(image_query)
            image_url = image_result.scalar_one_or_none()
            
            plant_data = {
                "plant_id": plant.plant_id,
                "scientific_name": plant.scientific_name,
                "common_name_ru": plant.common_name_ru,
                "synonyms": plant.synonyms,
                "representative_image": image_url
            }
            plants_with_images.append(plant_data)
        
        logger.info(f"Найдено {len(plants_with_images)} растений с краткой информацией.")
        return plants_with_images
    
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при поиске / получении списка растений с краткой информацией: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка базы данных при получении растений.")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при поиске / получении списка растений с краткой информацией: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера.")


@app.get("/genus/",
    response_model=List[GenusWateringCoefficient],
    summary="Список родов растений с коэффициентом потребления воды"
)
async def get_genus(
    db: AsyncSession = Depends(get_async_db)
):
    logger.info(f"Запрос списка родов растений.")
    query = select(Plant.genus, Plant.watering_coefficient).distinct()

    try:
        result = await db.execute(query)
        genus_tuples = result.fetchall()
        logger.info(f"Найдено {len(genus_tuples)} уникальных пар рода и коэффициента полива.")
        return genus_tuples
    
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError получении списка родов растений с коэффициентом потребления водый: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка базы данных при получении списка родов растений с коэффициентом потребления водый.")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении списка родов растений с коэффициентом потребления водый: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера.")


@app.get("/plants/",
    response_model=List[PlantOut],
    summary="Список всех растений с детальной информацией и возможностью поиска"
)
async def get_plants_detail(
    search: Optional[str] = Query(None, description="Поиск по названию/синонимам"),
    db: AsyncSession = Depends(get_async_db)
):
    logger.info(f"Запрос детальной информации о сортах растений. Поиск по строке: {search}.")
    query = select(Plant)
    
    if search:
        search_variations = [
            f"%{search}%",
            f"%{search.lower()}%", 
            f"%{search.upper()}%",
            f"%{search.capitalize()}%"
        ]
        
        conditions = []
        for pattern in search_variations:
            conditions.extend([
                Plant.scientific_name.like(pattern),
                Plant.common_name_ru.like(pattern),
                Plant.synonyms.like(pattern)
            ])
        
        query = query.filter(or_(*conditions))

    query = query.options(
        selectinload(Plant.nn_classes).options(
            selectinload(PlantNNClass.plant_nn_classes_images)
        )
    )

    try:
        result = await db.execute(query)
        plants_detail = result.scalars().all()
        logger.info(f"Найдено {len(plants_detail)} растений с детальной информацией.")
        return plants_detail
    
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при поиске / получении списка растений с детальной информацией: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка базы данных при получении растений.")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при поиске / получении списка растений с детальной информацией: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера.")


@app.get("/plants/{plant_id}", response_model=PlantOut, summary="Получить полную информацию о растении по ID")
async def get_plant_details(
    plant_id: int, 
    db: AsyncSession = Depends(get_async_db)
    ):
    """
    Получить полную информацию о растении по его ID.
    """
    logger.info(f"Запрос информации о растении с ID: {plant_id}")
    plant_info = await get_plant_by_id(db, plant_id)
    
    if plant_info is None:
        logger.warning(f"Растение с ID {plant_id} не найдено.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Растение не найдено")
    
    logger.info(f"Информация о растении с ID {plant_id} успешно получена.")
    return plant_info


@app.get("/plants-by-variety/{variety_id}", response_model=PlantOut, summary="Получить полную информацию о виде растении по ID сорта растения")
async def get_plant_by_variety_endpoint(
    variety_id: int, 
    db: AsyncSession = Depends(get_async_db)
):
    """
    Получить полную информацию о виде растении по ID сорта растения.
    """
    logger.info(f"Запрос информации о виде растения по сорту растения ID=: {variety_id}")
    plant_info = await get_plant_by_variety(db, variety_id)
    
    if plant_info is None:
        logger.warning(f"Вид растения по сорту ID={variety_id} не найдено.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Вид растения не найден")
    
    logger.info(f"Информация о виде растения по сорту ID={variety_id} успешно получена.")
    return plant_info


@app.get("/variety-search/",
    response_model=List[VarietyOutForSearch],
    summary="Список всех сортов растений с возможностью поиска"
)
async def get_variety_search(
    search: Optional[str] = Query(None, description="Поиск по сортам"),
    db: AsyncSession = Depends(get_async_db)
):
    logger.info(f"Запрос краткой информации о сортах растений. Поиск по строке: {search}.")
    query = select(PlantNNClass)

    if search:
        search_variations = [
            f"%{search}%",
            f"%{search.lower()}%", 
            f"%{search.upper()}%",
            f"%{search.capitalize()}%"
        ]
        
        conditions = []
        for pattern in search_variations:
            conditions.extend([
                PlantNNClass.variety_name.like(pattern),
                PlantNNClass.class_label.like(pattern)
            ])
        
        query = query.filter(or_(*conditions))

    try:
        result = await db.execute(query)
        variety_detail = result.scalars().all()
        logger.info(f"Найдено {len(variety_detail)} растений с краткой информацией.")
        return variety_detail
    
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при поиске / получении списка сортов растений с краткой информацией: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка базы данных при получении растений.")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при поиске / получении списка сортов растений с краткой информацией: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера.")


@app.post("/identify_plant", response_model=IdentifyResponse,  summary="Идентификация растения по изображению")
@limiter.limit("10/minute")
async def identify_plant(
    request: Request,
    file: UploadFile = File(...), 
    db: AsyncSession = Depends(get_async_db)
):
    
    try:
        contents = await file.read()

        if not plant_detector.predict(contents):
            logger.info("На поступившем изображении не обнаружено растение")
            return IdentifyResponse(
                                    status="not plant",
                                    data=[],
                                    total=0
                                )
        
        classifier_response = requests.post("http://classifier:8001/classifier/classify",
                                files={"file": (file.filename, contents, file.content_type)},
                                timeout=7)
        classifier_response.raise_for_status() # Вызывает HTTPError для плохих ответов (4xx или 5xx)
        raw_classifier_data = RawClassifierResponse.model_validate(classifier_response.json())

        # Собираем все class_label из предсказаний для одного запроса к БД
        class_labels_to_fetch = [pred.class_name for pred in raw_classifier_data.data.predictions]

        # Выполняем ОДИН асинхронный запрос к базе данных (Если список пуст, функция вернет пустой словарь)
        plants_full_info_map = await get_plant_from_db_by_nn(db, class_labels_to_fetch)

        processed_predictions: List[PredictItem] = []
        for raw_pred in raw_classifier_data.data.predictions:
            class_name = raw_pred.class_name
            confidence = round(raw_pred.confidence * 100, 2) # Переводим в проценты
            
            plant_info = plants_full_info_map.get(class_name)
            
            if plant_info:
                    processed_predictions.append(
                        PredictItem(
                            item_id=plant_info["item_id"],
                            item_name=plant_info["item_name"],
                            confidence=confidence,
                            images=plant_info.get("images", []) # Передаем полученные изображения
                        )
                    )
            else:
                logger.warning(f"Не найдено растения для класса: {class_name}. Добавлено как 'Неизвестное растение ...'")
                processed_predictions.append(
                    PredictItem(
                        item_id=0,
                        item_name=f"Неизвестное растение, класс: {class_name}",
                        confidence=confidence,
                        images=[]
                    )
                )

        # Формируем и возвращаем окончательный ответ
        response_data_object = IdentifyResponse(
                                    status="ok",
                                    data=processed_predictions,
                                    total=len(processed_predictions),
                                )
        return response_data_object

    except requests.exceptions.ConnectionError:
        logger.error("Сервис классификации растений недоступен..", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Сервис классификации расстений недоступен.")
    except requests.exceptions.RequestException as e:
        status_code = classifier_response.status_code if 'classifier_response' in locals() else 500
        logger.error(f"Ошибка из сервиса классификации расстений: {e}. Response: {classifier_response.text if 'classifier_response' in locals() else 'N/A'}", exc_info=True)
        raise HTTPException(status_code=status_code, detail=f"Ошибка из сервиса классификации расстений: {e}. Response: {classifier_response.text if 'classifier_response' in locals() else 'N/A'}")
    except Exception as e:
        logger.error(f"Произошла непредвиденная ошибка в сервисе распознавания растений: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Произошла непредвиденная ошибка: {e}")


@app.get("/get_disease")
async def get_disease():
    logger.info("DEBUG: Эндпоинт get_disease был вызван.")
    return {"message": "Укажите id заболеваниия (/get_disease/{disease_id})"}


@app.get("/get_disease/{disease_id}", response_model=DiseaseWithSymptoms, summary="Получить полную информацию о заболевании по ID")
async def get_disease_details(
    disease_id: int, 
    db: AsyncSession = Depends(get_async_db),
):
    logger.info(f"Запрос информации о заболевании с ID: {disease_id}")
    disease_info = await get_disease_by_id(db, disease_id)
    
    if disease_info is None:
        logger.warning(f"Заболевание с ID {disease_id} не найдено.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заболевание не найдено")
    
    logger.info(f"Информация о заболевании с ID {disease_id} успешно получена.")
    return disease_info


@app.post("/identify_disease", response_model=IdentifyResponse, summary="Идентификация заболевания по изображению")
@limiter.limit("10/minute")
async def identify_disease(
    request: Request,
    file: UploadFile = File(...), 
    db: AsyncSession = Depends(get_async_db)
):
    try:
        contents = await file.read()
        if not plant_detector.predict(contents):
            logger.info("На поступившем изображении не обнаружено растение")
            return IdentifyResponse(
                                    status="not plant",
                                    data=[],
                                    total=0
                                )

        disease_response = requests.post("http://disease:8002/disease/predict",
                                files={"file": (file.filename, contents, file.content_type)},
                                timeout=7)
        disease_response.raise_for_status() # Вызывает HTTPError для плохих ответов (4xx или 5xx)
        raw_disease_data = RawClassifierResponse.model_validate(disease_response.json())

        # Собираем все class_label из предсказаний для одного запроса к БД
        class_labels_to_fetch = [pred.class_name for pred in raw_disease_data.data.predictions]

        # Выполняем ОДИН асинхронный запрос к базе данных. Если список пуст, функция вернет пустой словарь)
        diseases_full_info_map = await get_diseases_from_db_by_nn(db, class_labels_to_fetch)

        processed_predictions: List[PredictItem] = []
        for raw_pred in raw_disease_data.data.predictions:
            class_name = raw_pred.class_name
            confidence = round(raw_pred.confidence * 100, 2)
            
            disease_info = diseases_full_info_map.get(class_name)
            
            if disease_info:
                    processed_predictions.append(
                        PredictItem(
                            item_id=disease_info["item_id"],
                            item_name=disease_info["item_name"],
                            confidence=confidence,
                            images=disease_info.get("images", [])
                        )
                    )
            else:
                logger.warning(f"Не найдено заболевания для метки: {class_name}. Добавлено как 'Неизвестное заболевание ...'.")
                processed_predictions.append(
                    PredictItem(
                        item_id=0,
                        item_name=f"Неизвестное заболевание, метка: {class_name}",
                        confidence=confidence,
                        images=[]
                    )
                )
            
        response_data_object = IdentifyResponse(
                                    status="ok",
                                    data=processed_predictions,
                                    total=len(processed_predictions),
                                )
        return response_data_object

    except requests.exceptions.ConnectionError:
        logger.error("Сервис классификации заболеваний недоступен..", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Сервис классификации заболеваний недоступен.")
    except requests.exceptions.RequestException as e:
        status_code = disease_response.status_code if 'disease_response' in locals() else 500
        logger.error(f"Ошибка из сервиса классификации заболеваний: {e}. Response: {disease_response.text if 'disease_response' in locals() else 'N/A'}", exc_info=True)
        raise HTTPException(status_code=status_code, detail=f"Ошибка из сервиса классификации заболеваний: {e}. Response: {disease_response.text if 'disease_response' in locals() else 'N/A'}")
    except Exception as e:
        logger.error(f"В файле identify_disease произошла непредвиденная ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Произошла непредвиденная ошибка: {e}")



@app.post(
    "/users/{user_id}/add_user_plant/",
    response_model=UserPlantOut,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить новое растение пользователю"
)
async def add_user_plant(
    user_id: int = Path(..., description="ID пользователя, которому добавляется растение"),
    plant_data: UserPlantCreate = Body(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Добавляет новое растение в коллекцию пользователя.
    
    Args:
        user_id: Telegram ID пользователя.
        plant_data: Данные для создания растения пользователя.
        db: Сессия базы данных.
        
    Returns:
        Созданное растение пользователя.
    
    Raises:
        HTTPException 404: Если пользователь, растение или тип грунта не найдены.
        HTTPException 500: При внутренней ошибке сервера.
    """
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен. Вы можете добавлять растения только себе.")

    logger.info(f"Получен запрос на добавление растения для пользователя {user_id}: {plant_data.model_dump_json(exclude='image_data_uri')}")
    
    new_plant = await create_user_plant(db, user_id, plant_data)
    
    if new_plant is None:
        logger.warning(f"Не удалось добавить растение для пользователя {user_id} (проверьте логи database.py).")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Не удалось добавить растение. Возможно, пользователь, растение или тип грунта не найдены."
        )

    logger.info(f"Растение user_plant_id={new_plant.user_plant_id} успешно добавлено пользователю {user_id}.")

    query = select(UserPlant).options(
        selectinload(UserPlant.user_plant_images),
    ).where(
        UserPlant.user_plant_id == new_plant.user_plant_id
    )
    try:
        result = await db.execute(query)
        user_plants = result.scalars().first()
        return user_plants
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при получении растения для пользователя {user_id} после создания нового растения пользователя: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка базы данных при получении растения после создания нового растения пользователя.")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении растения для пользователя {user_id} после создания нового растения пользователя: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера.")


@app.get(
    "/users/{user_id}/plants/",
    response_model=List[UserPlantWithDetails],
    summary="Получить список растений пользователя"
)
async def get_user_plants_list(
    user_id: int = Path(..., description="ID пользователя, чьи растения нужно получить"),
    db: AsyncSession = Depends(get_async_db),
    include_deleted: bool = Query(default=False, description="Включить мягко удаленные растения в список"),
    current_user: dict = Depends(get_current_user)
):
    """
    Получает список всех растений, принадлежащих пользователю.
    
    Args:
        user_id: ID пользователя.
        db: Сессия базы данных.
        include_deleted: Включить ли мягко удаленные растения.
        
    Returns:
        Список растений пользователя.
    
    Raises:
        HTTPException 404: Если пользователь не найден.
    """
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен. Вы можете просматривать только свои растения.")

    logger.info(f"Запрос списка растений для пользователя {user_id}. Включать удаленные: {include_deleted}")
    
    # Проверяем существование пользователя
    user_exists = await get_user_by_telegram_id(db, user_id)
    if not user_exists:
        logger.warning(f"Пользователь с ID {user_id} не найден при запросе растений.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    query = select(UserPlant).options(
        selectinload(UserPlant.plant_nn_classes).options(
            selectinload(PlantNNClass.plant),
        ),
        selectinload(UserPlant.user_plant_images),
        selectinload(UserPlant.soil)
    ).where(
        UserPlant.user_id == user_id
    )

    if not include_deleted:
        query = query.where(UserPlant.deleted == False) # Исключаем мягко удаленные

    try:
        result = await db.execute(query)
        user_plants = result.scalars().all()
        
        logger.info(f"Найдено {len(user_plants)} растений для пользователя {user_id}.")
        return user_plants
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при получении списка растений для пользователя {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка базы данных при получении растений.")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении списка растений для пользователя {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера.")


@app.get(
    "/users/{user_id}/plants/{user_plant_id}",
    response_model=UserPlantWithDetails,
    summary="Получить детальную информацию о растении пользователя"
)
async def get_user_plant_details(
    user_id: int = Path(..., description="ID пользователя-владельца растения"),
    user_plant_id: int = Path(..., description="ID конкретного растения пользователя"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Получает детальную информацию о конкретном растении пользователя, включая данные из справочников (Plant, SoilType).
    
    Args:
        user_id: ID пользователя для проверки прав доступа.
        user_plant_id: ID растения пользователя.
        db: Сессия базы данных.
        
    Returns:
        Детальная информация о растении пользователя.
        
    Raises:
        HTTPException 404: Если растение не найдено или принадлежит другому пользователю.
        HTTPException 500: При внутренней ошибке сервера.
    """
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен. Вы можете просматривать только свои растения.")

    logger.info(f"Запрос детальной информации о растении user_plant_id={user_plant_id} пользователя {user_id}")
    
    # Загружаем UserPlant с связанными объектами Plant и SoilType
    try:
        result = await db.execute(
            select(UserPlant)
            .filter(UserPlant.user_plant_id == user_plant_id, UserPlant.user_id == user_id)
            .options(
                selectinload(UserPlant.plant_nn_classes).options(
                    selectinload(PlantNNClass.plant),
                ),
                selectinload(UserPlant.user_plant_images),
                selectinload(UserPlant.soil)
            )
        )
        user_plant = result.scalars().first()
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при получении деталей растения user_plant_id={user_plant_id} для пользователя {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка базы данных при получении деталей растения.")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении деталей растения user_plant_id={user_plant_id} для пользователя {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера.")
    
    if not user_plant:
        logger.warning(f"Растение пользователя user_plant_id={user_plant_id} для пользователя {user_id} не найдено или у пользователя нет прав доступа.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Растение не найдено или у вас нет прав доступа")
    
    logger.info(f"Детали растения user_plant_id={user_plant_id} успешно получены.")
    return user_plant


@app.put(
    "/users/{user_id}/plants/{user_plant_id}",
    response_model=UserPlantOut,
    summary="Обновить информацию о растении пользователя"
)
async def update_user_plant_info(
    user_id: int = Path(..., description="ID пользователя-владельца растения"),
    user_plant_id: int = Path(..., description="ID растения пользователя для обновления"),
    plant_data: UserPlantUpdate = Body(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Обновляет информацию о конкретном растении пользователя.

    Args:
        user_id: ID пользователя для проверки прав доступа.
        user_plant_id: ID растения пользователя.
        plant_data: Данные для обновления.
        db: Сессия базы данных.
        
    Returns:
        Обновленное растение пользователя.
        
    Raises:
        HTTPException 404: Если растение не найдено, принадлежит другому пользователю, или связанный тип грунта не найден.
        HTTPException 500: При внутренней ошибке сервера.
    """
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен. Вы можете обновлять только свои растения.")

    logger.info(f"Получен запрос на обновление растения user_plant_id={user_plant_id} пользователя {user_id} с данными: {plant_data.model_dump_json(exclude='image_data_uri')}")
    
    user_plant = await get_user_plant_by_id_and_user_id(db, user_plant_id, user_id)
    if not user_plant:
        logger.warning(f"Растение пользователя user_plant_id={user_plant_id} для пользователя {user_id} не найдено или у пользователя нет прав доступа.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Растение не найдено или у вас нет прав доступа")
    
    updated_plant = await update_user_plant(db, user_plant, plant_data)
    
    if updated_plant is None:
        logger.warning(f"Не удалось обновить растение user_plant_id={user_plant_id} для пользователя {user_id} (проверьте логи database.py).")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Или 400 Bad Request, в зависимости от причины
            detail="Не удалось обновить растение. Возможно, не выбрано растение или указан некорректный тип грунта."
        )
    
    logger.info(f"Растение user_plant_id={user_plant_id} пользователя {user_id} успешно обновлено.")
    
    query = select(UserPlant).options(
            selectinload(UserPlant.user_plant_images),
        ).where(
            UserPlant.user_plant_id == updated_plant.user_plant_id
        )
    try:
        result = await db.execute(query)
        user_plants = result.scalars().first()
        return user_plants
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при получении растения для пользователя {user_id} после обновления данных о растении пользователя: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка базы данных при получении растений после обновления данных о растении пользователя.")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении растения для пользователя {user_id} после обновления данных о растении пользователя: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера.")


@app.delete(
    "/users/{user_id}/plants/{user_plant_id}",
    response_model=MessageResponse,
    summary="Удалить растение пользователя (мягкое удаление)"
)
async def delete_user_plant(
    user_id: int = Path(..., description="ID пользователя-владельца растения"),
    user_plant_id: int = Path(..., description="ID растения пользователя для удаления"),
    # hard_delete: bool = Query(default=False, description=""), # Если True, выполняет жесткое удаление из БД. Иначе - мягкое (рекомендуется).
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Удаляет растение пользователя.
    
    Args:
        user_id: ID пользователя для проверки прав доступа.
        user_plant_id: ID растения пользователя.
        db: Сессия базы данных.
        
    Returns:
        Сообщение об успешном удалении.
        
    Raises:
        HTTPException 404: Если растение не найдено или принадлежит другому пользователю.
        HTTPException 500: При внутренней ошибке сервера.
    """
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен. Вы можете удалять только свои растения.")

    logger.info(f"Запрос на удаление растения user_plant_id={user_plant_id} пользователя {user_id}.")

    user_plant = await get_user_plant_by_id_and_user_id(db, user_plant_id, user_id)
    if not user_plant:
        logger.warning(f"Растение пользователя user_plant_id={user_plant_id} для пользователя {user_id} не найдено или у пользователя нет прав доступа.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Растение не найдено или у вас нет прав доступа")
    
    success = False
    updated_plant = await delete_user_plant_soft(db, user_plant)
    if updated_plant:
        success = True
    message = f"Растение пользователя user_plant_id={user_plant_id} и все связанные с ним задачи удалены."
    
    if not success:
        logger.error(f"Не удалось удалить растение user_plant_id={user_plant_id} пользователя {user_id}.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при удалении растения.")

    logger.info(message)
    return MessageResponse(message=message, success=True)


@app.post(
    "/users/{user_id}/tasks/",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить новую задачу пользователю"
)
async def add_task(
    user_id: int = Path(..., description="ID пользователя-владельца задачи"),
    task_data: TaskCreate = Body(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Создать новую задачу для пользователя.
    
    Args:
        task_data: Данные для создания задачи
        db: Сессия базы данных
        
    Returns:
        Созданная задача
    """
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен. Вы можете добавлять задачи только себе.")

    logger.info(f"Получен запрос на добавление задачи для пользователя {user_id}: {task_data.model_dump_json()}")

    try:
        new_task = await create_task(db, user_id, task_data)
        if new_task is None:
            logger.warning(f"Не удалось добавить задачу для пользователя {user_id} (проверьте логи database.py).")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Не удалось добавить задачу. Возможно, пользователь, растение пользователя или тип задачи не найдены."
            )

        logger.info(f"Задача {new_task.id} успешно добавлена пользователю {user_id}.")

        return new_task
    
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Неожиданная ошибка при добавлении задачи для пользователя {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла внутренняя ошибка сервера при добавлении задачи."
        )


@app.get(
    "/users/{user_id}/tasks/daily/",
    response_model=List[TaskOut],
    summary="Получить задачи на определенный день"
)
async def get_tasks_for_day(
    user_id: int = Path(..., description="ID пользователя-владельца задач"),
    task_date: Optional[date] = Query(default_factory=date.today, description="Дата (YYYY-MM-DD), для которой нужно получить задачи"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """Получает список всех задач пользователя на указанную дату."""
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен. Вы можете просматривать только свои задачи.")

    logger.info(f"Запрос задач для пользователя {user_id} на дату: {task_date}.")
    try:
        tasks = await get_tasks_for_date(db, user_id, task_date)
        logger.info(f"Найдено {len(tasks)} задач для пользователя {user_id} на {task_date}")

        return tasks
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении задач для пользователя {user_id} на дату {task_date}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла внутренняя ошибка сервера при получении задач на день."
        )


@app.get(
    "/users/{user_id}/tasks/grouped/",
    response_model=List[TasksByDate],
    summary="Получить задачи, сгрупированные по дате"
)
async def get_tasks_grouped_endpoint(
    user_id: int = Path(..., description="ID пользователя-владельца задач"),
    start_date: Optional[date] = Query(default_factory=date.today, description="Начальная дата (YYYY-MM-DD)"),
    days: Optional[int] = Query(7, ge=1, le=50, description="Количество дней (1-31)"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Получает список всех задач пользователя, сгрупированных по дате, начиная с указанной даты (по умолчанию - от сегодня), 
    заканчивая указанной датой (по умолчанию + 6 дней вперед).
    """
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен. Вы можете просматривать только свои задачи.")

    end_date = start_date + timedelta(days=days-1)
    
    logger.info(f"Запрос задач для пользователя {user_id} с {start_date} до {end_date}.")

    try:

        grouped_tasks_dict  = await get_tasks_grouped_by_date(db, user_id, start_date, end_date)

        result = []
        current_date = start_date
        while current_date <= end_date:
            tasks_for_date = grouped_tasks_dict.get(current_date, [])
            result.append(TasksByDate(date=current_date, tasks=tasks_for_date))
            current_date += timedelta(days=1)

        return result
    
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при получении задач для пользователя {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка базы данных при получении задач"
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении задач для пользователя {user_id} с {start_date} до {end_date}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Произошла внутренняя ошибка сервера при получении задач с {start_date} до {end_date}."
        )


@app.get(
    "/users/{user_id}/tasks/{task_id}",
    response_model=TaskOut,
    summary="Получить задачу по ID"
)
async def get_task_by_id(
    user_id: int = Path(..., description="ID пользователя для проверки прав доступа"),
    task_id: int = Path(..., description="ID задачи"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить задачу по ID с проверкой прав доступа"""
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен. Вы можете просматривать только свои задачи.")

    logger.info(f"Запрос информации о задаче {task_id} для пользователя {user_id}.")

    try:
        task = await get_task_by_id_and_user_id(db, task_id, user_id)
        
        if not task:
            logger.warning(f"Задача {task_id} для пользователя {user_id} не найдена или у пользователя нет прав доступа.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Задача не найдена или у вас нет прав доступа"
            )
        logger.info(f"Получена задача {task_id} для пользователя {user_id}")

        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении задачи {task_id} для пользователя {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла внутренняя ошибка сервера при получении задачи."
        )


@app.put(
    "/users/{user_id}/tasks/{task_id}",
    response_model=TaskOut,
    summary="Обновить задачу"
)
async def update_task_endpoint(
    user_id: int = Path(..., description="ID пользователя для проверки прав доступа"),
    task_id: int = Path(..., description="ID задачи для обновления"),
    task_data: TaskUpdate = Body(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """Обновляет информацию о конкретной задаче пользователя."""
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен. Вы можете обновлять только свои задачи.")

    logger.info(f"Получен запрос на обновление задачи {task_id} пользователя {user_id} с данными: {task_data.model_dump_json()}")
    try:
        task_obj = await get_task_by_id_and_user_id(db, task_id, user_id)

        if not task_obj:
            logger.warning(f"Задача {task_id} для пользователя {user_id} не найдена или у пользователя нет прав доступа.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Задача не найдена или у вас нет прав доступа"
            )
        
        updated_task = await update_task(db, task_obj, task_data)
        
        if updated_task is None:
            logger.warning(f"Не удалось обновить задачу {task_id} для пользователя {user_id} (проверьте логи database.py).")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось обновить задачу. Возможно, связанное растение или тип задачи не найдены."
            )

        logger.info(f"Обновлена задача ID: {task_id} для пользователя {user_id}")
        return updated_task
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при обновлении задачи {task_id} для пользователя {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла внутренняя ошибка сервера при обновлении задачи."
        )


@app.delete(
    "/users/{user_id}/tasks/{task_id}",
    response_model=MessageResponse,
    summary="Удалить задачу"
)
async def delete_task_endpoint(
    user_id: int = Path(..., description="ID пользователя для проверки прав доступа"),
    task_id: int = Path(..., description="ID задачи для удаления"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """Удалить задачу"""
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен. Вы можете удалять только свои задачи.")

    logger.info(f"Запрос на удаление задачи {task_id} пользователя {user_id}.")
    try:
        task_obj = await get_task_by_id_and_user_id(db, task_id, user_id)

        if not task_obj:
            logger.warning(f"Задача {task_id} для пользователя {user_id} не найдена или у пользователя нет прав доступа.")
            raise HTTPException(    
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Задача не найдена или у вас нет прав доступа"
            )        
        
        success = await delete_task_hard(db, task_obj)

        if not success:
            logger.error(f"Не удалось удалить задачу {task_id} пользователя {user_id}.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при удалении задачи.")

        logger.info(f"Удалена задача ID: {task_id} для пользователя {user_id}")

        return MessageResponse(success=True, message=f"Задача {task_id} успешно удалена.")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при удалении задачи {task_id} для пользователя {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла внутренняя ошибка сервера при удалении задачи."
        )


@app.get(
    "/users/{user_id}/tasks/",
    response_model=TaskList,
    summary="Получить список задач для пользователя с пагинацией"
)
async def get_all_tasks_paginated(
    user_id: int = Path(..., description="ID пользователя, для которого запрашиваются задачи"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(50, ge=1, le=100, description="Количество задач на странице"),
    is_completed: Optional[bool] = Query(None, description="Фильтр по статусу выполнения задачи"),
    user_plant_id: Optional[int] = Query(None, description="Фильтровать по ID растения пользователя"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Получить список задач для указанного пользователя с пагинацией и опциональной фильтрацией.
    """
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен. Вы можете просматривать только свои задачи.")

    logger.info(f"Запрос всех задач для пользователя {user_id}. Страница: {page}, на страницу: {per_page}, Выполнено: {is_completed}, Растение user_plant_id={user_plant_id}")
    try:
        tasks_data = await get_all_user_tasks_paginated(db, user_id, page, per_page, is_completed, user_plant_id)
        
        if not tasks_data["tasks"] and tasks_data["total"] > 0:
            logger.warning(f"Страница {page} пуста для пользователя {user_id}, но всего задач: {tasks_data['total']}.")

        return tasks_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении пагинированного списка задач для пользователя {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла внутренняя ошибка сервера при получении списка задач."
        )


@app.post(
    "/users/{user_id}/tasks/{task_id}/complete",
    response_model=TaskOut, 
    summary='Отметить задачу как выполненную'
)
async def complete_task_endpoint(
    user_id: int = Path(..., description="ID пользователя для проверки прав доступа"),
    task_id: int = Path(..., description="ID задачи для отметки как выполненной"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """Отметить задачу как выполненную"""
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен. Вы можете отмечать только свои задачи.")

    try:
        task_obj = await get_task_by_id_and_user_id(db, task_id, user_id)
        
        if not task_obj:
            logger.warning(f"Задача {task_id} для пользователя {user_id} не найдена или у пользователя нет прав доступа.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задача не найдена или у вас нет прав доступа"
            )
        
        completed_task = await mark_task_completed(db, task_obj)
        if completed_task is None:
            logger.error(f"Не удалось отметить задачу {task_id} как выполненную для пользователя {user_id}.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при отметке задачи как выполненной.")
        
        logger.info(f"Задача {task_id} отмечена как выполненная")

        return completed_task
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при отметке задачи {task_id} как выполненной для пользователя {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла внутренняя ошибка сервера при отметке задачи как выполненной."
        )


@app.post(
    "/users/{user_id}/tasks/{task_id}/uncomplete",
    response_model=TaskOut,
    summary="Отменить выполнение задачи"
)
async def uncomplete_task_endpoint(
    user_id: int = Path(..., description="ID пользователя для проверки прав доступа"),
    task_id: int = Path(..., description="ID задачи для отмены выполнения"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """Отменить выполнение задачи"""
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен. Вы можете отменять выполнение только своих задач.")

    logger.info(f"Запрос на отмену выполнения задачи {task_id} для пользователя {user_id}.")
    try:
        task_obj = await get_task_by_id_and_user_id(db, task_id, user_id)
        
        if not task_obj:
            logger.warning(f"Задача {task_id} для пользователя {user_id} не найдена или у пользователя нет прав доступа.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задача не найдена или у вас нет прав доступа"
            )
        uncompleted_task = await unmark_task_completed(db, task_obj)

        if uncompleted_task is None:
            logger.error(f"Не удалось отменить выполнение задачи {task_id} для пользователя {user_id}.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при отмене выполнения задачи.")
        
        logger.info(f"Выполнение задачи {task_id} отменено")
        return uncompleted_task
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при отмене выполнения задачи {task_id} для пользователя {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла внутренняя ошибка сервера при отмене выполнения задачи."
        )
    

@app.get(
"/soil_types/",
response_model=List[SoilTypeOut],
summary="Получить список типов грунта"
)
async def get_soil_types(
    db: AsyncSession = Depends(get_async_db)
):
    """
    Получает список типов грунта.
    Args:
        None  
    Returns:
        Список типов грунта.
    """
    logger.info(f"Запрос списка типов грунта")
    query = select(SoilType)
   
    try:
        result = await db.execute(query)
        soil_types = result.scalars().all()
        return soil_types
    
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при получении списка типов грунта: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка базы данных при получении типов грунта.")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении списка типов грунта: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера.")


@app.get(
"/task-types/",
response_model=List[TaskTypeOut],
summary="Получить список типов задач"
)
async def get_task_types(
    db: AsyncSession = Depends(get_async_db)
):
    """
    Получает список типов задач.
    Args:
        None
    Returns:
        Список типов грунта.
    """
    logger.info(f"Запрос списка типов задач")
    query = select(TaskType)
   
    try:
        result = await db.execute(query)
        task_types = result.scalars().all()
        return task_types
    
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError при получении списка задач: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка базы данных при получении типов задач.")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении списка типов задач: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера.")
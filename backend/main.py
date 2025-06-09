import logging
from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic_core import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from datetime import date, timedelta, datetime
from contextlib import asynccontextmanager
from typing import List
import requests

from models import Task, Base
from schemas import (PlantOut, DiseaseWithSymptoms, TaskCreate, TaskUpdate, TaskOut, TaskList, HealthResponse, 
                     PredictItem, IdentifyResponse, RawClassifierResponse,
                     IdentifyResponse)
from database import (engine, check_db_connection, get_async_db,
                      check_db_connection, get_plant_by_id, get_disease_by_id,
                      get_plant_from_db_by_nn, get_diseases_from_db_by_nn)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Plantastic Backend API",
    description="API для управления задачами по уходу за растениями",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://plantastic.space", "https://www.plantastic.space"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Base.metadata.create_all(bind=engine)
# --- Функция для создания базы данных и таблиц ---
async def create_db_and_tables():
    logger.info("Попытка создания таблиц базы данных...")
    # Используем 'engine.run_sync' для выполнения синхронной операции DDL
    # в асинхронном контексте.
    # 'async with engine.begin() as conn' получает асинхронное соединение
    # и начинает транзакцию.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Таблицы базы данных успешно созданы (или уже существуют).")

# --- Обработчик события запуска FastAPI ---
# Эта функция будет вызвана при запуске приложения FastAPI.
@app.on_event("startup")
async def startup_event():
    await create_db_and_tables()


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
        timestamp=datetime.now(),
        database_connected=db_connected
    )


@app.get("/plants/{plant_id}", response_model=PlantOut, summary="Получить полную информацию о растении по ID")
async def get_plant_details(plant_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Получить полную информацию о растении по его ID.
    """
    logger.info(f"Запрос информации о растении с ID: {plant_id}")
    plant_info = await get_plant_by_id(db, plant_id)
    
    if plant_info is None:
        logger.warning(f"Растение с ID {plant_id} не найдено.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Растение не найдено")
    
    logger.info(f"Информация о растении с ID {plant_id} успешно получена.")
    return JSONResponse(content=plant_info, media_type="application/json; charset=utf-8")


@app.post("/identify_plant", response_model=IdentifyResponse,  summary="Идентификация растения по изображению")
async def identify_plant(file: UploadFile = File(...), db: AsyncSession = Depends(get_async_db)):
    try:  
        classifier_response = requests.post("http://classifier:8001/classifier/classify",
                                files={"file": (file.filename, file.file, file.content_type)})
        classifier_response.raise_for_status() # Вызывает HTTPError для плохих ответов (4xx или 5xx)
        raw_classifier_data = RawClassifierResponse.model_validate(classifier_response.json())

        # Собираем все class_label из предсказаний для одного запроса к БД
        class_labels_to_fetch = [pred.class_name for pred in raw_classifier_data.data.predictions]

        # Выполняем ОДИН аси пустонхронный запрос к базе данных
        # (Если список пуст, функция вернетй словарь)
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
                # Если растение не найдено в БД, можно добавить заглушку или пропустить
                logger.warning(f"Не найдено растения для класса: {class_name}. Добавлено как 'Неизвестное растение ...'")
                # Или добавить элемент с "неизвестным" растением:
                processed_predictions.append(
                    PredictItem(
                        item_id=0, # Или другое значение для неизвестного
                        item_name=f"Неизвестное растение, класс: {class_name}",
                        confidence=confidence, # Сохраняем уверенность модели
                        images=[]
                    )
                )
            
            current_time = datetime.now()

            # 4. Формируем и возвращаем окончательный ответ
            response_data_object = IdentifyResponse(
                                        status="ok",
                                        timestamp=current_time,
                                        data=processed_predictions,
                                        total=len(processed_predictions),
                                    )
                
            # return JSONResponse(
            #     content=response_data_object.model_dump(),
            #     media_type="application/json; charset=utf-8"
            # )
            return response_data_object

    except requests.exceptions.ConnectionError:
        logger.error("Сервис классификации растений недоступен..", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Сервис классификации расстений недоступен.")
    except requests.exceptions.RequestException as e:
        status_code = classifier_response.status_code if 'classifier_response' in locals() else 500
        logger.error(f"Ошибка из сервиса классификации расстений: {e}. Response: {classifier_response.text if 'disease_response' in locals() else 'N/A'}", exc_info=True)
        raise HTTPException(status_code=status_code, detail=f"Ошибка из сервиса классификации расстений: {e}. Response: {classifier_response.text if 'classifier_response' in locals() else 'N/A'}")
    except Exception as e:
        logger.error(f"Произошла непредвиденная ошибка в сервисе распознования растений: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Произошла непредвиденная ошибка: {e}")


@app.get("/get_disease")
async def get_disease():
    print("DEBUG: Эндпоинт get_disease был вызван.")
    return {"message": "Укажите id заболеваниия (/get_disease/{disease_id})"}


@app.get("/get_disease/{disease_id}", response_model=DiseaseWithSymptoms, summary="Получить полную информацию о заболевании по ID")
async def get_disease_details(disease_id: int, db: AsyncSession = Depends(get_async_db)):
    logger.info(f"Запрос информации о заболевании с ID: {disease_id}")
    disease_info = await get_disease_by_id(db, disease_id)
    
    if disease_info is None:
        logger.warning(f"Заболевание с ID {disease_id} не найдено.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заболевание не найдено")
    
    logger.info(f"Информация о заболевании с ID {disease_id} успешно получена.")
    return JSONResponse(content=disease_info, media_type="application/json; charset=utf-8")


@app.post("/identify_disease", response_model=IdentifyResponse, summary="Идентификация заболевания по изображению")
async def identify_disease(file: UploadFile = File(...), db: AsyncSession = Depends(get_async_db)):
    try:  
        disease_response = requests.post("http://disease:8002/disease/predict",
                                files={"file": (file.filename, file.file, file.content_type)})
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
            
            current_time = datetime.now()
            response_data_object = IdentifyResponse(
                                        status="ok",
                                        timestamp=current_time,
                                        data=processed_predictions,
                                        total=len(processed_predictions),
                                    )
            
            # return JSONResponse(
            #         content=response_data_object.model_dump(),
            #         media_type="application/json; charset=utf-8"
            #     )
            return response_data_object

    except requests.exceptions.ConnectionError:
        logger.error("Сервис классификации заболеваний недоступен..", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Сервис классификации расстений недоступен.")
    except requests.exceptions.RequestException as e:
        status_code = disease_response.status_code if 'disease_response' in locals() else 500
        logger.error(f"Ошибка из сервиса классификации заболеваний: {e}. Response: {disease_response.text if 'disease_response' in locals() else 'N/A'}", exc_info=True)
        raise HTTPException(status_code=status_code, detail=f"Ошибка из сервиса классификации заболеваний: {e}. Response: {disease_response.text if 'disease_response' in locals() else 'N/A'}")
    except Exception as e:
        logger.error(f"В файле identify_disease произошла непредвиденная ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Произошла непредвиденная ошибка: {e}")


# Добавить задачу
@app.post("/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def add_task(task: TaskCreate, db: AsyncSession = Depends(get_async_db)):
    """Создать новую задачу"""
    try:
        db_task = Task(date=task.date, text=task.text, user_id=task.user_id)
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)
        logger.info(f"Создана задача ID: {db_task.id}")
        return db.query(Task).filter(Task.user_id == task.user_id).all()
    except SQLAlchemyError as e:
        logger.error(f"Ошибка создания задачи: {e}")
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка создания задачи")


# Получить задачи на день
@app.get("/tasks", response_model=list[TaskOut])
async def get_tasks(
    task_date: date = Query(..., description="Дата для получения задач"),
    db: AsyncSession = Depends(get_async_db)
    ):
    """Получить задачи на определенную дату"""
    try:
        result = await db.execute(select(Task).filter(Task.date == task_date))
        tasks = result.scalars().all()
        logger.info(f"Найдено {len(tasks)} задач на {task_date}")
        return tasks
    except SQLAlchemyError as e:
        logger.error(f"Ошибка получения задач: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка получения задач")


# Получить задачи на неделю (от сегодня)
@app.get("/tasks/week", response_model=list[TaskOut])
async def get_week_tasks(db: AsyncSession = Depends(get_async_db)):
    """Получить задачи на неделю от сегодня"""
    try:
        today = date.today()
        next_week = today + timedelta(days=7)
        result = await db.execute(
            select(Task).filter(
                Task.date >= today,
                Task.date <= next_week
            ).order_by(Task.date) # order_by применяется к select
        )
        tasks = result.scalars().all()
        logger.info(f"Найдено {len(tasks)} задач на неделю")
        return tasks
    except SQLAlchemyError as e:
        logger.error(f"Ошибка получения задач на неделю: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка получения задач")
    

@app.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task(task_id: int, db: AsyncSession = Depends(get_async_db)):
    """Получить задачу по ID"""
    try:
        result = await db.execute(select(Task).filter(Task.id == task_id))
        task = result.scalars().first()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
        return task
    except SQLAlchemyError as e:
        logger.error(f"Ошибка получения задачи {task_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка получения задачи")


@app.put("/tasks/{task_id}", response_model=TaskOut)
async def update_task(task_id: int, task_update: TaskUpdate, db: AsyncSession = Depends(get_async_db)):
    """Обновить задачу"""
    try:
        result = await db.execute(select(Task).filter(Task.id == task_id))
        task = result.scalars().first()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
        
        # Обновляем только переданные поля
        if task_update.date is not None:
            task.date = task_update.date
        if task_update.text is not None:
            task.text = task_update.text
            
        await db.commit()
        await db.refresh(task)
        logger.info(f"Обновлена задача ID: {task_id}")
        return task
    except SQLAlchemyError as e:
        logger.error(f"Ошибка обновления задачи {task_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка обновления задачи")


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT) # 204 No Content - для успешного удаления
async def delete_task(task_id: int, db: AsyncSession = Depends(get_async_db)):
    """Удалить задачу"""
    try:
        result = await db.execute(select(Task).filter(Task.id == task_id))
        task = result.scalars().first()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
        
        await db.delete(task)
        await db.commit()
        logger.info(f"Удалена задача ID: {task_id}")
        # return {"message": "Задача удалена"} # Для 204 No Content не нужно возвращать тело ответа
    except SQLAlchemyError as e:
        logger.error(f"Ошибка удаления задачи {task_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка удаления задачи")


# Обработчики ошибок
@app.exception_handler(Exception)
async def custom_exception_handler(request: Request, exc: Exception):
    # Логируем ошибку для отладки
    logger.error(f"Необработанное исключение: {exc}", exc_info=True)

    if isinstance(exc, RequestValidationError):
        # Это ошибка валидации запроса (например, неверные поля в JSON)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, # 422 Unprocessable Entity
            content={"message": "Ошибка валидации данных запроса", "details": exc.errors()}
        )
    elif isinstance(exc, ValidationError):
        # Это ошибка валидации Pydantic модели (например, при создании HealthResponse)
        # В этом случае, это внутренняя ошибка, так как модель HealthResponse не должна быть невалидной
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Ошибка валидации внутренней модели", "details": exc.errors()}
        )
    elif isinstance(exc, HTTPException):
        # Это стандартные ошибки FastAPI (например, 404 Not Found, 400 Bad Request)
        # Здесь можно логирование для 4xx ошибок
        if exc.status_code >= 500:
            logger.error(f"HTTPException: {exc.status_code} - {exc.detail}", exc_info=True)
        else:
            logger.warning(f"HTTPException: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.detail}
        )
    else:
        # Все остальные необработанные исключения
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Произошла внутренняя ошибка сервера."}
        )
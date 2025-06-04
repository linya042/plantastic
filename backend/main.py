import logging

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import date, timedelta, datetime
from fastapi.middleware.cors import CORSMiddleware

from models import Task
from database import SessionLocal, engine,Base, check_db_connection
from schemas import TaskCreate, TaskUpdate, TaskOut, TaskList, HealthResponse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


Base.metadata.create_all(bind=engine)


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

# Зависимость
def get_db():
    """Зависимость для получения сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Ошибка БД: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Ошибка базы данных")
    finally:
        db.close()


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Hello from backend!",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Проверка состояния сервиса"""
    db_connected = check_db_connection()
    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        timestamp=datetime.now(),
        database_connected=db_connected
    )


# Добавить задачу
@app.post("/tasks", response_model=TaskOut, status_code=201)
async def add_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Создать новую задачу"""
    try:
        db_task = Task(date=task.date, text=task.text)
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        logger.info(f"Создана задача ID: {db_task.id}")
        return db_task
    except SQLAlchemyError as e:
        logger.error(f"Ошибка создания задачи: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Ошибка создания задачи")


# Получить задачи на день
@app.get("/tasks", response_model=list[TaskOut])
async def get_tasks(
    task_date: date = Query(..., description="Дата для получения задач"),
    db: Session = Depends(get_db)
    ):
    """Получить задачи на определенную дату"""
    try:
        tasks = db.query(Task).filter(Task.date == task_date).all()
        logger.info(f"Найдено {len(tasks)} задач на {task_date}")
        return tasks
    except SQLAlchemyError as e:
        logger.error(f"Ошибка получения задач: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения задач")


# Получить задачи на неделю (от сегодня)
@app.get("/tasks/week", response_model=list[TaskOut])
async def get_week_tasks(db: Session = Depends(get_db)):
    """Получить задачи на неделю от сегодня"""
    try:
        today = date.today()
        next_week = today + timedelta(days=7)
        tasks =  db.query(Task).filter(
                                    Task.date >= today,
                                    Task.date <= next_week
                                ).order_by(Task.date).all()
        logger.info(f"Найдено {len(tasks)} задач на неделю")
        return tasks
    except SQLAlchemyError as e:
        logger.error(f"Ошибка получения задач на неделю: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения задач")
    

@app.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Получить задачу по ID"""
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        return task
    except SQLAlchemyError as e:
        logger.error(f"Ошибка получения задачи {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения задачи")


@app.put("/tasks/{task_id}", response_model=TaskOut)
async def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Обновить задачу"""
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        
        # Обновляем только переданные поля
        if task_update.date is not None:
            task.date = task_update.date
        if task_update.text is not None:
            task.text = task_update.text
            
        db.commit()
        db.refresh(task)
        logger.info(f"Обновлена задача ID: {task_id}")
        return task
    except SQLAlchemyError as e:
        logger.error(f"Ошибка обновления задачи {task_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Ошибка обновления задачи")


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Удалить задачу"""
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        
        db.delete(task)
        db.commit()
        logger.info(f"Удалена задача ID: {task_id}")
        return {"message": "Задача удалена"}
    except SQLAlchemyError as e:
        logger.error(f"Ошибка удаления задачи {task_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Ошибка удаления задачи")


# Обработчики ошибок
@app.exception_handler(500)
async def internal_server_error(request, exc):
    logger.error(f"Внутренняя ошибка сервера: {exc}")
    return {"error": "Внутренняя ошибка сервера"}


# Событие запуска
@app.on_event("startup")
async def startup_event():
    logger.info("Plantastic Backend запущен")
    if not check_db_connection():
        logger.error("Не удалось подключиться к базе данных!")


# Событие завершения
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Plantastic Backend завершает работу")

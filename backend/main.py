from fastapi import FastAPI,Depends
from sqlalchemy.orm import Session
from datetime import date , timedelta
from models import Task
from fastapi.middleware.cors import CORSMiddleware
from database import SessionLocal, engine,Base
from pydantic import BaseModel
Base.metadata.create_all(bind=engine)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Pydantic схемы
class TaskCreate(BaseModel):
    date: date
    text: str

class TaskOut(BaseModel):
    id: int
    date: date
    text: str

    class Config:
        orm_mode = True

# Зависимость
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Добавить задачу
@app.post("/tasks", response_model=TaskOut)
def add_task(task: TaskCreate, db: Session = Depends(get_db)):
    db_task = Task(date=task.date, text=task.text)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

# Получить задачи на день
@app.get("/tasks", response_model=list[TaskOut])
def get_tasks(date: date, db: Session = Depends(get_db)):
    return db.query(Task).filter(Task.date == date).all()

# Получить задачи на неделю (от сегодня)
@app.get("/tasks/week", response_model=list[TaskOut])
def get_week_tasks(db: Session = Depends(get_db)):
    today = date.today()
    next_week = today + timedelta(days=7)
    return db.query(Task).filter(Task.date >= today, Task.date <= next_week).all()
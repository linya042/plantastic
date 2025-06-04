from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import date, datetime
from typing import Optional

class TaskCreate(BaseModel):
    """Схема для создания новой задачи"""
    task_date: date = Field(..., description="Дата выполнения задачи")
    text: str = Field(..., min_length=1, max_length=1000, description="Описание задачи")
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str):
        """Валидация текста задачи"""
        if not v or not v.strip():
            raise ValueError('Текст задачи не может быть пустым')
        return v.strip()
    
    @field_validator('task_date')
    @classmethod
    def validate_date(cls, v: date):
        """Валидация даты"""
        if v < date.today():
            raise ValueError('Нельзя создать задачу на прошедшую дату')
        return v

class TaskUpdate(BaseModel):
    """Схема для обновления задачи"""
    task_date: Optional[date] = Field(None, description="Новая дата выполнения")
    text: Optional[str] = Field(None, min_length=1, max_length=1000, description="Новое описание задачи")
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Текст задачи не может быть пустым')
            return v.strip() 
        return v
    
    @field_validator('task_date')
    @classmethod
    def validate_date(cls, v: Optional[date]) -> Optional[date]:
        """Валидация даты"""
        if v is not None and v < date.today():
            raise ValueError('Нельзя установить задачу на прошедшую дату')
        return v

class TaskOut(BaseModel):
    """Схема для вывода задачи"""
    id: int
    task_date: date
    text: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class TaskList(BaseModel):
    """Схема для списка задач"""
    tasks: list[TaskOut]
    total: int
    
class HealthResponse(BaseModel):
    """Схема для health check"""
    status: str
    timestamp: datetime
    database_connected: bool
    version: str = "1.0.0"
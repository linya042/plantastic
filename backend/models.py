from sqlalchemy import Column, Integer, String, Date, DateTime, Text
from sqlalchemy.sql import func
from database import Base

class Task(Base):
    """Модель задачи для ухода за растениями"""
    __tablename__='tasks'

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True, nullable=False, comment="Дата выполнения задачи")
    text = Column(String, nullable=False, comment="Описание задачи")

    # Метаданные для аудита@
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Время создания")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="Время последнего обновления")

    def __repr__(self):
        return f"<Task(id={self.id}, date={self.date}, text='{self.text[:50]}...')>"
    
    def __str__(self):
        return f"Задача на {self.date}: {self.text}"
from sqlalchemy import (Column, Integer, String, Date, DateTime, Text, Float,
                        ForeignKey, Boolean, JSON, text)
from sqlalchemy.orm import relationship, declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    user_id = Column('user_id', Integer, primary_key=True)
    first_name = Column('first_name', String)
    username = Column('username', String, unique=True)
    registration_date = Column('registration_date', DateTime)
    last_activity_date = Column('last_activity_date', DateTime)
    timezone = Column('timezone', String)
    settings_json = Column('settings_json', JSON)

    user_plants = relationship("UserPlant", back_populates="user")
    tasks = relationship("Task", back_populates="user")


class Plant(Base):
    __tablename__ = 'plants'

    plant_id = Column('plant_id', Integer, primary_key=True)
    scientific_name = Column('scientific_name', String, nullable=False, unique=True)
    common_name_ru = Column('common_name_ru', String, nullable=False)
    synonyms = Column('synonyms', String)
    family = Column('family', String)
    genus = Column('genus', String)
    description = Column('description', Text)
    max_height_cm = Column('max_height_cm', Integer)
    growth_rate = Column('growth_rate', String)
    light_requirements = Column('light_requirements', String)
    temperature_range = Column('temperature_range', String)
    humidity_requirements = Column('humidity_requirements', String)
    soil_requirements = Column('soil_requirements', String)
    repotting_frequency = Column('repotting_frequency', String)
    propagation_methods = Column('propagation_methods', String)
    toxicity = Column('toxicity', String)
    care_features = Column('care_features', String)
    watering_frequency = Column('watering_frequency', String)
    watering_coefficient = Column('watering_coefficient', Float)

    nn_classes = relationship("PlantNNClass", back_populates="plant")


class PlantImage(Base):
    __tablename__ = 'plant_images'

    image_id = Column('image_id', Integer, primary_key=True, autoincrement=True)
    plant_nn_classes_id = Column('plant_nn_classes_id', Integer, ForeignKey('plant_nn_classes.class_id'))
    image_url = Column('image_url', String, nullable=False)
    description = Column('description', String)
    is_main_image = Column('is_main_image', Boolean, default=False)
    source_url = Column('source_url', String)

    plant_nn_classes = relationship("PlantNNClass", back_populates="plant_nn_classes_images")


class UserPlant(Base):
    __tablename__ = 'user_plants'

    user_plant_id = Column('user_plant_id', Integer, primary_key=True, autoincrement=True)
    user_id = Column('user_id', Integer, ForeignKey('users.user_id'), index=True, nullable=False)
    plant_nn_classes_id = Column('plant_nn_classes_id', Integer, ForeignKey('plant_nn_classes.class_id'), nullable=False)
    nickname = Column('nickname', String)
    acquisition_date = Column('acquisition_date', Date)
    last_watering_date = Column('last_watering_date', Date)
    notes = Column('notes', Text)
    soil_type_id = Column('soil_type_id', Integer, ForeignKey('soil_types.soil_type_id'))
    deleted = Column('deleted', Boolean, default=False)
    created_at = Column(DateTime, server_default=text("STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')"))
    updated_at = Column(DateTime, server_default=text("STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')"), server_onupdate=text("STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')"))  # это поле обновляет триггер в БД

    plant_nn_classes = relationship("PlantNNClass", back_populates="user_plants")
    user = relationship("User", back_populates="user_plants")
    user_plant_images = relationship("UserPlantImage", back_populates="user_plant")
    tasks = relationship("Task", back_populates="user_plant")
    soil = relationship("SoilType", back_populates="user_plants")


class UserPlantImage(Base):
    __tablename__ = 'user_plant_images'

    image_id = Column('image_id', Integer, primary_key=True, autoincrement=True)
    user_plant_id = Column('user_plant_id', Integer, ForeignKey('user_plants.user_plant_id'), index=True, nullable=False)
    image_url = Column('image_url', Text, nullable=False)
    upload_date = Column('upload_date', DateTime, server_default=text("STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')"))
    description = Column('description', String)
    is_main_image = Column('is_main_image', Boolean, default=False)

    user_plant = relationship("UserPlant", back_populates="user_plant_images")


class Disease(Base):
    __tablename__ = 'diseases'

    disease_id = Column('disease_id', Integer, primary_key=True)
    disease_name_ru = Column('disease_name_ru', String, nullable=False)
    disease_name_en = Column('disease_name_en', String)
    description = Column('description', Text)
    symptoms_description = Column('symptoms_description', Text)
    treatment = Column('treatment', Text)
    prevention = Column('prevention', Text)

    disease_images = relationship("DiseaseImage", back_populates="disease")
    disease_symptoms = relationship("DiseaseSymptom", back_populates="disease")
    nn_classes = relationship("DiseaseNNClass", back_populates="disease")


class DiseaseImage(Base):
    __tablename__ = 'disease_images'

    image_id = Column('image_id', Integer, primary_key=True, autoincrement=True)
    disease_id = Column('disease_id', Integer, ForeignKey('diseases.disease_id'), index=True, nullable=False)
    image_url = Column('image_url', String, nullable=False)
    description = Column('description', String)
    is_main_image = Column('is_main_image', Boolean, default=False)
    source_url = Column('source_url', String)

    disease = relationship("Disease", back_populates="disease_images")


class Symptom(Base):
    __tablename__ = 'symptoms'

    symptom_id = Column('symptom_id', Integer, primary_key=True)
    symptom_name_ru = Column('symptom_name_ru', String, unique=True, nullable=False)
    question = Column('question', String, nullable=False)
    symptom_name_en = Column('symptom_name_en', String)

    disease_symptoms = relationship("DiseaseSymptom", back_populates="symptom")


class DiseaseSymptom(Base):
    __tablename__ = 'disease_symptoms'

    disease_symptom_id = Column('disease_symptom_id', Integer, primary_key=True)
    disease_id = Column('disease_id', Integer, ForeignKey('diseases.disease_id'), index=True, nullable=False)
    symptom_id = Column('symptom_id', Integer, ForeignKey('symptoms.symptom_id'), index=True, nullable=False)

    disease = relationship("Disease", back_populates="disease_symptoms")
    symptom = relationship("Symptom", back_populates="disease_symptoms")


class PlantNNClass(Base):
    __tablename__ = 'plant_nn_classes'

    class_id = Column('class_id', Integer, primary_key=True)
    class_label = Column('class_label', String, unique=True, nullable=False)
    plant_id = Column('plant_id', Integer, ForeignKey('plants.plant_id'), index=True, nullable=False)
    variety_name = Column('variety_name', String, nullable=False)

    plant = relationship("Plant", back_populates="nn_classes")
    user_plants = relationship("UserPlant", back_populates="plant_nn_classes")
    plant_nn_classes_images = relationship("PlantImage", back_populates="plant_nn_classes")


class DiseaseNNClass(Base):
    __tablename__ = 'disease_nn_classes'

    class_id = Column('class_id', Integer, primary_key=True)
    class_label = Column('class_label', String, unique=True, nullable=False)
    disease_id = Column('disease_id', Integer, ForeignKey('diseases.disease_id'), index=True, nullable=False)

    disease = relationship("Disease", back_populates="nn_classes")


class TaskType(Base):
    __tablename__ = 'task_types'

    task_type_id = Column('task_type_id', Integer, primary_key=True)
    task_name = Column('task_name', String, unique=True, index=True, nullable=False)
    task_description = Column('task_description', Text)

    tasks = relationship("Task", back_populates="task_type")


class Task(Base):
    """Модель задачи для ухода за растениями"""
    __tablename__='tasks'

    id = Column('id', Integer, primary_key=True, autoincrement=True)
    user_id = Column('user_id', Integer, ForeignKey('users.user_id'), index=True, nullable=False)
    user_plant_id = Column('user_plant_id', Integer, ForeignKey('user_plants.user_plant_id'), index=True, nullable=False)
    task_type_id = Column('task_type_id', Integer, ForeignKey('task_types.task_type_id'), nullable=False)
    due_date = Column('due_date', DateTime, index=True, nullable=False)
    description  = Column('description', Text)
    is_completed = Column('is_completed', Boolean, default=False, index=True)
    completion_date = Column('completion_date', DateTime)
    is_recurring = Column('is_recurring', Boolean, default=False) # Флаг: является ли эта запись "родительской" повторяющейся задачей
    original_task_id = Column('original_task_id', Integer, ForeignKey('tasks.id')) # Самоссылающийся внешний ключ
    recurrence_rule = Column('recurrence_rule', JSON) # JSON-строка для правила повторения
    recurrence_end_date = Column('recurrence_end_date', DateTime) # Дата окончания повторений
    created_at = Column('created_at', DateTime, server_default=text("STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')")) # В SQLAlchemy func.now() обычно достаточно
    updated_at = Column('updated_at', DateTime, server_default=text("STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')"), server_onupdate=text("STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')")) # Триггер в БД будет обновлять это поле
    deleted = Column('deleted', Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="tasks")
    user_plant = relationship("UserPlant", back_populates="tasks")
    task_type = relationship("TaskType", back_populates="tasks")
    # Рекурсивная связь для повторяющихся задач
    # parent_task - это родительская задача (если текущая - экземпляр)
    parent_task = relationship(
        "Task",
        remote_side=[id], # Указывает, что remote_side - это id этой же таблицы
        back_populates="child_tasks",
        uselist=False # Один экземпляр имеет одного родителя
    )
    # child_tasks - это экземпляры, сгенерированные этой родительской задачей
    child_tasks = relationship(
        "Task",
        back_populates="parent_task",
        cascade="all, delete-orphan", # Удаление родителя удаляет все дочерние задачи
        foreign_keys=[original_task_id] # Явно указываем внешний ключ
    )

    def __repr__(self):
        return f"<Task(id={self.id}, due_date={self.due_date}, description='{self.description[:50] if self.description else ''}...')>"
    
    def __str__(self):
        return f"Задача на {self.due_date}: {self.description}"
    

class SoilType(Base):
    __tablename__ = 'soil_types'

    soil_type_id = Column('soil_type_id', Integer, primary_key=True, autoincrement=True)
    name_ru = Column('name_ru', String, unique=True, nullable=False, index=True)
    name_en = Column('name_en', String)
    description_ru = Column('description_ru', Text)
    water_retention_coefficient = Column('water_retention_coefficient', Float, nullable=False)

    user_plants = relationship("UserPlant", back_populates="soil")
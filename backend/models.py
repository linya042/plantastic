from sqlalchemy import Column, Integer, String, Date, DateTime, Text, Float, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = 'users'

    user_id = Column('user_id', Integer, primary_key=True, index=True)
    first_name = Column('first_name', String)
    username = Column('username', String)
    registration_date = Column('registration_date', Date)
    last_activity_date = Column('last_activity_date', Date)
    timezone = Column('timezone', String)
    settings_json = Column('settings_json', Text)

    user_plants = relationship("UserPlant", back_populates="user")


class Plant(Base):
    __tablename__ = 'plants'

    plant_id = Column('plant_id', Integer, primary_key=True, index=True)
    scientific_name = Column('scientific_name', String)
    common_name_ru = Column('common_name_ru', String)
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

    plant_images = relationship("PlantImage", back_populates="plant")
    user_plants = relationship("UserPlant", back_populates="plant")
    nn_classes = relationship("PlantNNClass", back_populates="plant")


class UserPlant(Base):
    __tablename__ = 'user_plants'

    user_plant_id = Column('user_plant_id', Integer, primary_key=True, index=True)
    user_id = Column('user_id', Integer, ForeignKey('users.user_id'), index=True)
    plant_id = Column('plant_id', Integer, ForeignKey('plants.plant_id'), index=True)
    nickname = Column('nickname', String)
    acquisition_date = Column('acquisition_date', Date)
    last_watering_date = Column('last_watering_date', Date) 
    notes = Column('notes', Text)

    user = relationship("User", back_populates="user_plants")
    plant = relationship("Plant", back_populates="user_plants")
    user_plant_images = relationship("UserPlantImage", back_populates="user_plant")
    tasks = relationship("Task", back_populates="user_plant")


class UserPlantImage(Base):
    __tablename__ = 'user_plant_images'

    image_id = Column('image_id', Integer, primary_key=True, index=True)
    user_plant_id = Column('user_plant_id', Integer, ForeignKey('user_plants.user_plant_id'), index=True)
    image_url = Column('image_url', String)
    upload_date = Column('upload_date', Date)
    description = Column('description', String)
    is_main_image = Column('is_main_image', Boolean)

    user_plant = relationship("UserPlant", back_populates="user_plant_images")


class Disease(Base):
    __tablename__ = 'diseases'

    disease_id = Column('disease_id', Integer, primary_key=True, index=True)
    disease_name_ru = Column('disease_name_ru', String)
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

    image_id = Column('image_id', Integer, primary_key=True, index=True)
    disease_id = Column('disease_id', Integer, ForeignKey('diseases.disease_id'), index=True)
    image_url = Column('image_url', String)
    description = Column('description', String)
    is_main_image = Column('is_main_image', Boolean)
    source_url = Column('source_url', String)

    disease = relationship("Disease", back_populates="disease_images")


class Symptom(Base):
    __tablename__ = 'symptoms'

    symptom_id = Column('symptom_id', Integer, primary_key=True)
    symptom_name_ru = Column('symptom_name_ru', String, unique=True, index=True)
    question = Column('question', String)
    symptom_name_en = Column('symptom_name_en', String)

    disease_symptoms = relationship("DiseaseSymptom", back_populates="symptom")


class DiseaseSymptom(Base):
    __tablename__ = 'disease_symptoms'

    disease_symptom_id = Column('disease_symptom_id', Integer, primary_key=True)
    disease_id = Column('disease_id', Integer, ForeignKey('diseases.disease_id'), index=True)
    symptom_id = Column('symptom_id', Integer, ForeignKey('symptoms.symptom_id'), index=True)

    disease = relationship("Disease", back_populates="disease_symptoms")
    symptom = relationship("Symptom", back_populates="disease_symptoms")


class PlantNNClass(Base):
    __tablename__ = 'plant_nn_classes'

    class_id = Column('class_id', Integer, primary_key=True)
    class_label = Column('class_label', String, unique=True, index=True)
    plant_id = Column('plant_id', Integer, ForeignKey('plants.plant_id'), index=True)

    plant = relationship("Plant", back_populates="nn_classes")


class DiseaseNNClass(Base):
    __tablename__ = 'disease_nn_classes'

    class_id = Column('class_id', Integer, primary_key=True)
    class_label = Column('class_label', String, unique=True, index=True)
    disease_id = Column('disease_id', Integer, ForeignKey('diseases.disease_id'), index=True)

    disease = relationship("Disease", back_populates="nn_classes")


class TaskType(Base):
    __tablename__ = 'task_types'

    task_type_id = Column('task_type_id', Integer, primary_key=True)
    task_name = Column('task_name', String, unique=True, index=True)

    tasks = relationship("Task", back_populates="task_type_obj")


class Task(Base):
    """Модель задачи для ухода за растениями"""
    __tablename__='tasks'

    id = Column('id', Integer, primary_key=True, index=True)
    user_plant_id = Column('user_plant_id', Integer, ForeignKey('user_plants.user_plant_id'), index=True)
    date = Column('date', Date, index=True, nullable=False)
    task_type = Column('task_type', Integer, ForeignKey('task_types.task_type_id'), index=True)
    text = Column('text', String, nullable=False)
    is_completed = Column('is_completed', Boolean, default=False)
    completion_date = Column('completion_date', Date)
    recurrence = Column('recurrence', String)
    start_date = Column('start_date', Date)
    end_date = Column('end_date', Date)

    user_plant = relationship("UserPlant", back_populates="tasks")
    task_type_obj = relationship("TaskType", back_populates="tasks")  # Переименовано в task_type_obj чтобы избежать конфликта имен

    # Метаданные для аудита
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Task(id={self.id}, date={self.date}, text='{self.text[:50]}...')>"
    
    def __str__(self):
        return f"Задача на {self.date}: {self.text}"
    

class SoilType(Base):
    __tablename__ = 'soil_types'

    soil_type_id = Column('soil_type_id', Integer, primary_key=True, autoincrement=True, index=True)
    name_ru = Column('name_ru', String, unique=True, nullable=False, index=True)
    name_en = Column('name_en', String, nullable=True)
    description_ru = Column('description_ru', Text, nullable=True)
    description_en = Column('description_en', Text, nullable=True)
    water_retention_coefficient = Column('water_retention_coefficient', Float, nullable=False)
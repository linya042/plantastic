from pydantic import BaseModel, ConfigDict, Field, field_validator
import datetime
from typing import Optional, List, Any


# ПОЛЬЗОВАТЕЛИ

class UserCreate(BaseModel):
    """Схема для создания пользователя"""
    first_name: Optional[str] = Field(None, max_length=100)
    username: str = Field(..., min_length=1, max_length=50)
    timezone: Optional[str] = Field(None, max_length=50)
    settings_json: Optional[str] = None
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str):
        if not v or not v.strip():
            raise ValueError('Username не может быть пустым')
        return v.strip()


class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""
    first_name: Optional[str] = Field(None, max_length=100)
    username: Optional[str] = Field(None, min_length=1, max_length=50)
    timezone: Optional[str] = Field(None, max_length=50)
    settings_json: Optional[str] = None
    last_activity_date: Optional[datetime.date] = None


class UserOut(BaseModel):
    """Схема для вывода пользователя"""
    user_id: int
    first_name: Optional[str] = None
    username: str
    registration_date: Optional[datetime.date] = None
    last_activity_date: Optional[datetime.date] = None
    timezone: Optional[str] = None
    settings_json: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# РАСТЕНИЯ

class PlantCreate(BaseModel):
    """Схема для создания растения"""
    scientific_name: str = Field(..., min_length=1, max_length=200)
    common_name_ru: Optional[str] = Field(None, max_length=200)
    synonyms: Optional[str] = None
    family: Optional[str] = Field(None, max_length=100)
    genus: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    max_height_cm: Optional[int] = Field(None, ge=0)
    growth_rate: Optional[str] = Field(None, max_length=50)
    light_requirements: Optional[str] = None
    temperature_range: Optional[str] = None
    humidity_requirements: Optional[str] = None
    soil_requirements: Optional[str] = None
    repotting_frequency: Optional[str] = None
    propagation_methods: Optional[str] = None
    toxicity: Optional[str] = None
    care_features: Optional[str] = None
    watering_frequency: Optional[str] = None
    watering_coefficient: Optional[float] = Field(None, ge=0.0, le=10.0)


class PlantUpdate(BaseModel):
    """Схема для обновления растения"""
    scientific_name: Optional[str] = Field(None, min_length=1, max_length=200)
    common_name_ru: Optional[str] = Field(None, max_length=200)
    synonyms: Optional[str] = None
    family: Optional[str] = Field(None, max_length=100)
    genus: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    max_height_cm: Optional[int] = Field(None, ge=0)
    growth_rate: Optional[str] = Field(None, max_length=50)
    light_requirements: Optional[str] = None
    temperature_range: Optional[str] = None
    humidity_requirements: Optional[str] = None
    soil_requirements: Optional[str] = None
    repotting_frequency: Optional[str] = None
    propagation_methods: Optional[str] = None
    toxicity: Optional[str] = None
    care_features: Optional[str] = None
    watering_frequency: Optional[str] = None
    watering_coefficient: Optional[float] = Field(None, ge=0.0, le=10.0)


class PlantOut(BaseModel):
    """Схема для вывода растения"""
    plant_id: int
    scientific_name: str
    common_name_ru: Optional[str] = None
    synonyms: Optional[str] = None
    family: Optional[str] = None
    genus: Optional[str] = None
    description: Optional[str] = None
    max_height_cm: Optional[int] = None
    growth_rate: Optional[str] = None
    light_requirements: Optional[str] = None
    temperature_range: Optional[str] = None
    humidity_requirements: Optional[str] = None
    soil_requirements: Optional[str] = None
    repotting_frequency: Optional[str] = None
    propagation_methods: Optional[str] = None
    toxicity: Optional[str] = None
    care_features: Optional[str] = None
    watering_frequency: Optional[str] = None
    watering_coefficient: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)


# РАСТЕНИЯ ПОЛЬЗОВАТЕЛЕЙ 

class UserPlantCreate(BaseModel):
    """Схема для добавления растения пользователю"""
    user_id: int = Field(..., description="ID пользователя")
    plant_id: int = Field(..., description="ID растения")
    nickname: Optional[str] = Field(None, max_length=100, description="Прозвище растения")
    acquisition_date: Optional[datetime.date] = Field(None, description="Дата приобретения")
    last_watering_date: Optional[datetime.date] = Field(None, description="Дата последнего полива")
    notes: Optional[str] = Field(None, description="Заметки о растении")


class UserPlantUpdate(BaseModel):
    """Схема для обновления растения пользователя"""
    nickname: Optional[str] = Field(None, max_length=100)
    acquisition_date: Optional[datetime.date] = None
    last_watering_date: Optional[datetime.date] = None
    notes: Optional[str] = None


class UserPlantOut(BaseModel):
    """Схема для вывода растения пользователя"""
    user_plant_id: int
    user_id: int
    plant_id: int
    nickname: Optional[str] = None
    acquisition_date: Optional[datetime.date] = None
    last_watering_date: Optional[datetime.date] = None
    notes: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserPlantWithDetails(BaseModel):
    """Растение пользователя с деталями"""
    user_plant_id: int
    nickname: Optional[str] = None
    acquisition_date: Optional[datetime.date] = None
    last_watering_date: Optional[datetime.date] = None
    notes: Optional[str] = None
    
    # Вложенные данные
    user: Optional[UserOut] = None
    plant: Optional[PlantOut] = None
    
    model_config = ConfigDict(from_attributes=True)


# ИЗОБРАЖЕНИЯ 

class PlantImageCreate(BaseModel):
    """Схема для загрузки изображения растения"""
    plant_id: int
    image_url: str = Field(..., min_length=1)
    description: Optional[str] = None
    is_main_image: Optional[bool] = False


class UserPlantImageCreate(BaseModel):
    """Схема для загрузки изображения растения пользователя"""
    user_plant_id: int
    image_url: str = Field(..., min_length=1)
    description: Optional[str] = None
    is_main_image: Optional[bool] = False


class ImageOut(BaseModel):
    """Базовая схема для изображений"""
    image_id: int
    image_url: str
    description: Optional[str] = None
    is_main_image: Optional[bool] = False
    upload_date: Optional[datetime.date] = None
    
    model_config = ConfigDict(from_attributes=True)


# БОЛЕЗНИ И СИМПТОМЫ

class DiseaseCreate(BaseModel):
    """Схема для создания болезни"""
    disease_name_ru: str = Field(..., min_length=1, max_length=200)
    disease_name_en: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    symptoms_description: Optional[str] = None
    treatment: Optional[str] = None
    prevention: Optional[str] = None


class DiseaseOut(BaseModel):
    """Схема для вывода болезни"""
    disease_id: int
    disease_name_ru: str
    disease_name_en: Optional[str] = None
    description: Optional[str] = None
    symptoms_description: Optional[str] = None
    treatment: Optional[str] = None
    prevention: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class SymptomCreate(BaseModel):
    """Схема для создания симптома"""
    symptom_name_ru: str = Field(..., min_length=1, max_length=200)
    symptom_name_en: Optional[str] = Field(None, max_length=200)
    question: Optional[str] = None


class SymptomOut(BaseModel):
    """Схема для вывода симптома"""
    symptom_id: int
    symptom_name_ru: str
    symptom_name_en: Optional[str] = None
    question: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class DiseaseWithSymptoms(BaseModel):
    """Болезнь с симптомами"""
    disease_id: int
    disease_name_ru: str
    disease_name_en: Optional[str] = None
    description: Optional[str] = None
    symptoms_description: Optional[str] = None
    treatment: Optional[str] = None
    prevention: Optional[str] = None
    symptoms: List[SymptomOut] = []
    
    model_config = ConfigDict(from_attributes=True)


# НЕЙРОННЫЕ СЕТИ

class PlantNNClassOut(BaseModel):
    """Схема для класса нейросети растений"""
    class_id: int
    class_label: str
    plant_id: int
    
    model_config = ConfigDict(from_attributes=True)


class DiseaseNNClassOut(BaseModel):
    """Схема для класса нейросети болезней"""
    class_id: int
    class_label: str
    disease_id: int
    
    model_config = ConfigDict(from_attributes=True)


# ЗАДАЧИ

class TaskCreate(BaseModel):
    """Схема для создания новой задачи"""
    date: datetime.date = Field(..., description="Дата выполнения задачи")
    text: str = Field(..., min_length=1, max_length=1000, description="Описание задачи")
    user_plant_id: Optional[int] = Field(None, description="ID растения пользователя")
    task_type: Optional[int] = Field(None, description="ID типа задачи")
    recurrence: Optional[str] = Field(None, description="Периодичность повторения задачи")
    start_date: Optional[datetime.date] = Field(None, description="Дата начала для повторяющихся задач")
    end_date: Optional[datetime.date] = Field(None, description="Дата окончания для повторяющихся задач")
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str):
        """Валидация текста задачи"""
        if not v or not v.strip():
            raise ValueError('Текст задачи не может быть пустым')
        return v.strip()
    
    @field_validator('recurrence')
    @classmethod
    def validate_recurrence(cls, v: Optional[str]):
        if v is not None:
            allowed_values = ['daily', 'weekly', 'monthly', 'yearly', 'none']
            if v.lower() not in allowed_values:
                raise ValueError(f'Допустимые значения периодичности: {", ".join(allowed_values)}')
            return v.lower()
        return v


class TaskUpdate(BaseModel):
    """Схема для обновления задачи"""
    date: Optional[datetime.date] = Field(None, description="Новая дата выполнения")
    text: Optional[str] = Field(None, min_length=1, max_length=1000, description="Новое описание задачи")
    is_completed: Optional[bool] = Field(None, description="Статус выполнения задачи")
    user_plant_id: Optional[int] = Field(None, description="ID растения пользователя")
    task_type: Optional[int] = Field(None, description="ID типа задачи")
    recurrence: Optional[str] = Field(None, description="Периодичность повторения задачи")
    start_date: Optional[datetime.date] = Field(None, description="Дата начала")
    end_date: Optional[datetime.date] = Field(None, description="Дата окончания")

    @field_validator('text')
    @classmethod
    def validate_text(cls, v: Optional[str]):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Текст задачи не может быть пустым')
            return v.strip() 
        return v
    
    @field_validator('recurrence')
    @classmethod
    def validate_recurrence(cls, v: Optional[str]):
        if v is not None:
            allowed_values = ['daily', 'weekly', 'monthly', 'yearly', 'none']
            if v.lower() not in allowed_values:
                raise ValueError(f'Допустимые значения периодичности: {", ".join(allowed_values)}')
            return v.lower()
        return v


class TaskOut(BaseModel):
    """Схема для вывода задачи"""
    id: int
    date: datetime.date
    text: str
    is_completed: Optional[bool] = False
    completion_date: Optional[datetime.date] = None
    user_plant_id: Optional[int] = None
    task_type: Optional[int] = None
    recurrence: Optional[str] = None
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
        

class TaskTypeCreate(BaseModel):
    """Схема для создания типа задачи"""
    task_name: str = Field(..., min_length=1, max_length=100)
    
    @field_validator('task_name')
    @classmethod
    def validate_task_name(cls, v: str):
        if not v or not v.strip():
            raise ValueError('Название типа задачи не может быть пустым')
        return v.strip()


class TaskTypeOut(BaseModel):
    """Схема для вывода типа задачи"""
    task_type_id: int
    task_name: str
    
    model_config = ConfigDict(from_attributes=True)


class TaskWithDetails(BaseModel):
    """Расширенная схема задачи с деталями"""
    id: int
    date: datetime.date
    text: str
    is_completed: Optional[bool] = False
    completion_date: Optional[datetime.date] = None
    recurrence: Optional[str] = None
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None
    
    # Вложенные объекты
    user_plant: Optional[UserPlantOut] = None
    task_type_obj: Optional[TaskTypeOut] = None
    
    model_config = ConfigDict(from_attributes=True)


class TaskList(BaseModel):
    """Схема для списка задач"""
    tasks: List[TaskOut]
    total: int
    

class HealthResponse(BaseModel):
    """Схема для health check"""
    status: str
    timestamp: datetime.datetime
    database_connected: bool
    version: str = "1.0.0"


class MessageResponse(BaseModel):
    """Базовая схема для ответов с сообщением"""
    message: str
    success: bool = True


class ListResponse(BaseModel):
    """Базовая схема для списков с пагинацией"""
    items: List[Any]
    total: int
    page: int = 1
    per_page: int = 50
    pages: int


class SoilTypeBase(BaseModel):
    name_ru: str = Field(..., description="Название типа грунта на русском")
    name_en: Optional[str] = Field(None, description="Название типа грунта на английском")
    description_ru: Optional[str] = Field(None, description="Описание типа грунта на русском")
    description_en: Optional[str] = Field(None, description="Описание типа грунта на английском")
    water_retention_coefficient: float = Field(..., ge=0.0, le=1.0, description="Коэффициент влагоемкости (от 0.0 до 1.0)")


class SoilTypeOut(SoilTypeBase):
    soil_type_id: int = Field(..., description="Уникальный ID типа грунта")

    model_config = ConfigDict(from_attributes=True) # Важно для конвертации SQLAlchemy-объектов
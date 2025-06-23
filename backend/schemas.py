from pydantic import BaseModel, ConfigDict, Field, field_validator, computed_field
from datetime import date, datetime
from typing import Optional, List, Any

# ПОЛЬЗОВАТЕЛИ

class UserCreate(BaseModel):
    """Схема для создания пользователя"""
    user_id: int = Field(..., description="Telegram ID пользователя")
    first_name: Optional[str] = Field(None, max_length=100)
    username: Optional[str] = Field(None, max_length=50)
    registration_date: datetime = Field(default_factory=datetime.now)
    last_activity_date: datetime = Field(default_factory=datetime.now)
    timezone: Optional[str] = Field(None, max_length=50)
    settings_json: Optional[str] = None
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        v = v.strip()
        if v.startswith('@'):
            v = v[1:]
        return v if v else None


# class UserUpdate(BaseModel):
#     """Схема для обновления пользователя"""
#     first_name: Optional[str] = Field(None, max_length=100)
#     username: Optional[str] = Field(None, min_length=1, max_length=50)
#     timezone: Optional[str] = Field(None, max_length=50)
#     settings_json: Optional[str] = None
#     last_activity_date: Optional[datetime] = None


class UserOut(BaseModel):
    """Схема для вывода пользователя"""
    user_id: int
    first_name: Optional[str] = None
    username: Optional[str] = None
    registration_date: datetime
    last_activity_date: datetime
    timezone: Optional[str] = None
    settings_json: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class TelegramInitData(BaseModel):
    """Схема для валидации initData от Telegram"""
    initData: str = Field(..., description="Строка initData от Telegram WebApp")

    @field_validator('initData')
    @classmethod
    def validate_init_data(cls, v: str) -> str:
        """Проверяем, что initData не пустая"""
        if not v or not v.strip():
            raise ValueError('initData не может быть пустой')
        return v.strip()


class AuthResponse(BaseModel):
    """Схема ответа авторизации"""
    success: bool
    message: str
    is_new_user: bool
    user_data: Optional[UserOut] = None


# ИЗОБРАЖЕНИЯ 

# class PlantImageCreate(BaseModel):
#     """Схема для загрузки изображения растения"""
#     plant_id: int
#     image_url: str = Field(..., min_length=1)
#     description: Optional[str] = None
#     is_main_image: Optional[bool] = False


# class UserPlantImageCreate(BaseModel):
#     """Схема для загрузки изображения растения пользователя"""
#     user_plant_id: int
#     image_url: str = Field(..., min_length=1)
#     description: Optional[str] = None
#     is_main_image: Optional[bool] = False


class ImageOut(BaseModel):
    """Базовая схема для изображений"""
    # image_id: int
    image_url: str
    is_main_image: Optional[bool] = False
    upload_date: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# РАСТЕНИЯ

# class PlantCreate(BaseModel):
#     """Схема для создания растения"""
#     scientific_name: str = Field(..., min_length=1, max_length=200)
#     common_name_ru: Optional[str] = Field(None, max_length=200)
#     synonyms: Optional[str] = None
#     family: Optional[str] = Field(None, max_length=100)
#     genus: Optional[str] = Field(None, max_length=100)
#     description: Optional[str] = None
#     max_height_cm: Optional[int] = Field(None, ge=0)
#     growth_rate: Optional[str] = Field(None, max_length=50)
#     light_requirements: Optional[str] = None
#     temperature_range: Optional[str] = None
#     humidity_requirements: Optional[str] = None
#     soil_requirements: Optional[str] = None
#     repotting_frequency: Optional[str] = None
#     propagation_methods: Optional[str] = None
#     toxicity: Optional[str] = None
#     care_features: Optional[str] = None
#     watering_frequency: Optional[str] = None
#     watering_coefficient: Optional[float] = Field(None)


# class PlantUpdate(BaseModel):
#     """Схема для обновления растения"""
#     scientific_name: Optional[str] = Field(None, min_length=1, max_length=200)
#     common_name_ru: Optional[str] = Field(None, max_length=200)
#     synonyms: Optional[str] = None
#     family: Optional[str] = Field(None, max_length=100)
#     genus: Optional[str] = Field(None, max_length=100)
#     description: Optional[str] = None
#     max_height_cm: Optional[int] = Field(None, ge=0)
#     growth_rate: Optional[str] = Field(None, max_length=50)
#     light_requirements: Optional[str] = None
#     temperature_range: Optional[str] = None
#     humidity_requirements: Optional[str] = None
#     soil_requirements: Optional[str] = None
#     repotting_frequency: Optional[str] = None
#     propagation_methods: Optional[str] = None
#     toxicity: Optional[str] = None
#     care_features: Optional[str] = None
#     watering_frequency: Optional[str] = None
#     watering_coefficient: Optional[float] = Field(None)


class GenusWateringCoefficient(BaseModel):
    genus: str
    watering_coefficient: float
    model_config = ConfigDict(from_attributes=True)


class VarietyWithImage(BaseModel):
    variety_name: str
    variety_images_raw: List[ImageOut] = Field(alias='plant_nn_classes_images',default_factory=list, description="Сырые данные изображений для сорта", exclude=True)
    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def variety_images_url_list(self) -> List[str]:
        if self.variety_images_raw:
            sorted_images = sorted(
                self.variety_images_raw,
                key=lambda img: not getattr(img, 'is_main_image', False)
                )
            return [img.image_url for img in sorted_images]
        return []

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

    varietys: List[VarietyWithImage] = Field(alias="nn_classes", default_factory=list, description="Список сортов растений c изображениями")
    
    model_config = ConfigDict(from_attributes=True)
    

class PlantOutForSearch(BaseModel):
    """Схема для вывода растения"""
    plant_id: int
    scientific_name: str
    common_name_ru: Optional[str] = None
    synonyms: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)



class VarietyOutForSearch(BaseModel):
    """Схема для вывода сортов растений"""
    class_id: int
    class_label: str
    variety_name: str

    model_config = ConfigDict(from_attributes=True)

    @field_validator('class_label', mode='after')
    @classmethod
    def edit_class_label(cls, v: str, info) -> str:
        return v.replace("_", " ").title()


# РАСТЕНИЯ ПОЛЬЗОВАТЕЛЕЙ 

class UserPlantCreate(BaseModel):
    """Схема для добавления растения пользователю"""
    plant_nn_classes_id: int = Field(..., description="ID сорта растения из справочника plant_nn_classes")
    nickname: Optional[str] = Field(None, max_length=100, description="Прозвище растения")
    acquisition_date: Optional[date] = Field(None, description="Дата приобретения")
    last_watering_date: Optional[date] = Field(None, description="Дата последнего полива")
    notes: Optional[str] = Field(None, description="Заметки о растении")
    soil_type_id: Optional[int] = Field(None, description="ID типа грунта")
    image_data_uri: Optional[str] = Field(None, description="Data URI изображения растения (120x120px)")

    @field_validator('nickname', 'notes', 'acquisition_date', 'last_watering_date', mode='before')
    def check_empty_strings(cls, v):
        if isinstance(v, str) and v == "":
            return None
        return v
    
    @field_validator('soil_type_id', mode='before')
    def check_zero(cls, v):
        if v == 0:
            return None
        return v


class UserPlantUpdate(UserPlantCreate):
    """Схема для обновления растения пользователя"""
    # plant_nn_classes_id: int = Field(..., description="ID сорта растения из справочника plant_nn_classes")
    # nickname: Optional[str] = Field(None, max_length=100, description="Прозвище растения")
    # acquisition_date: Optional[date] = Field(None, description="Дата приобретения")
    # last_watering_date: Optional[date] = Field(None, description="Дата последнего полива")
    # notes: Optional[str] = Field(None, description="Заметки о растении")
    # soil_type_id: Optional[int] = Field(None, description="ID типа грунта")
    deleted: Optional[bool] = Field(None, description="Флаг удаления (для мягкого удаления)")

    # @field_validator('nickname', 'notes', 'acquisition_date', 'last_watering_date', mode='before')
    # def check_empty_strings(cls, v):
    #     if v == "":
    #         return None
    #     return v
    
    # @field_validator('soil_type_id', mode='before')
    # def check_zero(cls, v):
    #     if v == 0:
    #         return None
    #     return v


class UserPlantOut(BaseModel):
    """Схема для вывода растения пользователя"""
    user_plant_id: int
    plant_nn_classes_id: int
    nickname: Optional[str] = None
    acquisition_date: Optional[date] = None
    last_watering_date: Optional[date] = None
    notes: Optional[str] = None
    soil_type_id: Optional[int] = None
    deleted: bool = False

    user_plant_images: List[ImageOut] = Field(default_factory=list, exclude=True)

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def user_plant_images_URI(self) -> List[str]:
        if self.user_plant_images:
            sorted_images = sorted(
                self.user_plant_images,
                key=lambda img: img.upload_date,
                reverse=True
                )
            return [img.image_url for img in sorted_images]
        return []

# БОЛЕЗНИ И СИМПТОМЫ

# class DiseaseCreate(BaseModel):
#     """Схема для создания болезни"""
#     disease_name_ru: str = Field(..., min_length=1, max_length=200)
#     disease_name_en: Optional[str] = Field(None, max_length=200)
#     description: Optional[str] = None
#     symptoms_description: Optional[str] = None
#     treatment: Optional[str] = None
#     prevention: Optional[str] = None


# class DiseaseOut(BaseModel):
#     """Схема для вывода болезни"""
#     disease_id: int
#     disease_name_ru: str
#     disease_name_en: Optional[str] = None
#     description: Optional[str] = None
#     symptoms_description: Optional[str] = None
#     treatment: Optional[str] = None
#     prevention: Optional[str] = None
#     disease_images: List[str] = Field(default_factory=list, description="Список адресов изображений заболевания")

#     model_config = ConfigDict(from_attributes=True)

#     @field_validator('disease_images', mode='before')
#     @classmethod
#     def convert_disease_images_to_urls(cls, v: Any) -> List[str]:
#         if not isinstance(v, list):
#             return []
#         sorted_images = sorted(v, key=lambda img: not getattr(img, 'is_main_image', False))
#         return [getattr(img, 'image_url') for img in sorted_images if hasattr(img, 'image_url')]


# class SymptomCreate(BaseModel):
#     """Схема для создания симптома"""
#     symptom_name_ru: str = Field(..., min_length=1, max_length=200)
#     symptom_name_en: Optional[str] = Field(None, max_length=200)
#     question: Optional[str] = None


class SymptomOut(BaseModel):
    """Схема для вывода симптома"""
    symptom_name_ru: str
    model_config = ConfigDict(from_attributes=True)


class DiseaseSymptomRel(BaseModel):
    symptom: SymptomOut
    model_config = ConfigDict(from_attributes=True)


class DiseaseWithSymptoms(BaseModel):
    """Болезнь с симптомами"""
    disease_id: int
    disease_name_ru: str
    # disease_name_en: Optional[str] = None
    description: Optional[str] = None
    symptoms_description: Optional[str] = None
    treatment: Optional[str] = None
    prevention: Optional[str] = None

    disease_images: List[ImageOut] = Field(default_factory=list, exclude=True)
    disease_symptoms: List[DiseaseSymptomRel] = Field(default_factory=list, exclude=True)

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def disease_images_url_list(self) -> List[str]:
        """Формирует отсортированный список URL изображений."""
        if self.disease_images:
            sorted_images = sorted(
                self.disease_images,
                key=lambda img: not getattr(img, 'is_main_image', False)
            )
            return [str(img.image_url) for img in sorted_images]
        return []

    @computed_field
    @property
    def symptoms_list(self) -> List[str]:
        """Формирует список названий симптомов."""
        if self.disease_symptoms:
            symptoms = []
            for ds in self.disease_symptoms:
                if ds.symptom:
                    symptoms.append(ds.symptom.symptom_name_ru)
            return symptoms
        return []





# class DiseaseNNClassOut(BaseModel):
#     """Схема для класса нейросети болезней"""
#     class_id: int
#     class_label: str
#     disease_id: int
    
#     model_config = ConfigDict(from_attributes=True)



# НЕЙРОННЫЕ СЕТИ

# Схемы для предсказаний
class RawPredictionItem(BaseModel):
    class_name: str = Field(..., description="Имя класса, предсказанное моделью")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Уверенность модели (0-1)")

class PredictionContent(BaseModel):
    predictions: List[RawPredictionItem]
    filename: str
    processed_at: datetime = Field(..., description="Время обработки запроса")

class RawClassifierResponse(BaseModel):
    success: bool
    data: PredictionContent


# Схемы для финального ответа
class PredictItem(BaseModel):
    """Схема для схемы IdentifyResponse"""
    item_id: int = Field(..., description="Идентификатор растения / заболевания")
    item_name: str = Field(..., description="Название сорта растения / заболевания")
    confidence: float = Field(..., ge=0.0, le=100.0, description="Уверенность модели в предсказании")
    images: List[str] = Field(default_factory=list, description="Список адресов изображений")

class IdentifyResponse(BaseModel):
    """Схема для ответов на запрос на распознавание"""
    status: str = Field(..., example="ok", description="Статус выполнения запроса")
    timestamp: datetime = Field(default_factory=datetime.now, description="Время обработки запроса")
    data: List[PredictItem]  = Field(..., description="Список предсказан")
    total: int = Field(..., description="Общее количество предсказанных элементов")


# ЗАДАЧИ

# class TaskTypeCreate(BaseModel):
#     """Схема для создания типа задачи"""
#     task_name: str = Field(..., min_length=1, max_length=100)
    
#     @field_validator('task_name')
#     @classmethod
#     def validate_task_name(cls, v: str):
#         if not v or not v.strip():
#             raise ValueError('Название типа задачи не может быть пустым')
#         return v.strip()


class TaskTypeOut(BaseModel):
    """Схема для вывода типа задачи"""
    task_type_id: int
    task_name: str
    task_description: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    """Схема для создания новой задачи"""
    # user_id: int = Field(..., description="ID пользователя-владельца задачи")
    user_plant_id: int = Field(..., description="ID растения пользователя")
    task_type_id: int = Field(..., description="ID типа задачи")
    due_date: datetime = Field(..., description="Дата выполнения задачи")
    description: Optional[str] = Field(None, max_length=1000, description="Описание задачи")
    
    is_recurring: bool = Field(False, description="Является ли эта задача повторяющейся?")
    recurrence_rule: Optional[str] = Field(None, description="JSON-строка с правилом повторения (например, 'daily', 'weekly', 'monthly', 'yearly').")
    recurrence_end_date: Optional[datetime] = Field(None, description="Дата окончания повторений для повторяющихся задач")
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]):
        """Валидация текста задачи"""
        if v is not None:
            v = v.strip()
            if not v:
                return None
            return v
        return v
    
    @field_validator('recurrence_rule')
    @classmethod
    def validate_recurrence_rule(cls, v: Optional[str], info):
        if info.data.get('is_recurring') and v is None:
            raise ValueError('Для повторяющейся задачи должно быть указано правило повторения (recurrence_rule).')
        if v is not None:
            allowed_values = ['daily', 'weekly', 'monthly', 'yearly']
            if v.lower() not in allowed_values:
                raise ValueError(f'Допустимые значения периодичности: {", ".join(allowed_values)}')
            return v.lower()
        return v

    @field_validator('recurrence_end_date')
    @classmethod
    def validate_recurrence_end_date(cls, v: Optional[datetime], info):
        if info.data.get('is_recurring') and v is None:
            raise ValueError('Для повторяющейся задачи должна быть указана дата окончания (recurrence_end_date).')
        if v is not None and info.data.get('due_date') and v < info.data['due_date']:
            raise ValueError('Дата окончания повторений не может быть раньше due_date.')
        return v
    

class TaskUpdate(BaseModel):
    """Схема для обновления задачи"""
    user_plant_id: Optional[int] = Field(None, description="ID растения пользователя")
    task_type_id: Optional[int] = Field(None, description="ID типа задачи")
    due_date: Optional[datetime] = Field(None, description="Новая дата выполнения")
    description: Optional[str] = Field(None, min_length=1, max_length=1000, description="Новое описание задачи")

    is_completed: Optional[bool] = Field(None, description="Статус выполнения задачи")
    completion_date: Optional[datetime] = None # Будет устанавливаться автоматически при is_completed=True

    is_recurring: Optional[bool] = Field(None, description="Является ли эта задача повторяющейся?")
    recurrence_rule: Optional[str] = Field(None, description="JSON-строка с правилом повторения")
    recurrence_end_date: Optional[datetime] = Field(None, description="Дата окончания повторений")

    @field_validator('description')
    @classmethod
    def validate_description_update(cls, v: Optional[str]):
        if v is not None:
            v = v.strip()
            if not v:
                return None
            return v
        return v
    
    @field_validator('recurrence_rule')
    @classmethod
    def validate_recurrence_rule_update(cls, v: Optional[str], info):
        if info.data.get('is_recurring') is True and v is None:
            raise ValueError('При установке is_recurring=True, recurrence_rule не может быть None.')
        if v is not None:
            allowed_values = ['daily', 'weekly', 'monthly', 'yearly']
            if v.lower() not in allowed_values:
                raise ValueError(f'Допустимые значения периодичности: {", ".join(allowed_values)}')
            return v.lower()
        return v
    
    @field_validator('recurrence_end_date')
    @classmethod
    def validate_recurrence_end_date_update(cls, v: Optional[datetime], info):
        if info.data.get('is_recurring') is True and v is None:
            raise ValueError('При установке is_recurring=True, recurrence_end_date не может быть None.')
        if v is not None and info.data.get('due_date') and v < info.data['due_date']:
            raise ValueError('Дата окончания повторений не может быть раньше due_date.')
        return v


class TaskOut(BaseModel):
    """Схема для вывода задачи"""
    id: int
    user_id: int
    user_plant_id: int
    task_type_id: int
    due_date: datetime
    description: Optional[str] = None

    is_completed: bool = False
    completion_date: Optional[datetime] = None

    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    recurrence_end_date: Optional[datetime] = None

    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted: bool = False
    
    # Вложенные объекты для деталей
    task_type: Optional[TaskTypeOut] = None

    model_config = ConfigDict(from_attributes=True)


class TaskList(BaseModel):
    """Схема для списка задач"""
    tasks: List[TaskOut]
    total: int
    page: int
    per_page: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)
    

class HealthResponse(BaseModel):
    """Схема для health check"""
    status: str
    timestamp: datetime = Field(default_factory=datetime.now)
    database_connected: bool
    version: str = "1.0.0"


class MessageResponse(BaseModel):
    """Базовая схема для ответов с сообщением"""
    success: bool = True
    message: str


class SoilTypeOut(BaseModel):
    soil_type_id: int = Field(..., description="Уникальный ID типа грунта")
    name_ru: str = Field(..., description="Название типа грунта на русском")
    name_en: Optional[str] = Field(None, description="Название типа грунта на английском")
    description_ru: Optional[str] = Field(None, description="Описание типа грунта на русском")
    water_retention_coefficient: float = Field(..., description="Коэффициент влагоемкости")

    model_config = ConfigDict(from_attributes=True)


class PlantNNClassForDetails(BaseModel):
    class_id: int
    class_label: str
    plant: PlantOutForSearch
    variety_name: str
    
    model_config = ConfigDict(from_attributes=True)


class UserPlantWithDetails(BaseModel):
    """Растение пользователя с деталями"""
    user_plant_id: int
    user_id: int
    plant_nn_classes_id: int
    nickname: Optional[str] = None    
    acquisition_date: Optional[date] = None
    last_watering_date: Optional[date] = None
    notes: Optional[str] = None
    soil_type_id: Optional[int] = None
    deleted: bool
    created_at: datetime
    updated_at: datetime

    plant_nn_classes: Optional[PlantNNClassForDetails] = Field(exclude=True)
    user_plant_images: List[ImageOut] = Field(default_factory=list, exclude=True)

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def variety_name(self) -> str:
        return self.plant_nn_classes.variety_name if self.plant_nn_classes else "Неизвестное растение"

    @computed_field
    @property
    def plant_common_name_ru(self) -> Optional[str]:
        if self.plant_nn_classes and self.plant_nn_classes.plant:
            return self.plant_nn_classes.plant.common_name_ru
        return None
    
    @computed_field
    @property
    def plant_scientific_name(self) -> Optional[str]:
        if self.plant_nn_classes and self.plant_nn_classes.plant:
            return self.plant_nn_classes.plant.scientific_name
        return None

    @computed_field
    @property
    def user_plant_images_list(self) -> List[str]:
        if self.user_plant_images:
            sorted_images = sorted(
                self.user_plant_images,
                key=lambda img: img.upload_date,
                reverse=True
                )
            return [img.image_url for img in sorted_images]
        return []
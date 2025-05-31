from pathlib import Path
from typing import Dict, List, Union
from PIL import Image

from classifier.models import PlantClassifier
from classifier.config import WEIGHT_PATH, CLASS_NAMES_PATH, TOP_K
from classifier.utils import ClassificationError

class PlantService:
    def __init__(
        self,
        model_path: Path = WEIGHT_PATH,
        class_names_path: Path = CLASS_NAMES_PATH,
        top_k: int = TOP_K
    ):
        """
        Сервис для классификации растений
        
        Args:
            model_path: путь к весам модели
            class_names_path: путь к файлу с именами классов
            top_k: количество возвращаемых предсказаний
        """
        self.classifier = PlantClassifier(
            model_path=model_path,
            class_names_path=class_names_path
        )
        self.top_k = top_k
        
    @property
    def model(self):
        return self.classifier.model
        
    @property
    def class_names(self):
        return self.classifier.class_names

    def classify_plant(self, image_data: Union[bytes, str, Path, Image.Image]) -> List[Dict[str, Union[str, float]]]:
        """
        Классификация растения
        
        Args:
            image_data: изображение в одном из форматов:
                - bytes: байты изображения
                - str: путь к файлу
                - Path: путь к файлу
                - Image.Image: PIL изображение
                
        Returns:
            Список предсказаний с уверенностью
            
        Raises:
            ClassificationError: при ошибках классификации
        """
        try:
            predictions = self.classifier.predict(image_data, top_k=self.top_k)
            return predictions
        except Exception as e:
            raise ClassificationError(str(e))

    def close(self):
        """Освобождение ресурсов"""
        if hasattr(self, 'classifier'):
            del self.classifier
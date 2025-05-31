import logging
import torch
import torch.nn as nn
from torchvision import models
from typing import List, Dict, Union
from pathlib import Path
from PIL import Image
from classifier.utils import ImageProcessor

logger = logging.getLogger(__name__)

class PlantClassifier:
    def __init__(
        self,
        model_path: Path,
        class_names_path: Path,
        device: str = None,
        batch_size: int = 1
    ):
        """
        Инициализация классификатора растений
        
        Args:
            model_path: путь к файлу весов
            class_names_path: путь к файлу с именами классов
            device: устройство для вычислений ('cuda' или 'cpu')
            batch_size: размер батча для обработки
        """
        self.batch_size = batch_size
        self.class_names = self._load_class_names(class_names_path)
        self.num_classes = len(self.class_names)
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Инициализируем обработчик изображений
        self.image_processor = ImageProcessor()
        
        self.model = self._initialize_model()
        self._load_weights(model_path)
        self.model.eval()

    def _load_class_names(self, class_names_path: Path) -> List[str]:
        """Загрузка имен классов из файла"""
        try:
            with open(class_names_path, 'r') as f:
                return [line.strip() for line in f.readlines()]
        except Exception as e:
            logger.error(f"Ошибка при загрузке классов: {str(e)}")
            raise

    def _initialize_model(self) -> nn.Module:
        """Инициализация архитектуры модели"""
        try:
            model = models.efficientnet_b2(weights=None)
            
            # Замораживаем веса базовой модели
            for param in model.parameters():
                param.requires_grad = False
                
            # Заменяем классификатор
            num_ftrs = model.classifier[1].in_features
            model.classifier = nn.Sequential(
                nn.Dropout(p=0.2),
                nn.Linear(num_ftrs, self.num_classes)
            )
            
            return model.to(self.device)
            
        except Exception as e:
            logger.error(f"Ошибка инициализации модели: {str(e)}")
            raise

    def _load_weights(self, model_path: Path) -> None:
        """Загрузка весов модели"""
        try:
            if not model_path.exists():
                raise FileNotFoundError(f"Файл весов не найден: {model_path}")
                
            checkpoint = torch.load(model_path, map_location=self.device)
            
            if isinstance(checkpoint, dict):
                state_dict = checkpoint.get('state_dict', checkpoint)
                
            missing, unexpected = self.model.load_state_dict(state_dict, strict=True)
            
            if missing or unexpected:
                raise ValueError(f"Проблемы при загрузке весов: missing={missing}, unexpected={unexpected}")
                
        except Exception as e:
            logger.error(f"Ошибка загрузки весов: {str(e)}")
            raise

    @torch.no_grad()
    def predict(self, image_data: Union[bytes, str, Path, Image.Image], top_k: int = 3) -> List[Dict[str, Union[str, float]]]:
        """
        Получение предсказаний модели
        
        Args:
            image_data: Входные данные в одном из форматов:
                - bytes: байты изображения
                - str: путь к файлу
                - Path: путь к файлу
                - Image.Image: PIL изображение
            top_k: количество лучших предсказаний
            
        Returns:
            Список предсказаний с уверенностью
        """
        try:
            if top_k > self.num_classes:
                top_k = self.num_classes
                
            # Используем ImageProcessor для обработки изображения
            image_tensor = self.image_processor.process_image(image_data)
            # Добавляем размерность батча для модели
            image_tensor = image_tensor.unsqueeze(0).to(self.device)
            
            outputs = self.model(image_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            top_probs, top_indices = torch.topk(probabilities, top_k)
            
            predictions = []
            for prob, idx in zip(top_probs[0], top_indices[0]):
                predictions.append({
                    "class_name": self.class_names[idx],
                    "confidence": float(prob)
                })
            
            # Очистка CUDA памяти, если используется GPU
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            return predictions
            
        except Exception as e:
            logger.error(f"Ошибка при предсказании: {str(e)}")
            raise

    def __del__(self):
        """Очистка ресурсов при удалении объекта"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
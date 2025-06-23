import torch
import torch.nn as nn
from torchvision import models
import torchvision.transforms as transforms
from PIL import Image
from pillow_heif import register_heif_opener
from io import BytesIO
from typing import List, Dict, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

WEIGHTS_DIR = Path(__file__).resolve().parent.parent / 'detector_weights'
PLANT_DETECTOR_WEIGHTS_PATH = WEIGHTS_DIR / 'model_epoch_10.pth'
PLANT_DETECTOR_NAMES_PATH = WEIGHTS_DIR / 'class_names.txt'
register_heif_opener()

class PlantDetector:
    def __init__(
        self,
        device: str = None,
        batch_size: int = 1
    ):
        """
        Инициализация классификатора растений
        
        Args:
            device: устройство для вычислений ('cuda' или 'cpu')
            batch_size: размер батча для обработки
        """
        self.batch_size = batch_size
        self.class_names = self._load_class_names(PLANT_DETECTOR_NAMES_PATH)
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
                
        self.model = self._initialize_model()
        self._load_weights(PLANT_DETECTOR_WEIGHTS_PATH)
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
            model = models.mobilenet_v3_small(weights=None)
                
            # Заменяем классификатор
            num_ftrs = model.classifier[3].in_features
            model.classifier[3] = nn.Linear(num_ftrs, len(self.class_names))
            
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

    def _process_image(self, image_input: Union[bytes, str, Path, Image.Image]) -> torch.Tensor:
        """
        Обработка входного изображения
        
        Args:
            image_input: Входные данные в одном из форматов:
                - bytes: байты изображения
                - Image.Image: PIL изображение
                
        Returns:
            torch.Tensor: Подготовленный тензор изображения размерности (C, H, W)
            
        Raises:
            Error: При ошибках обработки изображения
        """
        try:
            
            if isinstance(image_input, bytes):
                img = Image.open(BytesIO(image_input)).convert('RGB')

            elif isinstance(image_input, (str, Path)):
                path = Path(image_input)
                if not path.exists():
                    raise FileNotFoundError(f"Файл не найден: {path}")
                return Image.open(path).convert('RGB')
                
            elif isinstance(image_input, Image.Image):
                img = image_input.convert('RGB')

            else:
                raise ValueError(f"Неподдерживаемый тип входных данных: {type(image_input)}")

            tensor = self.transform(img)
            logger.debug(f"Изображение уменьшено до: {img.size}")
            
            return tensor
            
        except Exception as e:
            logger.error(f"Ошибка обработки изображения: {str(e)}")
            raise ValueError(f"Не удалось обработать изображение: {str(e)}")

    @torch.no_grad()
    def predict(self, image_data: Union[bytes, str, Path, Image.Image], top_k: int = 2) -> bool:
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
            image_tensor = self._process_image(image_data)
            # Добавляем размерность батча для модели
            image_tensor = image_tensor.unsqueeze(0).to(self.device)
            
            outputs = self.model(image_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            top_probs, top_indices = torch.topk(probabilities, top_k)
            
            predictions = {}
            for prob, idx in zip(top_probs[0], top_indices[0]):
                predictions[self.class_names[idx]] = float(prob)
            
            # Очистка CUDA памяти, если используется GPU
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            if predictions['plant'] > 0.5:
                return True
            else:
                return False
            
        except Exception as e:
            logger.error(f"Ошибка при предсказании: {str(e)}")
            raise

    def __del__(self):
        """Очистка ресурсов при удалении объекта"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
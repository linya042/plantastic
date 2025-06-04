import logging
from pathlib import Path
from typing import Union
from PIL import Image
import torch
from torchvision import transforms
from pillow_heif import register_heif_opener
from io import BytesIO
from .exceptions import ImageProcessingError
from classifier.config import MODEL_INPUT_SIZE, MAX_IMAGE_SIZE

# Регистрируем обработчик HEIF/HEIC
register_heif_opener()

class ImageProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        self.resize_transform = transforms.Compose([
            transforms.Resize(MAX_IMAGE_SIZE),
            transforms.CenterCrop(MAX_IMAGE_SIZE)
        ])
        
        self.model_transform = transforms.Compose([
            transforms.Resize((MODEL_INPUT_SIZE, MODEL_INPUT_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def _convert_to_pil(self, image_input: Union[bytes, str, Path, Image.Image]) -> Image.Image:
        """
        Конвертация входных данных в PIL Image
        
        Args:
            image_input: Входные данные в одном из форматов:
                - bytes: байты изображения
                - str: путь к файлу
                - Path: путь к файлу
                - Image.Image: PIL изображение
                
        Returns:
            Image.Image: PIL изображение в формате RGB
            
        Raises:
            FileNotFoundError: если файл не найден
            ValueError: если неподдерживаемый тип входных данных
        """
        try:
            if isinstance(image_input, bytes):
                return Image.open(BytesIO(image_input)).convert('RGB')
                
            elif isinstance(image_input, (str, Path)):
                path = Path(image_input)
                if not path.exists():
                    raise FileNotFoundError(f"Файл не найден: {path}")
                return Image.open(path).convert('RGB')
                
            elif isinstance(image_input, Image.Image):
                return image_input.convert('RGB')
                
            else:
                raise ValueError(f"Неподдерживаемый тип входных данных: {type(image_input)}")
                
        except Exception as e:
            self.logger.error(f"Ошибка при конвертации изображения: {str(e)}")
            raise

    def process_image(self, image_input: Union[bytes, str, Path, Image.Image]) -> torch.Tensor:
        """
        Обработка входного изображения
        
        Args:
            image_input: Входные данные в одном из форматов:
                - bytes: байты изображения
                - str: путь к файлу
                - Path: путь к файлу
                - Image.Image: PIL изображение
                
        Returns:
            torch.Tensor: Подготовленный тензор изображения размерности (C, H, W)
            
        Raises:
            ImageProcessingError: При ошибках обработки изображения
        """
        try:
            img = self._convert_to_pil(image_input)
            
            # Сохраняем оригинальные размеры
            original_size = img.size
            self.logger.debug(f"Оригинальный размер изображения: {original_size}")
            
            # Уменьшаем большие изображения
            if max(original_size) > MAX_IMAGE_SIZE:
                img = self.resize_transform(img)
                self.logger.debug(f"Изображение уменьшено до: {img.size}")
            
            # Подготавливаем для модели
            tensor = self.model_transform(img)
            self.logger.debug(f"Размер тензора: {tensor.shape}")
            
            return tensor
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки изображения: {str(e)}")
            raise ImageProcessingError(f"Не удалось обработать изображение: {str(e)}")
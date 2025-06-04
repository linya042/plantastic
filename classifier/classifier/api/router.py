from fastapi import APIRouter, File, UploadFile, HTTPException, status
from pathlib import Path
import logging
from typing import Dict
from ..services.plant_service import PlantService
from ..utils.exceptions import ImageProcessingError, ClassificationError
from ..config.settings import (
    ALLOWED_FORMATS,
    MAX_FILE_SIZE,
    MODEL_PATH,
    CLASS_NAMES_PATH,
    TOP_K
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Инициализация сервиса при старте приложения
try:
    plant_service = PlantService(
        model_path=MODEL_PATH,
        class_names_path=CLASS_NAMES_PATH,
        top_k=TOP_K
    )
except Exception as e:
    logger.critical(f"Ошибка инициализации сервиса: {str(e)}")
    raise

def is_valid_extension(filename: str) -> bool:
    """Проверка расширения файла"""
    ext = Path(filename).suffix.lower()
    return any(ext in extensions for extensions in ALLOWED_FORMATS.values())

@router.post("/classify", response_model=Dict[str, object])
async def classify_plant(file: UploadFile = File(...)):
    """
    Классификация растения по изображению
    
    Args:
        file: Загруженное изображение (JPG, JPEG, PNG, WebP, HEIC, HEIF)
        
    Returns:
        Dict с результатами классификации или сообщением об ошибке
        
    Raises:
        HTTPException: При ошибках обработки или классификации
    """
    if (file.content_type not in ALLOWED_FORMATS and 
        not is_valid_extension(file.filename)):
        supported_formats = [
            ext[1:].upper() 
            for exts in ALLOWED_FORMATS.values() 
            for ext in exts
        ]
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Неверный формат файла. Поддерживаемые форматы: {', '.join(supported_formats)}"
        )
    
    try:
        contents = await file.read(MAX_FILE_SIZE + 1)
        
        if len(contents) > MAX_FILE_SIZE:
            size_mb = MAX_FILE_SIZE / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Размер файла превышает {size_mb:.0f}MB. Пожалуйста, используйте изображение меньшего размера."
            )
        
        logger.info(f"Получен файл: {file.filename} ({file.content_type})")
        logger.debug(f"Размер файла: {len(contents)} bytes")
        
        try:
            predictions = await plant_service.classify_plant(contents)
            
            formatted_predictions = [
                {
                    "name": pred["class_name"].replace("_", " ").title(),
                    "confidence": round(pred["confidence"] * 100, 2)
                }
                for pred in predictions
            ]
            
            return {
                "success": True,
                "data": {
                    "predictions": formatted_predictions
                }
            }
            
        except ImageProcessingError as e:
            logger.error(f"Ошибка обработки изображения: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ошибка обработки изображения: {str(e)}"
            )
        except ClassificationError as e:
            logger.error(f"Ошибка классификации: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при классификации изображения"
            )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.exception(
            f"Неожиданная ошибка при обработке запроса: {str(e)}\n"
            f"Тип файла: {file.content_type}\n"
            f"Имя файла: {file.filename}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )
    finally:
        await file.close()

@router.on_event("shutdown")
async def shutdown_event():
    """Освобождение ресурсов при завершении работы"""
    await plant_service.close()
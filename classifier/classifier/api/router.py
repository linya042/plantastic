from fastapi import APIRouter, File, UploadFile, HTTPException, status
from pathlib import Path
import logging
from typing import Dict, Optional
from datetime import datetime
from ..services.plant_service import PlantService
from ..utils.exceptions import ImageProcessingError, ClassificationError
from ..config.settings import (
    ALLOWED_FORMATS,
    MAX_FILE_SIZE,
    WEIGHT_PATH,
    CLASS_NAMES_PATH,
    TOP_K
)

logger = logging.getLogger(__name__)

plant_service: Optional[PlantService] = None

router = APIRouter(
    prefix="/classifier",
    tags=["Classifier"],
)

async def get_plant_service() -> PlantService:
    """Получение экземпляра PlantService с ленивой инициализацией"""
    global plant_service
    if plant_service is None:
        try:
            logger.info("Инициализация PlantService...")
            plant_service = PlantService(
                model_path=WEIGHT_PATH,
                class_names_path=CLASS_NAMES_PATH,
                top_k=TOP_K
            )
            logger.info("PlantService успешно инициализирован")
        except Exception as e:
            logger.critical(f"Ошибка инициализации PlantService: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Сервис классификации временно недоступен"
            )
    return plant_service


def is_valid_extension(filename: str) -> bool:
    """Проверка расширения файла"""
    if not filename:
        return False
    ext = Path(filename).suffix.lower()
    return any(ext in extensions for extensions in ALLOWED_FORMATS.values())


@router.get("/health")
async def health():
    """Проверка состояния сервиса"""
    try:
        service = await get_plant_service()
        return {
            "status": "healthy",
            "service": "classifier",
            "model_loaded": service is not None
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "classifier",
            "error": str(e)
        }


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

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Имя файла не указано"
        )

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
        
        if len(contents) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Файл пуст"
            )
        
        logger.info(f"Получен файл: {file.filename} ({file.content_type})")
        logger.debug(f"Размер файла: {len(contents)} bytes")
        
        # Получение сервиса и классификация
        service = await get_plant_service()
        try:
            predictions = service.classify_plant(contents) # НАДО СДЕЛАТЬ ФУНКЦИЯЮ АССИНХРОННОЙ
            # from starlette.concurrency import run_in_threadpool
            # predictions = await run_in_threadpool(self.classifier.predict, image_data, top_k=self.top_k)
            
            if not predictions:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Не удалось классифицировать изображение"
                )
            
            formatted_predictions = [
                {
                    "class_name": pred["class_name"],
                    "confidence": round(pred["confidence"], 4)
                }
                for pred in predictions
            ]
            
            return {
                "success": True,
                "data": {
                    "predictions": formatted_predictions,
                    "filename": file.filename,
                    "processed_at": datetime.now()
                }
                                    # Было это -> logger.handlers[0].formatter.formatTime(logging.LogRecord("", 0, "", 0, "", (), None) if logger.handlers else None
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
    global plant_service
    if plant_service:
        try:
            plant_service.close()
            logger.info("PlantService успешно закрыт")
        except Exception as e:
            logger.error(f"Ошибка при закрытии PlantService: {str(e)}")
        finally:
            plant_service = None
from fastapi import APIRouter, File, UploadFile, HTTPException, status
# from PIL import Image #ИЗМЕНЕНО! - удалено
# import os #ИЗМЕНЕНО! - удалено
# from io import BytesIO #ИЗМЕНЕНО! - удалено
import logging  #ИЗМЕНЕНО!

from disease_app.services import run_inference
from disease_app.models import model


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/disease",
    tags=["disease"],)

@router.get("/health")
async def health():
    """Проверка состояния сервиса с обработкой исключений"""
    try:
        if model is not None:
            return {
                "status": "healthy",
                "service": "disease",
                "model_loaded": True
            }
        else:
            error_msg = "Model is not loaded"
            logger.error(f"Health check failed: {error_msg}")
            return {
                "status": "unhealthy",
                "service": "disease",
                "error": error_msg
            }
    except Exception as e:
        logger.error(f"Health check failed with exception: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "disease",
            "error": str(e)
        }


@router.post("/predict/", summary="Распознавание болезни по одному изображению")
async def predict_plant_disease(file: UploadFile = File(...)):
    """
    Отправьте изображение (JPG, PNG), и API вернёт результат.
    """
    # Проверка типа файла
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Имя файла не указано"
        )

    # Проверяем MIME-тип и расширение
    filename = file.filename.lower()
    if not filename.endswith((".jpg", ".jpeg", ".png")):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Неподдерживаемый формат файла"
        )

    try:
        contents = await file.read()
        
        if len(contents) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Файл пуст"
            )
         
        logger.info(f"Получен файл: {file.filename} ({file.content_type})")
        logger.debug(f"Размер файла: {len(contents)} bytes")

        # Запускаем инференс
        result = run_inference(contents)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Не удалось выполнить инференс"
            )


        return {
            "success": True,
            "data": {
                "predictions": result,
                "filename": file.filename,
                "processed_at": logger.handlers[0].formatter.formatTime(
                    logging.LogRecord("", 0, "", 0, "", (), None)
                ) if logger.handlers else None
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при предсказании: {str(e)}"
        )
    
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
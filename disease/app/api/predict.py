from fastapi import APIRouter, File, UploadFile, HTTPException, status
from PIL import Image
import os
from io import BytesIO
from app.services.inference_service import run_inference


router = APIRouter()

@router.post("/predict/", summary="Распознавание болезни по одному изображению")
async def predict_plant_disease(file: UploadFile = File(...)):
    """
    Отправьте изображение (JPG, PNG), и API вернёт результат.
    """

    # Проверяем MIME-тип и расширение
    filename = file.filename.lower()
    if not filename.endswith((".jpg", ".jpeg", ".png")):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Неподдерживаемый формат файла"
        )

    try:
        contents = await file.read()

        image = Image.open(BytesIO(contents)).convert("RGB")

        # Сохраняем во временном файле
        temp_path = "temp.jpg"
        image.save(temp_path, format="JPEG")

        # Запускаем инференс
        result = run_inference(temp_path)
        os.remove(temp_path)

        return {"predictions": result}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при предсказании: {str(e)}"
        )
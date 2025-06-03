from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.predict import router as predict_router

app = FastAPI(
    title="Plant Disease Classifier API",
    description="API для распознавания болезней растений через ConvNeXt-Base",
    version="1.0"
)

# Разрешаем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем маршруты
app.include_router(predict_router, prefix="/api", tags=["Prediction"])

@app.get("/")
def root():
    return {
        "message": "Добро пожаловать! Перейдите /docs для тестирования API"
    }
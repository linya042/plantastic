# Plant Classification Module

Модуль классификации комнатных растений для мини-приложения Telegram. Использует EfficientNetB2 для определения 179 различных видов растений.

## Особенности

- Классификация 179 видов комнатных растений
- Поддержка различных форматов изображений (JPEG, PNG, WebP, HEIC)
- Асинхронная обработка запросов
- Оптимизация для работы в Telegram Mini App
- Обработка изображений высокого разрешения

## Технологии

- Python 3.8+
- PyTorch + TorchVision
- FastAPI
- EfficientNetB2
- Docker

## Установка

1. Клонировать репозиторий:
```bash
git clone https://github.com/your-username/plants_prod.git
cd plants_prod
```

2. Создать виртуальное окружение и активировать его:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Установить зависимости:
```bash
pip install -r requirements.txt
```

4. Скачать веса модели:
```bash
# Поместите файл model_epoch_27.pth в папку data/model_weights/
```

## Использование

### Запуск с помощью Docker:
```bash
docker-compose up -d
```

### Локальный запуск:
```bash
uvicorn src.api.main:app --reload
```

## API Endpoints

- `POST /classify` - Классификация изображения
  - Принимает: multipart/form-data с полем file
  - Возвращает: JSON с предсказаниями

## Структура проекта

```
plants_prod/
├── src/                    # Исходный код
│   ├── api/               # API endpoints
│   ├── models/            # Модели нейронных сетей
│   ├── services/          # Бизнес-логика
│   └── utils/             # Вспомогательные функции
├── data/                   # Данные и веса моделей
├── tests/                 # Тесты
└── docker/                # Docker конфигурация
```

## Разработка

### Запуск тестов:
```bash
pytest
```

### Линтинг:
```bash
flake8 src tests
```

## Лицензия

MIT

## Авторы

- avicesx
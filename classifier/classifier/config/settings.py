import yaml
from pathlib import Path
from typing import Dict, List
import os

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
print(PACKAGE_ROOT)
print(Path(__file__).resolve().parent)
print(Path(__file__).resolve())
CONFIG_FILE = Path(__file__).resolve().parent / "config.yml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

WEIGHT_PATH = Path(PACKAGE_ROOT / config["path"]["weights_path"])
CLASS_NAMES_PATH = Path(PACKAGE_ROOT / config["path"]["class_names_path"])

# Проверка существования файлов
if not WEIGHT_PATH.exists():
    raise FileNotFoundError(f"Файл модели не найден: {WEIGHT_PATH}")
if not CLASS_NAMES_PATH.exists():
    raise FileNotFoundError(f"Файл с именами классов не найден: {CLASS_NAMES_PATH}")

# Параметры изображений
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_FORMATS: Dict[str, List[str]] = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/webp': ['.webp'],
    'image/heic': ['.heic', '.heif']
}

# Параметры модели
MODEL_INPUT_SIZE = 260  # Размер входа для EfficientNetB2
MAX_IMAGE_SIZE = 2048  # Максимальный размер исходного изображения
TOP_K = config["model"]["top_k"]  # Количество возвращаемых предсказаний

# Параметры логирования
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': LOG_LEVEL,
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'error_file': {
            'level': 'ERROR',
            'formatter': 'detailed',
            'class': 'logging.FileHandler',
            'filename': 'error.log',
            'mode': 'a',
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['default', 'error_file'],
            'level': LOG_LEVEL,
            'propagate': True
        }
    }
} 
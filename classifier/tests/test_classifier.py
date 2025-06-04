import sys
from pathlib import Path
import pytest
import torch
from PIL import Image
import logging
import warnings

# Добавляем путь к корневой директории проекта
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Импортируем из пакета classifier
from classifier import PlantService, ImageProcessor
from classifier.config.settings import TOP_K, WEIGHT_PATH, CLASS_NAMES_PATH, MODEL_INPUT_SIZE

TEST_IMAGES = {
    'philodendron_birkin': 'photo_2025-05-28_20-42-13.jpg'
}

TEST_IMAGES_DIR = Path(__file__).parent / 'test_images'

def get_test_image_path(image_name: str) -> Path:
    return TEST_IMAGES_DIR / image_name

warnings.filterwarnings("ignore", category=UserWarning)
logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

@pytest.fixture
def setup_test_env():
    """Setup test environment"""
    try:
        service = PlantService(
            model_path=WEIGHT_PATH,
            class_names_path=CLASS_NAMES_PATH,
            top_k=TOP_K
        )
        return service
    except Exception as e:
        logger.error(f"Ошибка инициализации: {str(e)}")
        raise

def test_service_initialization(setup_test_env):
    """Test service initialization"""
    service = setup_test_env
    assert isinstance(service, PlantService)
    assert service.model is not None
    assert service.class_names is not None
    assert service.top_k == TOP_K

TEST_IMAGE_PATH = get_test_image_path(next(iter(TEST_IMAGES.values())))

def test_image_processing():
    """Тест обработки изображения"""
    processor = ImageProcessor()
    img = Image.open(TEST_IMAGE_PATH)
    assert img is not None
    
    # Проверяем обработку изображения
    tensor = processor.process_image(img)
    
    # Проверяем формат выходного тензора
    assert isinstance(tensor, torch.Tensor)
    assert len(tensor.shape) == 3  # [channels, height, width]
    assert tensor.shape[0] == 3    # RGB channels 
    assert tensor.shape[1] == MODEL_INPUT_SIZE  # Height 
    assert tensor.shape[2] == MODEL_INPUT_SIZE  # Width
    
def test_classification_output(setup_test_env):
    """Test classification output format"""
    service = setup_test_env
    predictions = service.classify_plant(TEST_IMAGE_PATH)
    
    assert isinstance(predictions, list)
    assert len(predictions) == TOP_K
    
    for pred in predictions:
        assert isinstance(pred, dict)
        assert 'class_name' in pred
        assert 'confidence' in pred
        assert isinstance(pred['confidence'], float)
        assert 0 <= pred['confidence'] <= 1

def test_top_k_parameter(setup_test_env):
    """Test top_k parameter behavior"""
    service = setup_test_env
    
    predictions = service.classify_plant(TEST_IMAGE_PATH)
    assert len(predictions) == TOP_K

def test_confidence_values(setup_test_env):
    """Проверка значений уверенности"""
    service = setup_test_env
    predictions = service.classify_plant(TEST_IMAGE_PATH)
    
    total_confidence = sum(pred['confidence'] for pred in predictions)
    assert 0.99 <= total_confidence <= 1.01

def test_different_image_sizes(setup_test_env):
    """Проверка работы с изображениями разного размера"""
    processor = ImageProcessor()
    img = Image.open(TEST_IMAGE_PATH).resize((512, 512))
    tensor = processor.process_image(img)
    
    assert tensor.shape[1] == 224  # Height
    assert tensor.shape[2] == 224  # Width

def test_classification_results(setup_test_env):
    """Проверка и вывод результатов классификации"""
    service = setup_test_env
    
    print(f"\nАнализ изображения: {TEST_IMAGE_PATH.name}")
    print("-" * 50)
    
    predictions = service.classify_plant(TEST_IMAGE_PATH)
    
    print("Результаты классификации:")
    print("-" * 50)
    for i, pred in enumerate(predictions, 1):
        confidence_percent = pred['confidence'] * 100
        confidence_bar = "█" * int(confidence_percent // 10) + "▒" * int(10 - confidence_percent // 10)
        print(f"{i}. {pred['class_name']}")
        print(f"   Уверенность: {confidence_bar} {confidence_percent:.2f}%")
    print("-" * 50)
    
    assert len(predictions) > 0
    assert predictions[0]['confidence'] >= predictions[-1]['confidence']

def test_multiple_images(setup_test_env):
    """Проверка классификации разных изображений"""
    service = setup_test_env
    
    print("\nТестирование разных изображений:")
    print("=" * 50)
    
    for plant_name, img_name in TEST_IMAGES.items():
        img_path = get_test_image_path(img_name)
        if not img_path.exists():
            print(f"Пропускаем {plant_name} ({img_name}) - файл не найден")
            continue
            
        print(f"\nИзображение: {plant_name} ({img_name})")
        print("-" * 50)
        
        predictions = service.classify_plant(img_path)
        for i, pred in enumerate(predictions, 1):
            confidence_percent = pred['confidence'] * 100
            confidence_bar = "█" * int(confidence_percent // 10) + "▒" * int(10 - confidence_percent // 10)
            print(f"{i}. {pred['class_name']}")
            print(f"   Уверенность: {confidence_bar} {confidence_percent:.2f}%")

if __name__ == "__main__":
    pytest.main([__file__])
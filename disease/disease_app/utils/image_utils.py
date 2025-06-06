from PIL import Image
from torchvision import transforms
from disease_app.models import device
from io import BytesIO


transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

def preprocess_image(image_data):
    """Обработка изображения перед подачей в модель"""
    try:
        if isinstance(image_data, bytes):
            image = Image.open(BytesIO(image_data)).convert('RGB')
            
        elif isinstance(image_data, str):
            path = image_data
            if not path.exists():
                raise FileNotFoundError(f"Файл не найден: {path}")
            image = Image.open(path).convert('RGB')
            
        elif isinstance(image_data, Image.Image):
            image = image_data.convert('RGB')
            
        else:
            raise ValueError(f"Неподдерживаемый тип входных данных: {type(image_data)}")
            
    except Exception as e:
        raise
    
    
    return transform(image).unsqueeze(0).to(device)
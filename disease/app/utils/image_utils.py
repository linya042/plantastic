from PIL import Image
import os
from torchvision import transforms
from app.models.model_loader import device

transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

def preprocess_image(image_path):
    """Обработка изображения перед подачей в модель"""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Изображение не найдено: {image_path}")

    image = Image.open(image_path).convert("RGB")
    return transform(image).unsqueeze(0).to(device)
import torch
from torchvision import models
import torch.nn as nn
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
print(PACKAGE_ROOT)
print(Path(__file__).resolve().parent.parent)
print(Path(__file__).resolve().parent)
print(Path(__file__).resolve())


# Загрузка классов
CLASS_NAMES_PATH = Path(PACKAGE_ROOT / "models/class_names.txt")
if not CLASS_NAMES_PATH.exists():
    raise FileNotFoundError(f"Файл class_names.txt не найден по пути: {CLASS_NAMES_PATH.resolve()}. PACKAGE_ROOT: {PACKAGE_ROOT}")
print(CLASS_NAMES_PATH)

MODEL_PATH =  Path(PACKAGE_ROOT / "models/trained_convnext_best.pth")
if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Файл trained_convnext_best.pth не найден по пути: {MODEL_PATH.resolve()}. PACKAGE_ROOT: {PACKAGE_ROOT}")
print(MODEL_PATH)

with open(CLASS_NAMES_PATH, 'r') as f:
    CLASS_NAMES = [line.strip() for line in f.readlines()]

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


# Модель ConvNeXt-Base
def load_model(model_path=MODEL_PATH):
    model = models.convnext_base(weights=None)
    num_classes = len(CLASS_NAMES)

    # Заменяем финальный слой под ваши классы
    model.classifier[2] = nn.Sequential(
        nn.Dropout(p=0.7),
        nn.Linear(model.classifier[2].in_features, num_classes)
    )

    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device).eval()
    print("[+] Модель ConvNeXt-Base загружена")
    return model

model = load_model()
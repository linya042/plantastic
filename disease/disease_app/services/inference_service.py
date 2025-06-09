from disease_app.models import model, CLASS_NAMES
from disease_app.utils import preprocess_image
import torch

def run_inference(image_data):
    """Запуск инференса и возврат топ-3 классов"""
    input_tensor = preprocess_image(image_data)

    with torch.no_grad():
        output = model(input_tensor)
        probabilities = torch.softmax(output, dim=1)[0]  # Вероятности классов

    # Получаем индексы топ-3 классов
    top_probs, top_indices = torch.topk(probabilities, 3)

    # Преобразуем в список словарей
    results = []
    for prob, idx in zip(top_probs, top_indices):
        results.append({
            "class_name": CLASS_NAMES[idx.item()].replace("_", " ").title(),
            "confidence": round(prob.item(), 4) #f"{prob.item() * 100:.2f}%"
        })

    return results
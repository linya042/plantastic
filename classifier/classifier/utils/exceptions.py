class ImageProcessingError(Exception):
    """Исключение при обработке изображения"""
    def __init__(self, message: str = "Ошибка при обработке изображения", details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class ClassificationError(Exception):
    """Исключение при классификации"""
    def __init__(self, message: str = "Ошибка при классификации", details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
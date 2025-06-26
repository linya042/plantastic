import logging
from typing import Dict, Optional, Any
import time
import json
import hashlib
import hmac
# import urllib.parse
from urllib.parse import unquote, parse_qsl
from fastapi import HTTPException
from datetime import datetime, timedelta
import jwt


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelegramDataValidator:
    def __init__(self, bot_token: str) -> None:
        """
        Инициализация валидатора Telegram Web App initData.
        Согласно документации Telegram: https://core.telegram.org/bots/webapps#checking-authorization

        Args:
            bot_token: Токен вашего Telegram бота
        """
        self.bot_token = bot_token
        
        # Секретный ключ для подписи данных Telegram и JWT.
        # Используется SHA256 хеш токена бота.
        self.secret_key = hmac.new(
            key="WebAppData".encode(),
            msg=bot_token.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
    

    def validate_init_data(self, init_data_raw: str) -> Dict[str, Any]:
        """
        Валидирует initData, полученную от Telegram Web App.
        Выбрасывает HTTPException, если валидация не удалась.
        """
        logger.info(f"Получены init_data_raw для валидации: {init_data_raw}")
        
        hash_from_data = None
        user_data_for_jwt = None

        # Разбираем initData на пары ключ-значение. parse_qsl уже выполняет URL-декодирование.
        parsed_data = parse_qsl(init_data_raw)
        
        # Создаем словарь из parsed_data для более удобного доступа и удаления 'hash'
        parsed_data_dict = dict(parsed_data)

        if 'hash' not in parsed_data_dict:
            logger.error("Отсутствует hash в данных инициализации initData.")
            raise HTTPException(status_code=400, detail="Отсутствует hash в данных инициализации.")
        
        hash_from_data = parsed_data_dict.pop('hash') # Удаляем hash перед сортировкой и объединением

        # Формируем строку для проверки хеша:
        # Все параметры, кроме 'hash', сортируются по алфавиту и соединяются через '\n'.
        # Значения должны быть оригинальными, как они были получены после parse_qsl,
        # без дополнительной обработки (кроме unquote, если это JSON-строка для 'user').
        data_check_string_parts = []
        for key, value in sorted(parsed_data_dict.items()):
            data_check_string_parts.append(f"{key}={value}")
        
        data_check_string = "\n".join(data_check_string_parts)
        
        logger.info(f"Сформирована data_check_string для валидации: {data_check_string}")

        # Вычисляем ожидаемый хеш с использованием HMAC-SHA256 и секретного ключа
        hmac_hash = hmac.new(self.secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()

        # Сравниваем полученный хеш с ожидаемым.
        # Используем hmac.compare_digest для защиты от атак по времени.
        if not hmac.compare_digest(hmac_hash, hash_from_data):
            logger.warning(f"Неверный hash: вычисленный={hmac_hash}, полученный={hash_from_data}")
            raise HTTPException(status_code=401, detail="Ошибка аутентификации: Неверный hash - данные могли быть подделаны")

        # После успешной валидации хеша, обрабатываем данные пользователя, если они присутствуют
        # Поле 'user' в initData — это URL-закодированная JSON-строка.
        # Ее нужно явно URL-декодировать, а затем разобрать как JSON.
        user_raw_json_str = parsed_data_dict.get('user')
        if user_raw_json_str:
            try:
                user_data_for_jwt = json.loads(user_raw_json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка декодирования JSON для поля 'user': {e}")
                raise HTTPException(status_code=400, detail="Неверный формат данных пользователя в initData.")
            except Exception as e:
                logger.error(f"Неожиданная ошибка при парсинге user data: {e}")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при парсинге user data.")
        
        # Проверяем, был ли user_data_for_jwt успешно разобран
        if user_data_for_jwt is None:
            logger.warning("Поле 'user' отсутствует или не содержит валидных данных в initData.")
            raise HTTPException(status_code=400, detail="Отсутствуют данные пользователя в initData.")
        auth_date = int(parsed_data_dict.get('auth_date', 0))
        current_time = int(time.time())
        
        if current_time - auth_date > 3600: # 3600 секунд = 1 час
            logger.warning(f"Данные устарели. Время аутентификации истекло. auth_date: {auth_date}, current_time: {current_time}")
            raise HTTPException(status_code=401, detail="Данные устарели. Время аутентификации истекло.")

        return user_data_for_jwt
        return user_data
   

    def create_jwt_token(self, user_data: dict) -> str:
        """
        Создает JWT (JSON Web Token) для аутентифицированного пользователя.
        Токен содержит данные пользователя и срок действия (24 часа).
        """
        # Полезная нагрузка (payload) для JWT
        payload = {
            'user_id': user_data.get('id'),
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name'),
            'username': user_data.get('username'),
            'photo_url': user_data.get('photo_url'),
            'auth_date': user_data.get('auth_date', int(time.time())), # Использовать auth_date из initData или текущее время
            'exp': datetime.utcnow() + timedelta(hours=24), # Срок действия токена 24 часа
            'telegram_auth': True # Пользовательский флаг для идентификации токена как сгенерированного Telegram Auth
        }
        
        # Кодируем токен с использованием секретного ключа и алгоритма HS256
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def verify_jwt_token(self, token: str) -> dict:
        """
        Проверяет JWT токен
        """
        try:
            # Декодируем токен с использованием секретного ключа и разрешенных алгоритмов
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            # Проверяем, что токен был выдан нашей системой аутентификации Telegram
            if not payload.get('telegram_auth'):
                raise jwt.InvalidTokenError("Токен недействителен или не выдан системой Telegram.")
            return payload
        except jwt.ExpiredSignatureError as exp_err:
            # Если срок действия токена истек
            raise HTTPException(status_code=401, detail="Токен истек. Пожалуйста, войдите снова.") from exp_err
        except jwt.InvalidTokenError as invalid_err:
            # Если токен недействителен (неверная подпись, структура и т.д.)
            raise HTTPException(status_code=401, detail="Неверный токен. Доступ запрещен.") from invalid_err
        except Exception as e:
            # Для любых других неожиданных ошибок во время проверки токена
            raise HTTPException(status_code=401, detail=f"Неизвестная ошибка при проверке токена: {e}")

import logging
from typing import Dict, Optional, Any
import time
import json
import hashlib
import hmac
import urllib.parse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelegramDataValidator:
    def __init__(self, bot_token: str) -> None:
        """
        Инициализация валидатора Telegram Web App initDat.
        Согласно документации Telegram: https://core.telegram.org/bots/webapps#checking-authorization

        Args:
            bot_token: Токен вашего Telegram бота
        """
        self.bot_token = bot_token
        # Создаем секретный ключ из токена бота
        self.secret_key = hmac.new(
            key="WebAppData".encode(),
            msg=bot_token.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
    
    def validate_init_data(self, init_data: str) -> Optional[Dict[str, Any]]:
        """
        Валидирует initData от Telegram WebApp.
        
        Args:
            init_data: Строка initData от Telegram
            
        Returns:
            Словарь с данными пользователя если валидация прошла успешно, None - если нет
        """
        if not init_data or not init_data.strip():
            logger.warning("Пустая строка initData")
            return None
        
        try:
            logger.info("Начинаем валидацию initData от Telegram")
            
            # Парсим URL-encoded строку initData на компоненты
            parsed_data = urllib.parse.parse_qs(init_data)
            
            # Получаем хеш из данных
            received_hash = parsed_data.get('hash', [None])[0]
            if not received_hash:
                logger.warning("Отсутствует hash в initData")
                return None
            
            # Удаляем hash из данных для проверки подписи
            data_check_string_parts = []
            for key in sorted(parsed_data.keys()):
                if key != 'hash':
                    decoded_value = urllib.parse.unquote_plus(parsed_data[key][0])
                    data_check_string_parts.append(f"{key}={decoded_value}")
            
            data_check_string = '\n'.join(data_check_string_parts)
            
            # Вычисляем ожидаемый хеш
            expected_hash = hmac.new(
                key=self.secret_key,
                msg=data_check_string.encode('utf-8'),
                digestmod=hashlib.sha256
            ).hexdigest()
            
            # Сравниваем хеши
            if not hmac.compare_digest(expected_hash, received_hash):
                logger.warning("Невалидная подпись initData")
                return None
            
            # Проверяем время создания (auth_date)
            auth_date_list  = parsed_data.get('auth_date')
            if auth_date_list:
                try:
                    auth_timestamp = int(auth_date_list[0])
                    current_timestamp = int(time.time())
                    # Проверяем, что данные не старше 24 часов
                    if current_timestamp - auth_timestamp > 86400:
                        logger.warning("InitData устарели (старше 24 часов)")
                        return None
                except (ValueError, IndexError):
                    logger.warning("Невалидный auth_date в initData")
                    return None

            # Парсим данные пользователя
            user_data = self._extract_user_data(parsed_data)
            
            if user_data:
                logger.info(f"InitData успешно валидирована для пользователя {user_data.get('id')}")
                return user_data
            else:
                logger.warning("Не удалось извлечь данные пользователя из initData")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при валидации initData: {e}", exc_info=True)
            return None
    
    def _extract_user_data(self, parsed_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Извлекает данные пользователя из распарсенных данных.
        
        Args:
            parsed_data: Распарсенные данные от Telegram
            
        Returns:
            Словарь с данными пользователя
        """
        try:
            # Получаем строку с данными пользователя
            user_json_list = parsed_data.get('user')
            if not user_json_list:
                logger.warning("Отсутствуют данные пользователя в initData")
                return None
            
            user_json_str = user_json_list[0]
            
            # Парсим JSON с данными пользователя
            user_data = json.loads(urllib.parse.unquote(user_json_str))
            
            # Проверяем наличие обязательного поля id
            if 'id' not in user_data:
                logger.warning("Отсутствует id пользователя в данных")
                return None
            
            # Проверяем, что id является числом
            user_id = user_data.get('id')
            if not isinstance(user_id, int):
                logger.warning(f"ID пользователя должен быть числом, получен: {type(user_id)} - {user_id}")
                return None
            
            return {
                'id': user_data.get('id'),
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'username': user_data.get('username'),
                'language_code': user_data.get('language_code'),
                'is_bot': user_data.get('is_bot'),
                'is_premium': user_data.get('is_premium'),
                'photo_url': user_data.get('photo_url')
            }
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Ошибка при парсинге данных пользователя: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при извлечении данных пользователя: {e}", exc_info=True)
            return None
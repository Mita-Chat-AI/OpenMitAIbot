"""
Minimax Voice Clone API - Утилиты для работы с клонированием голоса через Minimax
"""
import aiohttp
import json
import re
from loguru import logger
from typing import Optional

from ...settings.main import config


def validate_and_clean_voice_id(voice_id: str) -> str | None:
    """
    Валидирует и очищает voice_id перед отправкой в API.
    
    Согласно Minimax API, voice_id должен:
    - Начинаться с буквы (обычно "voice_")
    - Не содержать пробелов в начале/конце
    - Иметь минимальную длину
    
    Args:
        voice_id: Исходный voice_id
        
    Returns:
        Очищенный voice_id или None если невалидный
    """
    if not voice_id:
        return None
    
    original_voice_id = voice_id  # Сохраняем для логирования
    
    # Убираем пробелы в начале и конце
    voice_id = voice_id.strip()
    
    # Проверяем, что voice_id не пустой
    if not voice_id:
        logger.error("voice_id пустой после очистки")
        return None
    
    # Убираем HTML-теги (например, <voice_id>...</voice_id>)
    # Убираем теги вида <voice_id>...</voice_id> или <...>
    voice_id = re.sub(r'<[^>]+>', '', voice_id)
    voice_id = voice_id.strip()
    
    # Убираем кавычки если есть (на случай если скопировали с кавычками)
    if voice_id.startswith('"') and voice_id.endswith('"'):
        voice_id = voice_id[1:-1].strip()
    if voice_id.startswith("'") and voice_id.endswith("'"):
        voice_id = voice_id[1:-1].strip()
    
    # Убираем угловые скобки если остались (на случай <voice_id> без закрывающего тега)
    if voice_id.startswith('<'):
        voice_id = voice_id.lstrip('<').strip()
    if voice_id.endswith('>'):
        voice_id = voice_id.rstrip('>').strip()
    
    # Проверяем, что voice_id не пустой после всех очисток
    if not voice_id:
        logger.error(f"voice_id пустой после очистки от HTML-тегов. Исходное значение: {original_voice_id[:50]}")
        return None
    
    # Проверяем минимальную длину (voice_id обычно длинный)
    if len(voice_id) < 5:
        logger.error(f"voice_id слишком короткий: {voice_id}")
        return None
    
    # КРИТИЧНО: Проверяем первый символ - должен быть буквой (a-z, A-Z)
    # Minimax API требует, чтобы voice_id начинался с буквы
    # ВАЖНО: voice_id может быть любым (даже начинаться с "moss_audio_"), 
    # главное - первый символ должен быть буквой
    first_char = voice_id[0]
    if not first_char.isalpha():
        logger.error(
            f"❌ Невалидный первый символ voice_id: '{first_char}' (должен быть буквой)\n"
            f"   Исходное значение: {original_voice_id[:50]}...\n"
            f"   После очистки: {voice_id[:50]}...\n"
            f"   Первые 10 символов: '{voice_id[:10]}'"
        )
        return None
    
    # Логируем для отладки (только если было изменение)
    if original_voice_id != voice_id:
        logger.info(
            f"🧹 Очищен voice_id от HTML-тегов/кавычек:\n"
            f"   Было: {original_voice_id[:50]}...\n"
            f"   Стало: {voice_id[:30]}..."
        )
    
    logger.debug(
        f"✅ Валидированный voice_id: первый символ='{first_char}', "
        f"длина={len(voice_id)}, "
        f"первые 30 символов: {voice_id[:30]}..."
    )
    return voice_id


async def generate_minimax_voice(
    text: str,
    voice_id: Optional[str] = None,
    file_id: Optional[str] = None,
    prompt_audio_file_id: Optional[str] = None,
    prompt_text: Optional[str] = None,
    model: str = "speech-2.6-hd",
    need_noise_reduction: bool = False,
    need_volumn_normalization: bool = False,
    api_key: Optional[str] = None
) -> Optional[bytes]:
    """
    Генерирует голосовое сообщение через Minimax Voice Clone API.
    
    Args:
        text: Текст для озвучивания
        voice_id: ID клонированного голоса
        file_id: file_id клонированного голоса (опционально)
        prompt_audio_file_id: file_id промпт-аудио для клонирования
        prompt_text: Текст промпта для клонирования
        model: Модель для генерации (по умолчанию "speech-2.6-hd")
        need_noise_reduction: Нужна ли редукция шума
        need_volumn_normalization: Нужна ли нормализация громкости
        api_key: API ключ Minimax (если не указан, берется из config)
        
    Returns:
        Аудио в формате bytes или None при ошибке
    """
    if not api_key:
        # Используем отдельный ключ для Voice API если указан, иначе используем AI ключ
        if config.voice_config.minimax_voice_api_key:
            api_key = config.voice_config.minimax_voice_api_key.get_secret_value()
        else:
            api_key = config.ai_config.api_key.get_secret_value()
    
    base_url = config.voice_config.minimax_voice_base_url
    url = f"{base_url}/voice_clone"
    
    # Логируем информацию для отладки (без самого ключа)
    logger.debug(f"Используется API ключ длиной: {len(api_key)} символов")
    logger.debug(f"Base URL: {base_url}")
    
    # Формируем данные запроса согласно документации Minimax
    # Есть два режима:
    # 1. Если есть voice_id - используем только его (голос уже создан)
    # 2. Если нет voice_id, но есть file_id - создаем голос на лету с clone_prompt
    
    payload = {
        "text": text,
        "model": model
    }
    
    # Режим 1: Используем уже созданный голос (voice_id)
    cleaned_voice_id = None
    if voice_id:
        # Валидируем и очищаем voice_id
        cleaned_voice_id = validate_and_clean_voice_id(voice_id)
        if not cleaned_voice_id:
            logger.error(f"❌ Невалидный voice_id: {voice_id}")
            return None
        
        payload["voice_id"] = cleaned_voice_id
        # При использовании voice_id не нужны file_id и clone_prompt
        logger.debug(f"Используется режим с voice_id (голос уже создан): {cleaned_voice_id[:30]}...")
    
    # Режим 2: Создаем голос на лету (file_id + clone_prompt)
    elif file_id:
        payload["file_id"] = file_id
        
        # Добавляем clone_prompt (обязательно для клонирования)
        clone_prompt = {}
        if prompt_audio_file_id:
            clone_prompt["prompt_audio"] = prompt_audio_file_id
        else:
            # Если prompt_audio не указан, используем file_id
            clone_prompt["prompt_audio"] = file_id
        
        if prompt_text:
            clone_prompt["prompt_text"] = prompt_text
        else:
            # Используем дефолтный текст если не указан
            clone_prompt["prompt_text"] = "This voice sounds natural and pleasant."
        
        payload["clone_prompt"] = clone_prompt
        logger.debug("Используется режим с file_id (создание голоса на лету)")
    
    else:
        logger.error("Не указан ни voice_id, ни file_id для Minimax Voice Clone (нужен хотя бы один)")
        return None
    
    # Добавляем опциональные параметры только если они True
    if need_noise_reduction:
        payload["need_noise_reduction"] = True
    if need_volumn_normalization:
        payload["need_volumn_normalization"] = True
    
    # Согласно документации Minimax, используется формат "Bearer {api_key}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        logger.info(f"Отправка запроса к Minimax Voice Clone API: {url}")
        logger.debug(f"Payload: {payload}")
        logger.debug(f"Authorization: Bearer {api_key[:30]}... (первые 30 символов)")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ Minimax Voice Clone API вернул ошибку {response.status}: {error_text}")
                    
                    # Парсим ошибку для более понятного сообщения
                    try:
                        error_data = json.loads(error_text)
                        base_resp = error_data.get('base_resp', {})
                        status_code = base_resp.get('status_code')
                        status_msg = base_resp.get('status_msg', '')
                        
                        # Специальная обработка ошибки с voice_id
                        if status_code == 2013 or 'voice_id first character' in status_msg.lower():
                            used_voice_id = cleaned_voice_id if cleaned_voice_id else (voice_id if voice_id else "не указан")
                            first_char_info = ""
                            if isinstance(used_voice_id, str) and len(used_voice_id) > 0:
                                first_char = used_voice_id[0]
                                first_char_info = f"\n   Первый символ: '{first_char}' (код Unicode: {ord(first_char)})"
                                if not first_char.isalpha():
                                    first_char_info += f" ❌ НЕ БУКВА!"
                                else:
                                    first_char_info += f" ✅ буква"
                            
                            logger.error(
                                f"❌ Ошибка формата voice_id (код {status_code}): {status_msg}\n"
                                f"💡 Minimax API требует, чтобы voice_id начинался с БУКВЫ (a-z, A-Z)\n"
                                f"   Использованный voice_id: {used_voice_id[:50] if isinstance(used_voice_id, str) else 'не указан'}...{first_char_info}\n"
                                f"   💡 Проверьте:\n"
                                f"   1. voice_id должен начинаться с буквы (обычно 'voice_')\n"
                                f"   2. Нет ли лишних пробелов или символов в начале\n"
                                f"   3. Правильно ли скопирован voice_id из ответа API"
                            )
                        else:
                            logger.error(f"❌ Minimax API ошибка (код {status_code}): {status_msg}")
                    except:
                        pass
                    
                    return None
                    
                # Проверяем Content-Type
                content_type = response.headers.get('Content-Type', '')
                logger.debug(f"Content-Type ответа: {content_type}")
                
                # Получаем аудио
                audio_bytes = await response.read()
                
                if not audio_bytes:
                    logger.error("Minimax Voice Clone API вернул пустой ответ")
                    return None
                
                # Проверяем минимальный размер аудио (обычно аудио больше 1KB)
                if len(audio_bytes) < 1024:
                    logger.warning(f"⚠️ Подозрительно маленький размер ответа: {len(audio_bytes)} байт")
                    # Пробуем прочитать как текст/JSON для диагностики
                    try:
                        error_text = audio_bytes.decode('utf-8')
                        logger.error(f"❌ Ответ API (как текст): {error_text}")
                        
                        # Пробуем распарсить как JSON
                        try:
                            import json
                            error_data = json.loads(error_text)
                            if isinstance(error_data, dict):
                                # Извлекаем сообщение об ошибке
                                base_resp = error_data.get('base_resp', {})
                                error_msg = base_resp.get('status_msg', error_data.get('error', error_data.get('message', str(error_data))))
                                logger.error(f"❌ Minimax Voice Clone API вернул ошибку: {error_msg}")
                        except:
                            pass
                        
                        return None
                    except UnicodeDecodeError:
                        # Не текст, возможно бинарные данные, но слишком маленькие
                        logger.error(f"❌ Ответ слишком маленький для аудио: {len(audio_bytes)} байт")
                        return None
                
                # Успех!
                logger.success(f"✅ Minimax Voice Clone: сгенерировано {len(audio_bytes)} байт")
                return audio_bytes
                
    except aiohttp.ClientError as e:
        logger.error(f"Ошибка подключения к Minimax Voice Clone API: {e}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при обращении к Minimax Voice Clone API: {e}")
        return None


async def create_voice_from_file_id(
    file_id: str,
    prompt_audio_file_id: Optional[str] = None,
    prompt_text: Optional[str] = None,
    model: str = "speech-2.6-hd",
    api_key: Optional[str] = None
) -> Optional[str]:
    """
    Создает клонированный голос из file_id и возвращает voice_id.
    
    Args:
        file_id: file_id загруженного аудио файла
        prompt_audio_file_id: file_id промпт-аудио (если отличается от file_id)
        prompt_text: Текст промпта для клонирования
        model: Модель для генерации (по умолчанию "speech-2.6-hd")
        api_key: API ключ Minimax (если не указан, берется из config)
        
    Returns:
        voice_id или None при ошибке
    """
    if not api_key:
        # Используем отдельный ключ для Voice API если указан, иначе используем AI ключ
        if config.voice_config.minimax_voice_api_key:
            api_key = config.voice_config.minimax_voice_api_key.get_secret_value()
        else:
            api_key = config.ai_config.api_key.get_secret_value()
    
    base_url = config.voice_config.minimax_voice_base_url
    url = f"{base_url}/voice_clone"
    
    # Формируем payload для создания голоса (БЕЗ text!)
    payload = {
        "file_id": file_id,
        "model": model
    }
    
    # Добавляем clone_prompt
    clone_prompt = {}
    if prompt_audio_file_id:
        clone_prompt["prompt_audio"] = prompt_audio_file_id
    else:
        clone_prompt["prompt_audio"] = file_id
    
    if prompt_text:
        clone_prompt["prompt_text"] = prompt_text
    else:
        clone_prompt["prompt_text"] = "This voice sounds natural and pleasant."
    
    payload["clone_prompt"] = clone_prompt
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        logger.info(f"Создание голоса из file_id: {file_id}")
        logger.debug(f"Payload: {payload}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_text = await response.text()
                
                if response.status != 200:
                    logger.error(f"❌ Ошибка создания голоса {response.status}: {response_text}")
                    
                    # Пробуем распарсить ошибку для более понятного сообщения
                    try:
                        error_data = json.loads(response_text)
                        base_resp = error_data.get('base_resp', {})
                        status_code = base_resp.get('status_code')
                        status_msg = base_resp.get('status_msg', '')
                        logger.error(f"   Код ошибки: {status_code}, Сообщение: {status_msg}")
                    except:
                        pass
                    
                    return None
                
                # Парсим JSON ответ
                try:
                    response_data = json.loads(response_text)
                    
                    # Проверяем наличие voice_id в ответе
                    voice_id = response_data.get("voice_id")
                    if voice_id:
                        # ВАЖНО: voice_id может быть любым (даже начинаться с "moss_audio_")
                        # Это нормально - API возвращает то, что нужно использовать
                        logger.success(f"✅ Голос создан, voice_id: {voice_id}")
                        logger.debug(f"   Формат voice_id: начинается с '{voice_id[0] if voice_id else 'N/A'}' (длина: {len(voice_id)})")
                        return voice_id
                    else:
                        logger.error(f"❌ В ответе API нет voice_id: {response_data}")
                        return None
                        
                except json.JSONDecodeError:
                    logger.error(f"❌ Не удалось распарсить JSON ответ: {response_text}")
                    return None
                    
    except aiohttp.ClientError as e:
        logger.error(f"Ошибка подключения к Minimax Voice Clone API: {e}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при создании голоса: {e}")
        return None


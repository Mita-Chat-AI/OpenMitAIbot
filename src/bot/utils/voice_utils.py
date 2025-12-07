"""
Voice Utilities - Утилиты для работы с голосом

Содержит функции для:
- Генерации речи через Edge TTS (библиотека)
- Обработки аудио (эффекты)
"""
from io import BytesIO
from typing import Optional

import edge_tts
from loguru import logger


async def generate_edge_tts(
    text: str,
    voice: str = "ru-RU-SvetlanaNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz"
) -> Optional[bytes]:
    """
    Генерирует речь через Microsoft Edge TTS (библиотека, без API).
    
    Edge TTS использует нейросетевые голоса Microsoft. Работает без API ключа.
    
    Args:
        text: Текст для озвучивания
        voice: ID голоса (см. список ниже)
        rate: Скорость речи ("-50%" до "+100%")
        pitch: Высота голоса ("-50Hz" до "+50Hz")
        
    Returns:
        Аудио в формате MP3 (bytes) или None при ошибке
        
    Популярные русские голоса:
        - ru-RU-SvetlanaNeural - женский (похож на Миту!)
        - ru-RU-DariyaNeural - женский (молодой)
        - ru-RU-DmitryNeural - мужской
        
    Популярные английские голоса:
        - en-US-JennyNeural - женский
        - en-US-GuyNeural - мужской
        
    Example:
        >>> audio = await generate_edge_tts(
        ...     text="Привет! Я Мита!",
        ...     voice="ru-RU-SvetlanaNeural",
        ...     rate="+10%"
        ... )
    """
    try:
        # Создаём communicate объект
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch
        )
        
        # Собираем аудио в буфер
        audio_buffer = BytesIO()
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])
        
        audio_buffer.seek(0)
        result = audio_buffer.read()
        
        if len(result) == 0:
            logger.error("Edge TTS вернул пустой аудио буфер")
            return None
        
        logger.success(f"Edge TTS: сгенерировано {len(result)} байт для голоса {voice}")
        return result
        
    except Exception as e:
        logger.error(f"Edge TTS ошибка: {e}")
        return None


def map_person_to_voice(person: str) -> str:
    """
    Маппинг имени персонажа на голос Edge TTS.
    
    Args:
        person: Имя персонажа (например, "CrazyMita")
        
    Returns:
        ID голоса Edge TTS
    """
    # Маппинг персонажей на голоса
    voice_map = {
        "CrazyMita": "ru-RU-SvetlanaNeural",  # Женский русский
        "Mita": "ru-RU-SvetlanaNeural",
        "default": "ru-RU-SvetlanaNeural"
    }
    
    return voice_map.get(person, voice_map["default"])


def map_pitch_int_to_hz(pitch_int: int) -> str:
    """
    Конвертирует pitch из int (0-20) в формат Edge TTS ("+0Hz").
    
    Args:
        pitch_int: Pitch как int (0-20, где 10 = нормальный)
        
    Returns:
        Pitch в формате Edge TTS ("+0Hz", "+10Hz", "-5Hz" и т.д.)
    """
    # Конвертируем: 0-20 -> -10Hz до +10Hz
    # 10 = 0Hz, 0 = -10Hz, 20 = +10Hz
    hz_value = (pitch_int - 10) * 1  # 1 Hz на единицу
    sign = "+" if hz_value >= 0 else ""
    return f"{sign}{hz_value}Hz"


async def get_available_voices(language_filter: str = "ru") -> list[dict]:
    """
    Получает список доступных голосов Edge TTS.
    
    Args:
        language_filter: Фильтр по языку ("ru", "en", "ja" и т.д.)
        
    Returns:
        Список словарей с информацией о голосах
        
    Example:
        >>> voices = await get_available_voices("ru")
        >>> for v in voices:
        ...     print(f"{v['ShortName']}: {v['Gender']}")
    """
    voices = await edge_tts.list_voices()
    
    if language_filter:
        voices = [v for v in voices if v["Locale"].startswith(language_filter)]
    
    return voices


"""
RVC Voice Conversion API Service
Легковесный FastAPI сервис для конвертации голоса через RVC
Оптимизирован для работы на хостинге с ограниченной RAM (5-6 ГБ)

Использование:
    uvicorn main:app --host 0.0.0.0 --port 8001
"""
import os
import time
from io import BytesIO
from pathlib import Path
from typing import Optional

import soundfile as sf
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from loguru import logger

# Инициализация FastAPI
app = FastAPI(
    title="RVC Voice Conversion API",
    version="1.0.0",
    description="API для конвертации голоса через RVC модель"
)

# Глобальные переменные (ленивая загрузка модели)
_rvc_model = None
_model_loaded = False
_model_error: Optional[str] = None

# Настройки из переменных окружения
# Пути относительно корня проекта (rvc_service находится в подпапке)
_base_path = Path(__file__).parent.parent
MODEL_PATH = Path(os.getenv("RVC_MODEL_PATH", str(_base_path / "Miaea" / "model.pth")))
INDEX_PATH = Path(os.getenv("RVC_INDEX_PATH", str(_base_path / "Miaea" / "model.index")))
DEVICE = os.getenv("RVC_DEVICE", "cpu")  # cpu или cuda
F0_UP_KEY = int(os.getenv("RVC_F0_UP_KEY", "0"))
INDEX_RATE = float(os.getenv("RVC_INDEX_RATE", "0.75"))
PROTECT = float(os.getenv("RVC_PROTECT", "0.33"))


def load_rvc_model():
    """
    Ленивая загрузка RVC модели (только при первом запросе).
    Модель загружается один раз и переиспользуется для всех запросов.
    """
    global _rvc_model, _model_loaded, _model_error
    
    if _model_loaded:
        return _rvc_model
    
    if _model_error:
        return None
    
    try:
        # Проверяем наличие файлов модели
        if not MODEL_PATH.exists():
            error_msg = f"Модель не найдена: {MODEL_PATH}"
            logger.error(error_msg)
            _model_error = error_msg
            return None
        
        # Импортируем RVC библиотеку
        try:
            from rvc_python import RVCInference
        except ImportError:
            error_msg = "rvc-python не установлен. Установите: pip install rvc-python"
            logger.error(error_msg)
            _model_error = error_msg
            return None
        
        # Загружаем модель
        logger.info(f"Загрузка RVC модели: {MODEL_PATH}")
        logger.info(f"Устройство: {DEVICE}, F0 up key: {F0_UP_KEY}")
        
        _rvc_model = RVCInference(device=DEVICE)
        _rvc_model.load_model(
            model_path=str(MODEL_PATH),
            index_path=str(INDEX_PATH) if INDEX_PATH.exists() else None
        )
        
        _model_loaded = True
        logger.success("✅ RVC модель загружена успешно")
        return _rvc_model
        
    except Exception as e:
        error_msg = f"Ошибка загрузки RVC модели: {e}"
        logger.error(error_msg)
        _model_error = error_msg
        return None


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "service": "RVC Voice Conversion API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    Проверка работоспособности сервиса
    
    Returns:
        - status: "ok" если сервис работает
        - model_loaded: True если модель загружена
        - model_error: Сообщение об ошибке (если есть)
        - device: Устройство обработки (cpu/cuda)
    """
    model = load_rvc_model()
    return {
        "status": "ok",
        "model_loaded": _model_loaded and model is not None,
        "model_error": _model_error,
        "device": DEVICE,
        "model_path": str(MODEL_PATH),
        "index_path": str(INDEX_PATH) if INDEX_PATH.exists() else None
    }


@app.post("/convert")
async def convert_voice(
    audio: UploadFile = File(..., description="OGG аудио файл")
):
    """
    Конвертирует голос через RVC модель
    
    Принимает: OGG аудио файл (multipart/form-data)
    Возвращает: OGG аудио файл (конвертированный)
    
    Время обработки: ~5-8 секунд (зависит от длины аудио)
    
    Пример использования:
        curl -X POST "http://localhost:8001/convert" \\
             -F "audio=@voice.ogg"
    """
    start_time = time.time()
    
    # 1. Загружаем модель (если еще не загружена)
    rvc = load_rvc_model()
    if not rvc:
        raise HTTPException(
            status_code=503,
            detail=_model_error or "RVC модель недоступна"
        )
    
    # 2. Читаем входящее аудио
    try:
        audio_bytes = await audio.read()
        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="Пустой аудио файл")
        
        logger.info(f"📥 Получено аудио: {len(audio_bytes)} байт")
        
        # 3. Конвертируем OGG -> WAV (для RVC)
        audio_buffer = BytesIO(audio_bytes)
        try:
            samples, samplerate = sf.read(audio_buffer, dtype='float32')
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Ошибка чтения аудио файла: {e}"
            )
        
        logger.info(f"Аудио: {len(samples)} сэмплов, {samplerate} Hz")
        
        # 4. RVC конвертация
        logger.info("🔄 Начало RVC конвертации...")
        try:
            converted_samples = rvc.infer(
                audio=samples,
                sample_rate=samplerate,
                f0_up_key=F0_UP_KEY,
                index_rate=INDEX_RATE,
                protect=PROTECT
            )
        except Exception as e:
            logger.error(f"Ошибка RVC конвертации: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка RVC конвертации: {str(e)}"
            )
        
        # 5. Конвертируем WAV -> OGG (для Telegram)
        out_buffer = BytesIO()
        try:
            sf.write(
                out_buffer,
                converted_samples,
                samplerate,
                format='OGG',
                subtype='VORBIS'
            )
            out_buffer.seek(0)
            result_bytes = out_buffer.read()
        except Exception as e:
            logger.error(f"Ошибка записи OGG: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка записи аудио: {str(e)}"
            )
        
        elapsed = time.time() - start_time
        logger.success(
            f"✅ RVC конвертация завершена за {elapsed:.2f}с, "
            f"результат: {len(result_bytes)} байт"
        )
        
        return Response(
            content=result_bytes,
            media_type="audio/ogg",
            headers={
                "X-Processing-Time": f"{elapsed:.2f}",
                "X-Original-Size": str(len(audio_bytes)),
                "X-Converted-Size": str(len(result_bytes))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка конвертации: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("RVC_PORT", "8001")),
        log_level="info"
    )


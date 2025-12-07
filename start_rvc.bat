@echo off
REM Быстрый запуск RVC сервиса для Windows
REM Запустите этот файл для старта RVC сервиса

echo ========================================
echo   Запуск RVC Voice Conversion Service
echo ========================================
echo.

cd /d "%~dp0\rvc_service"

REM Проверяем наличие модели
if not exist "..\Miaea\model.pth" (
    echo [ОШИБКА] Модель не найдена: ..\Miaea\model.pth
    echo Убедитесь, что файл модели существует!
    pause
    exit /b 1
)

if not exist "..\Miaea\model.index" (
    echo [ПРЕДУПРЕЖДЕНИЕ] Индексный файл не найден: ..\Miaea\model.index
    echo RVC будет работать без индекса (качество может быть ниже)
    echo.
)

REM Настройки (можно изменить)
set RVC_MODEL_PATH=..\Miaea\model.pth
set RVC_INDEX_PATH=..\Miaea\model.index
set RVC_DEVICE=cpu
set RVC_F0_UP_KEY=0
set RVC_INDEX_RATE=0.75
set RVC_PROTECT=0.33
set RVC_PORT=8001

echo Настройки:
echo   Модель: %RVC_MODEL_PATH%
echo   Индекс: %RVC_INDEX_PATH%
echo   Устройство: %RVC_DEVICE%
echo   Порт: %RVC_PORT%
echo.

REM Активируем виртуальное окружение (если есть)
if exist "venv\Scripts\activate.bat" (
    echo Активация виртуального окружения...
    call venv\Scripts\activate.bat
)

echo.
echo Запуск RVC сервиса на порту %RVC_PORT%...
echo Сервис будет доступен по адресу: http://localhost:%RVC_PORT%
echo.
echo Для остановки нажмите Ctrl+C
echo.

REM Используем uv run для правильного окружения
uv run uvicorn main:app --host 0.0.0.0 --port %RVC_PORT% --workers 1

pause


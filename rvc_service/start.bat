@echo off
REM Скрипт запуска RVC сервиса на Windows

REM Настройки (можно изменить)
set RVC_MODEL_PATH=Miaea/model.pth
set RVC_INDEX_PATH=Miaea/model.index
set RVC_DEVICE=cpu
set RVC_F0_UP_KEY=0
set RVC_INDEX_RATE=0.75
set RVC_PROTECT=0.33
set RVC_PORT=8001

REM Переходим в папку скрипта
cd /d "%~dp0"

REM Активируем виртуальное окружение (если есть)
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Запускаем сервис
echo Запуск RVC сервиса на порту %RVC_PORT%...
uvicorn main:app --host 0.0.0.0 --port %RVC_PORT% --workers 1

pause


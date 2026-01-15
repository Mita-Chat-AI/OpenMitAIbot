@echo off
REM Скрипт для запуска бота
cd /d "%~dp0"
echo Запуск бота...
uv run -m src.bot
pause

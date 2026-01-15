@echo off
REM Скрипт для запуска бота как фонового процесса (без окна)
cd /d "%~dp0"
start /B "" uv run -m src.bot
echo Бот запущен в фоновом режиме
echo Для остановки используйте: taskkill /F /IM python.exe

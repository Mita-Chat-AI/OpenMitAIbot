#!/bin/bash
# Скрипт запуска RVC сервиса на Linux/Mac
# Использование: ./start.sh

# Переходим в папку скрипта (rvc_service)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Определяем путь к корню проекта (на уровень выше rvc_service)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Проверяем наличие модели
MODEL_PATH="$PROJECT_ROOT/Miaea/model.pth"
INDEX_PATH="$PROJECT_ROOT/Miaea/model.index"

if [ ! -f "$MODEL_PATH" ]; then
    echo "❌ [ОШИБКА] Модель не найдена: $MODEL_PATH"
    echo "Убедитесь, что файл модели существует!"
    exit 1
fi

if [ ! -f "$INDEX_PATH" ]; then
    echo "⚠️  [ПРЕДУПРЕЖДЕНИЕ] Индексный файл не найден: $INDEX_PATH"
    echo "RVC будет работать без индекса (качество может быть ниже)"
    echo ""
fi

# Настройки (можно изменить через переменные окружения)
export RVC_MODEL_PATH="${RVC_MODEL_PATH:-$MODEL_PATH}"
export RVC_INDEX_PATH="${RVC_INDEX_PATH:-$INDEX_PATH}"
export RVC_DEVICE="${RVC_DEVICE:-cpu}"
export RVC_F0_UP_KEY="${RVC_F0_UP_KEY:-0}"
export RVC_INDEX_RATE="${RVC_INDEX_RATE:-0.75}"
export RVC_PROTECT="${RVC_PROTECT:-0.33}"
export RVC_PORT="${RVC_PORT:-8001}"

echo "========================================"
echo "  RVC Voice Conversion Service"
echo "========================================"
echo ""
echo "📁 Пути:"
echo "   Проект: $PROJECT_ROOT"
echo "   Модель: $RVC_MODEL_PATH"
echo "   Индекс: $RVC_INDEX_PATH"
echo ""
echo "⚙️  Настройки:"
echo "   Устройство: $RVC_DEVICE"
echo "   Порт: $RVC_PORT"
echo "   F0 up key: $RVC_F0_UP_KEY"
echo "   Index rate: $RVC_INDEX_RATE"
echo "   Protect: $RVC_PROTECT"
echo ""

# Активируем виртуальное окружение (обязательно!)
if [ -d "venv" ]; then
    echo "🔧 Активация виртуального окружения..."
    source venv/bin/activate
else
    echo "⚠️  Виртуальное окружение не найдено!"
    echo "Создайте его: python3 -m venv venv"
    echo "Затем установите зависимости:"
    echo "  pip install --upgrade pip setuptools wheel"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Проверяем наличие uvicorn
if ! command -v uvicorn &> /dev/null; then
    echo "❌ [ОШИБКА] uvicorn не найден!"
    echo "Установите:"
    echo "  pip install --upgrade pip setuptools wheel"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Запускаем сервис
echo "🚀 Запуск RVC сервиса на порту $RVC_PORT..."
echo "   Сервис будет доступен по адресу: http://localhost:$RVC_PORT"
echo "   Для остановки нажмите Ctrl+C"
echo ""
uvicorn main:app --host 0.0.0.0 --port $RVC_PORT --workers 1


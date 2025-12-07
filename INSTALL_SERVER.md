# 🚀 Установка на Linux сервер

## ⚠️ Важно: Python защищен системой

На новых Linux системах (Debian 12+, Ubuntu 22.04+) Python защищен от установки пакетов напрямую. Нужно использовать виртуальное окружение.

## 📋 Установка

### Шаг 1: Установить зависимости системы

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip python3-full build-essential
```

### Шаг 2: Создать виртуальное окружение для бота

```bash
cd /path/to/OpenMitAIbot

# Создать виртуальное окружение
python3 -m venv .venv

# Активировать
source .venv/bin/activate

# Установить зависимости
pip install -r pyproject.toml
# или если используете uv:
uv sync
```

### Шаг 3: Создать виртуальное окружение для RVC

```bash
cd /path/to/OpenMitAIbot/rvc_service

# Создать виртуальное окружение
python3 -m venv venv

# Активировать
source venv/bin/activate

# ⚠️ ВАЖНО: Установить build tools для Python 3.12
pip install --upgrade pip setuptools wheel

# Установить зависимости
pip install -r requirements.txt
```

**Примечание:** 
- Установка может занять 10-15 минут из-за больших зависимостей (torch, fairseq и т.д.)
- Для Python 3.12 требуется `setuptools` для компиляции старых версий numpy

### Шаг 4: Загрузить модели

```bash
# Создать папку
mkdir -p /path/to/OpenMitAIbot/Miaea

# Загрузить с вашего компьютера
scp Miaea/model.pth user@server:/path/to/OpenMitAIbot/Miaea/
scp Miaea/model.index user@server:/path/to/OpenMitAIbot/Miaea/
```

### Шаг 5: Настроить .env

```env
API_RVC=http://localhost:8001/convert
```

## 🚀 Запуск через systemd

### RVC сервис

Создайте `/etc/systemd/system/rvc-service.service`:

```ini
[Unit]
Description=RVC Voice Conversion Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/OpenMitAIbot/rvc_service
Environment="PATH=/path/to/OpenMitAIbot/rvc_service/venv/bin:/usr/bin"
Environment="RVC_MODEL_PATH=/path/to/OpenMitAIbot/Miaea/model.pth"
Environment="RVC_INDEX_PATH=/path/to/OpenMitAIbot/Miaea/model.index"
Environment="RVC_DEVICE=cpu"
Environment="RVC_PORT=8001"
ExecStart=/path/to/OpenMitAIbot/rvc_service/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001 --workers 1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Бот

Создайте `/etc/systemd/system/mitaibot.service`:

```ini
[Unit]
Description=Mita AI Bot
After=network.target mongodb.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/OpenMitAIbot
Environment="PATH=/path/to/OpenMitAIbot/.venv/bin:/usr/bin"
ExecStart=/path/to/OpenMitAIbot/.venv/bin/python -m src.bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Запуск

```bash
sudo systemctl enable rvc-service
sudo systemctl enable mitaibot
sudo systemctl start rvc-service
sudo systemctl start mitaibot
```

## 🔍 Проверка

```bash
# RVC сервис
curl http://localhost:8001/health

# Логи
sudo journalctl -u rvc-service -f
sudo journalctl -u mitaibot -f
```

## 🐛 Troubleshooting

### Ошибка: "externally managed"

**Решение:** Используйте виртуальное окружение (см. выше)

### Ошибка: "No module named 'distutils'"

**Решение:** Установите setuptools перед установкой зависимостей:

```bash
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Ошибка: "fairseq не компилируется"

```bash
sudo apt install build-essential
pip install fairseq --no-build-isolation
```

### Ошибка: "numpy не компилируется"

**Решение:** Убедитесь что установлены build tools:

```bash
sudo apt install build-essential python3-dev
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install numpy==1.23.5  # Установить отдельно
pip install -r requirements.txt
```

### Ошибка: "модель не найдена"

```bash
ls -la /path/to/OpenMitAIbot/Miaea/model.pth
# Убедитесь что файл существует
```

---

**Готово! 🎉**


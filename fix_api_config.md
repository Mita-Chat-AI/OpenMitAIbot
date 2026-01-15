# Исправление ошибки API ключа

## Проблема
Ошибка: `invalid api key (2049)`

## Причина
В `.env` файле все еще указан `AI_PROVIDER=minimax`, но поддержка Minimax удалена из кода.

## Решение

### Вариант 1: Использовать OpenAI

1. Откройте файл `.env` в корне проекта
2. Измените следующие строки:

```env
AI_PROVIDER=openai
AI_MODEL=gpt-3.5-turbo
AI_API_KEY=sk-ваш_ключ_openai
AI_BASE_URL=https://api.openai.com/v1
```

**Где получить ключ OpenAI:**
- Зарегистрируйтесь на https://platform.openai.com
- Перейдите в API Keys
- Создайте новый ключ

### Вариант 2: Использовать LMStudio (локально)

Если у вас запущен LMStudio локально:

```env
AI_PROVIDER=lmstudio
AI_MODEL=название_вашей_модели
AI_API_KEY=lm-studio  # или любой ключ, LMStudio не проверяет
AI_BASE_URL=http://localhost:1234/v1
```

**Как запустить LMStudio:**
1. Скачайте LMStudio: https://lmstudio.ai
2. Загрузите модель
3. Запустите локальный сервер (обычно на порту 1234)

### Вариант 3: Использовать другой OpenAI-совместимый API

Многие сервисы предоставляют OpenAI-совместимые API:
- **OpenRouter** - https://openrouter.ai
- **Together AI** - https://together.ai
- **Anthropic Claude** (через прокси)

Пример для OpenRouter:
```env
AI_PROVIDER=openai
AI_MODEL=openai/gpt-3.5-turbo
AI_API_KEY=ваш_ключ_openrouter
AI_BASE_URL=https://openrouter.ai/api/v1
```

## После изменения .env

1. Перезапустите бота:
   ```bash
   uv run -m src.bot
   ```

2. Проверьте, что ошибка исчезла

## Проверка текущих настроек

Запустите скрипт для проверки:
```bash
python check_bot.py
```

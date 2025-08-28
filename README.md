# OpenMitAIbot

**OpenMitAIbot** — это Telegram-бот с Искусственным Интеллектом (LLM) на базе **Aiogram**.
Бот использует OpenAI-like API, поэтому можно подключать любой совместимый ИИ.

---

## 🚀 Быстрая установка

1. Клонируйте проект:

   ```bash
   git clone https://github.com/Mita-Chat-AI/OpenMitAIbot.git
   ```
2. Перейдите в папку проекта:

   ```bash
   cd OpenMitAIbot
   ```
3. Создайте и заполните файл `.env` на основе `.env.example`.
4. Установите [uv](https://github.com/astral-sh/uv) (Python runner).
5. Запустите бота:

   ```bash
   uv run -m src.bot
   ```

---

## ✨ Возможности

* Генерация голосовых сообщений
* Общение с ИИ
* Добавление описания о себе (для улучшения диалога)
* Voice Mode — Мита отвечает голосом вместо текста

---

## 📜 Команды бота

| Команда           | Описание                       |
| ----------------- | ------------------------------ |
| `/setbio <текст>` | Добавить описание о себе       |
| `/voice <текст>`  | Генерация голосового сообщения |
| `/voice_mode`     | Включить/выключить Voice Mode  |
| `/reset`          | Очистить историю общения с ИИ  |

---

## 🧠 Логика ИИ

* Основной код ИИ находится в:
  `OpenMitAIbot/src/bot/services/model_services/ai_service.py`
* Промпт для ИИ можно изменить здесь:
  `OpenMitAIbot/src/prompt.py`

---

## ⚙ Настройка `.env.example`

* **API_EDGE_TTS** — адрес сервера, который генерирует голосовые сообщения.
  Сервер должен возвращать **байтовый поток (bytes)**.
  Если сервер возвращает другой формат, можно изменить логику генерации голосовых:
  `OpenMitAIbot/src/bot/services/model_services/user_service.py`, строка \~93 (`edge_voice_generate`).

---

## ❓ Поддержка

Если что-то непонятно, создайте **Issue** или напишите автору в [Telegram](https://t.me/PashaHatsune).
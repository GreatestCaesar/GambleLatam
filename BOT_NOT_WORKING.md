# Диагностика: Бот не работает

## Шаг 1: Проверьте webhook

Откройте в браузере:
```
https://api.telegram.org/bot8469451558:AAGaTleE2Q6rFfSw3HQgtjqlXupLPRS4ReA/getWebhookInfo
```

**Должно вернуться:**
```json
{
  "ok": true,
  "result": {
    "url": "https://gamblelatam.vercel.app/api",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

**Если `"url"` пустой или неправильный:**
- Webhook не установлен
- Установите заново (см. SET_WEBHOOK.md)

**Если `"pending_update_count"` больше 0:**
- Есть необработанные обновления
- Проверьте логи функции

## Шаг 2: Проверьте endpoint

Откройте в браузере:
```
https://gamblelatam.vercel.app/api
```

**Должно вернуться:**
```json
{
  "status": "ok",
  "service": "Telegram Bot Webhook",
  "message": "Bot is running",
  "application_initialized": true
}
```

**Если `"application_initialized": false`:**
- Проблема с инициализацией бота
- Проверьте переменные окружения

## Шаг 3: Проверьте переменные окружения

В Vercel Dashboard:
1. Settings → Environment Variables
2. Должны быть:
   - `TELEGRAM_BOT_TOKEN` = `8469451558:AAGaTleE2Q6rFfSw3HQgtjqlXupLPRS4ReA`
   - `ALLOWED_TELEGRAM_IDS` = ваш Telegram ID (например: `123456789`)

**Как узнать свой Telegram ID:**
- Напишите боту [@userinfobot](https://t.me/userinfobot)
- Он вернет ваш ID

## Шаг 4: Проверьте логи функции

1. Vercel Dashboard → ваш проект → Functions → `api/index.py`
2. Откройте вкладку **Logs**
3. Отправьте команду `/start` боту в Telegram
4. **Сразу вернитесь к логам** - должны появиться записи

**Что искать в логах:**
- `Handler called!` - функция вызывается
- `Access denied for user X` - ваш ID не в списке разрешенных
- `Application not initialized` - проблема с инициализацией
- `Import error` - проблема с импортом модулей
- Любые другие ошибки (Traceback)

## Шаг 5: Проверьте доступ

Если в логах видно `Access denied for user X`:
- Ваш Telegram ID не добавлен в `ALLOWED_TELEGRAM_IDS`
- Добавьте ваш ID в переменные окружения
- Перезапустите деплой

## Шаг 6: Тест доступа

Временно отключите проверку доступа для теста:

В `bot.py` функция `check_user_access`:
```python
def check_user_access(user_id: int) -> bool:
    # Временно разрешаем всем для теста
    return True  # Закомментируйте остальной код
```

**ВАЖНО:** После теста верните проверку обратно!

## Что проверить ПРЯМО СЕЙЧАС:

1. ✅ Что возвращает `getWebhookInfo`?
2. ✅ Что возвращает `/api` endpoint?
3. ✅ Что показывают логи при отправке `/start`?
4. ✅ Ваш Telegram ID добавлен в `ALLOWED_TELEGRAM_IDS`?

**Сообщите результаты этих проверок!**


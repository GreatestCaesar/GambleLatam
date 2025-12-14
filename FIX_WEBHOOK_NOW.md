# СРОЧНО: Исправление Webhook

## Проблема
Webhook установлен с неправильным URL: `gamblelatam.vercel.app` (без `https://` и без `/api`)

Из-за этого Telegram получает 404 ошибку при попытке отправить обновления.

## Решение

### Шаг 1: Удалите старый webhook

Откройте в браузере:
```
https://api.telegram.org/bot8469451558:AAGaTleE2Q6rFfSw3HQgtjqlXupLPRS4ReA/deleteWebhook
```

Должно вернуться: `{"ok":true,"result":true,"description":"Webhook was deleted"}`

### Шаг 2: Установите правильный webhook

**ПРАВИЛЬНЫЙ URL (с https:// и /api):**
```
https://api.telegram.org/bot8469451558:AAGaTleE2Q6rFfSw3HQgtjqlXupLPRS4ReA/setWebhook?url=https://gamblelatam.vercel.app/api
```

Откройте эту ссылку в браузере или используйте curl:
```bash
curl -X POST "https://api.telegram.org/bot8469451558:AAGaTleE2Q6rFfSw3HQgtjqlXupLPRS4ReA/setWebhook?url=https://gamblelatam.vercel.app/api"
```

Должно вернуться: `{"ok":true,"result":true,"description":"Webhook was set"}`

### Шаг 3: Проверьте статус

```
https://api.telegram.org/bot8469451558:AAGaTleE2Q6rFfSw3HQgtjqlXupLPRS4ReA/getWebhookInfo
```

Должно вернуться:
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

**Важно:** 
- `"url"` должен быть `"https://gamblelatam.vercel.app/api"` (с https:// и /api)
- `"pending_update_count"` должен быть 0 (или уменьшится после обработки)

### Шаг 4: Проверьте работу бота

1. Откройте бота в Telegram
2. Отправьте команду `/start`
3. Бот должен ответить

## Если все еще не работает:

1. Проверьте логи функции в Vercel Dashboard
2. Убедитесь, что ваш Telegram ID добавлен в `ALLOWED_TELEGRAM_IDS`
3. Проверьте, что endpoint `/api` возвращает правильный ответ


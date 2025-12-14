# Установка Webhook для Telegram бота

## Проблема
Webhook не устанавливается - ошибка 404.

## Решение

В URL для webhook должен быть **полный путь с `/api`** и протокол `https://`.

### Правильный формат:

```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://gamblelatam.vercel.app/api
```

### Важно:
- ✅ Используйте `https://` в начале URL
- ✅ Добавьте `/api` в конце URL домена
- ✅ Используйте правильный домен из Vercel Dashboard

### Шаг 1: Проверьте правильный домен

В Vercel Dashboard:
- Settings → Domains
- Или посмотрите домен в последнем деплое

Ваш домен: `gamblelatam.vercel.app`

### Шаг 2: Установите webhook

**Через браузер:**
```
https://api.telegram.org/bot8469451558:AAGaTleE2Q6rFfSw3HQgtjqlXupLPRS4ReA/setWebhook?url=https://gamblelatam.vercel.app/api
```

**Через curl:**
```bash
curl -X POST "https://api.telegram.org/bot8469451558:AAGaTleE2Q6rFfSw3HQgtjqlXupLPRS4ReA/setWebhook?url=https://gamblelatam.vercel.app/api"
```

### Шаг 3: Проверьте статус webhook

**Через браузер:**
```
https://api.telegram.org/bot8469451558:AAGaTleE2Q6rFfSw3HQgtjqlXupLPRS4ReA/getWebhookInfo
```

**Через curl:**
```bash
curl "https://api.telegram.org/bot8469451558:AAGaTleE2Q6rFfSw3HQgtjqlXupLPRS4ReA/getWebhookInfo"
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

### Шаг 4: Проверьте работу бота

1. Откройте бота в Telegram
2. Отправьте команду `/start`
3. Бот должен ответить

## Если все еще ошибка 404:

1. **Проверьте, что endpoint работает:**
   ```
   https://gamblelatam.vercel.app/api
   ```
   Должен вернуть: `{"status": "ok", ...}`

2. **Проверьте, что используете правильный токен:**
   - Токен должен быть из @BotFather
   - Формат: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

3. **Проверьте переменные окружения:**
   - В Vercel Dashboard → Settings → Environment Variables
   - Должна быть: `TELEGRAM_BOT_TOKEN`

## Удаление webhook (если нужно):

```
https://api.telegram.org/bot8469451558:AAGaTleE2Q6rFfSw3HQgtjqlXupLPRS4ReA/deleteWebhook
```


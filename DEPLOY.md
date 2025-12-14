# Инструкция по деплою бота на Vercel

## Подготовка

1. Убедитесь, что у вас установлен Vercel CLI:
```bash
npm i -g vercel
```

2. Войдите в Vercel:
```bash
vercel login
```

## Настройка переменных окружения

В панели Vercel или через CLI установите следующие переменные окружения:

### Обязательные переменные:

1. **TELEGRAM_BOT_TOKEN** - Токен вашего Telegram бота (получите у @BotFather)
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

2. **ALLOWED_TELEGRAM_IDS** - Список разрешенных Telegram ID пользователей (через запятую или пробел)
   ```
   ALLOWED_TELEGRAM_IDS=123456789 987654321 555555555
   ```
   или
   ```
   ALLOWED_TELEGRAM_IDS=123456789,987654321,555555555
   ```

### Как узнать свой Telegram ID:

1. Напишите боту [@userinfobot](https://t.me/userinfobot) в Telegram
2. Он вернет ваш ID (число, например: 123456789)

## Деплой на Vercel

### Через CLI:

```bash
# Перейдите в директорию проекта
cd "D:\Python Projects\latam"

# Запустите деплой
vercel

# Для продакшн деплоя
vercel --prod
```

### Через GitHub:

1. Создайте репозиторий на GitHub
2. Загрузите код в репозиторий
3. В Vercel Dashboard:
   - Нажмите "New Project"
   - Подключите ваш GitHub репозиторий
   - Настройте переменные окружения
   - Нажмите "Deploy"

## Настройка Webhook

После деплоя получите URL вашего API endpoint. 

**Важно:** URL должен быть в формате `https://your-project.vercel.app/api` (без `/index` в конце)

### Шаг 1: Проверьте, что endpoint работает

**Важно:** URL должен быть точно `https://your-project.vercel.app/api` (без слеша в конце)

Откройте в браузере:
```
https://your-project.vercel.app/api
```

Должен вернуться JSON: `{"status": "ok", "service": "Telegram Bot Webhook", "message": "Bot is running"}`

**Если получаете 404:**

1. Проверьте, что файл `api/index.py` существует
2. Проверьте логи деплоя в Vercel Dashboard
3. Попробуйте тестовый endpoint: `https://your-project.vercel.app/api/test`
4. Убедитесь, что в Vercel Dashboard проект правильно задеплоен

### Шаг 2: Установите webhook

Затем установите webhook для вашего бота:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-project.vercel.app/api"
```

Или через браузер:
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-project.vercel.app/api
```

**Замените:**
- `<YOUR_BOT_TOKEN>` на ваш токен бота
- `your-project.vercel.app` на ваш домен Vercel

### Шаг 3: Проверьте статус webhook

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

Должно вернуться:
```json
{
  "ok": true,
  "result": {
    "url": "https://your-project.vercel.app/api",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

## Проверка работы

1. Проверьте статус webhook:
```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

2. Отправьте команду `/start` боту в Telegram
3. Если вы в списке разрешенных ID, бот должен ответить

## Устранение проблем

### Ошибка 404 "Not Found" при установке webhook:

**Причины и решения:**

1. **Неправильный URL:**
   - ✅ Правильно: `https://your-project.vercel.app/api`
   - ❌ Неправильно: `https://your-project.vercel.app/api/index`
   - ❌ Неправильно: `https://your-project.vercel.app/api/`

2. **Функция не задеплоилась:**
   - Проверьте логи деплоя в Vercel Dashboard
   - Убедитесь, что файл `api/index.py` существует
   - Проверьте, что `vercel.json` настроен правильно

3. **Проверьте, что endpoint доступен:**
   ```bash
   curl https://your-project.vercel.app/api
   ```
   Должен вернуть JSON с `"status": "ok"`

4. **Проверьте структуру проекта:**
   ```
   .
   ├── api/
   │   └── index.py
   ├── bot.py
   ├── vercel.json
   └── requirements.txt
   ```

5. **Перезапустите деплой:**
   ```bash
   vercel --prod --force
   ```

### Бот не отвечает:

1. Проверьте, что webhook установлен правильно:
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
   ```

2. Проверьте логи в Vercel Dashboard:
   - Перейдите в проект → Functions → api/index.py → Logs

3. Убедитесь, что ваш Telegram ID в списке `ALLOWED_TELEGRAM_IDS`

4. Проверьте переменные окружения в Vercel Dashboard

### Ошибка доступа (403):

- Убедитесь, что ваш Telegram ID добавлен в переменную `ALLOWED_TELEGRAM_IDS`
- ID должен быть числом без пробелов (можно через запятую)
- Пример: `ALLOWED_TELEGRAM_IDS=123456789,987654321`

### Ошибки деплоя:

- Убедитесь, что все зависимости в `requirements.txt`
- Проверьте логи сборки в Vercel Dashboard
- Убедитесь, что `bot.py` находится в корне проекта (не в `api/`)

### Проверка работы endpoint:

1. **GET запрос (должен работать):**
   ```bash
   curl https://your-project.vercel.app/api
   ```

2. **Проверка webhook:**
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
   ```

3. **Проверка логов:**
   - Vercel Dashboard → Your Project → Functions → api/index.py → Logs

## Локальная разработка

Для локальной разработки используйте:

```bash
python bot.py
```

Бот будет работать в режиме polling (не требует webhook).

## Обновление переменных окружения

В Vercel Dashboard:
1. Перейдите в Settings → Environment Variables
2. Добавьте или измените переменные
3. Перезапустите деплой

Или через CLI:
```bash
vercel env add TELEGRAM_BOT_TOKEN
vercel env add ALLOWED_TELEGRAM_IDS
```

## Примечания

- Playwright может не работать на Vercel из-за ограничений serverless функций
- Для генерации скриншотов может потребоваться альтернативное решение (например, внешний сервис)
- Рекомендуется использовать более легковесную библиотеку для скриншотов или вынести генерацию скриншотов в отдельный сервис


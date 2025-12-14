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

После деплоя получите URL вашего API endpoint (например: `https://your-project.vercel.app/api`)

Затем установите webhook для вашего бота:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-project.vercel.app/api"
```

Или через браузер:
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-project.vercel.app/api
```

## Проверка работы

1. Проверьте статус webhook:
```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

2. Отправьте команду `/start` боту в Telegram
3. Если вы в списке разрешенных ID, бот должен ответить

## Устранение проблем

### Бот не отвечает:

1. Проверьте, что webhook установлен правильно
2. Проверьте логи в Vercel Dashboard
3. Убедитесь, что ваш Telegram ID в списке `ALLOWED_TELEGRAM_IDS`

### Ошибка доступа:

- Убедитесь, что ваш Telegram ID добавлен в переменную `ALLOWED_TELEGRAM_IDS`
- ID должен быть числом без пробелов (можно через запятую)

### Ошибки деплоя:

- Убедитесь, что все зависимости в `requirements.txt`
- Проверьте, что Python версия 3.11 поддерживается
- Проверьте логи сборки в Vercel Dashboard

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


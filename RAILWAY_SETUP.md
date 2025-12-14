# Настройка бота на Railway

## Шаг 1: Удалить webhook с Vercel

### Способ 1: Через скрипт
```bash
python delete_webhook.py YOUR_BOT_TOKEN
```

### Способ 2: Через curl
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook"
```

### Способ 3: Через браузер
Откройте в браузере:
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook
```

## Шаг 2: Создать проект на Railway

1. Зайдите на https://railway.app
2. Войдите через GitHub
3. Нажмите "New Project"
4. Выберите "Deploy from GitHub repo"
5. Выберите ваш репозиторий

## Шаг 3: Настроить переменные окружения

В Railway Dashboard:
1. Откройте ваш проект
2. Перейдите в "Variables"
3. Добавьте переменные:
   - `TELEGRAM_BOT_TOKEN` - токен вашего бота
   - `ALLOWED_TELEGRAM_IDS` - список разрешенных ID через запятую (например: `123456789,987654321`)

## Шаг 4: Настроить деплой

Railway автоматически определит Python проект. Убедитесь, что:
- `requirements.txt` присутствует
- `Procfile` присутствует (уже создан)
- `railway.json` присутствует (уже создан)

## Шаг 5: Установить Playwright браузеры

Railway автоматически установит зависимости из `requirements.txt`. 
Для установки браузеров Playwright добавьте в "Build Command" в настройках проекта:

```bash
pip install -r requirements.txt && python -m playwright install chromium
```

Или создайте файл `build.sh`:
```bash
#!/bin/bash
pip install -r requirements.txt
python -m playwright install chromium
```

## Шаг 6: Получить URL вашего приложения

1. В Railway Dashboard откройте ваш проект
2. Перейдите в "Settings"
3. Найдите "Public Domain" или создайте новый
4. Скопируйте URL (например: `https://your-app.railway.app`)

## Шаг 7: Установить webhook

### Способ 1: Через скрипт
Создайте файл `set_railway_webhook.py`:

```python
import requests
import os

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
RAILWAY_URL = os.getenv('RAILWAY_PUBLIC_DOMAIN', 'your-app.railway.app')

webhook_url = f"https://{RAILWAY_URL}/webhook"

response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
    json={"url": webhook_url}
)

print(response.json())
```

### Способ 2: Через curl
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-app.railway.app/webhook"}'
```

### Способ 3: Через браузер
Откройте в браузере:
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-app.railway.app/webhook
```

## Шаг 8: Проверить webhook

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

## Преимущества Railway

- ✅ Больше места в `/tmp` для установки браузеров Playwright
- ✅ Постоянное окружение (не serverless)
- ✅ Легче отлаживать
- ✅ Бесплатный тариф с ограничениями

## Структура файлов для Railway

```
.
├── bot.py                 # Основной файл бота
├── requirements.txt       # Зависимости
├── Procfile              # Команда запуска для Railway
├── railway.json          # Конфигурация Railway
├── build.sh              # Скрипт сборки (опционально)
└── webhook.py            # Webhook endpoint для Railway
```

## Примечания

- Railway использует обычное приложение, а не serverless функции
- Бот будет работать постоянно (не только при запросах)
- Webhook endpoint должен быть доступен по адресу `/webhook`


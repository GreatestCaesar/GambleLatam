# Как удалить webhook с Vercel

## Способ 1: Через Telegram Bot API

Выполните команду в терминале или через браузер:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook"
```

Или откройте в браузере:
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook
```

Замените `<YOUR_BOT_TOKEN>` на токен вашего бота.

## Способ 2: Через Python скрипт

Создайте файл `delete_webhook.py`:

```python
import requests
import os

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

response = requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook')
print(response.json())
```

Запустите:
```bash
python delete_webhook.py
```

## Способ 3: Проверить текущий webhook

Перед удалением можно проверить текущий webhook:

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

## После удаления

После удаления webhook бот перестанет получать обновления через webhook. Для работы на Railway нужно будет установить новый webhook.


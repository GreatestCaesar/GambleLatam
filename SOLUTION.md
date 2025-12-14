# Решение проблемы 404 - Финальный вариант

## Проблема
Vercel возвращает 404, хотя функции видны в Dashboard.

## Решение

Я убрал `builds` из `vercel.json` - Vercel теперь автоматически распознает Python функции в папке `api/`.

### Шаг 1: Задеплойте снова

```bash
vercel --prod --force
```

### Шаг 2: Проверьте endpoints

После деплоя попробуйте:

1. **Минимальный:**
   ```
   https://gamblelatam4-8kwka7lrp-nebulamood.vercel.app/api/minimal
   ```

2. **Webhook:**
   ```
   https://gamblelatam4-8kwka7lrp-nebulamood.vercel.app/api/webhook
   ```

3. **Основной:**
   ```
   https://gamblelatam4-8kwka7lrp-nebulamood.vercel.app/api
   ```

### Шаг 3: Если все еще 404

Проверьте в Vercel Dashboard:

1. **Settings → General → Build & Development Settings**
   - Убедитесь, что **Output Directory** пустой
   - **Install Command** должен быть пустым или `pip install -r requirements.txt`
   - **Build Command** должен быть пустым

2. **Проверьте переменные окружения:**
   - Settings → Environment Variables
   - Должны быть: `TELEGRAM_BOT_TOKEN` и `ALLOWED_TELEGRAM_IDS`

3. **Проверьте логи деплоя:**
   - Deployments → последний деплой → Build Logs
   - Должны быть строки про установку Python зависимостей

### Шаг 4: Альтернативный вариант

Если ничего не помогает, попробуйте создать файл `.vercelignore` и убедитесь, что он не блокирует `api/`:

```
# .vercelignore не должен блокировать api/
```

Или удалите `.vercelignore` полностью, если он есть.

## Важно

Vercel автоматически создает маршруты для всех `.py` файлов в папке `api/`:
- `api/minimal.py` → `/api/minimal`
- `api/index.py` → `/api`
- `api/webhook.py` → `/api/webhook`

Не нужно указывать маршруты вручную!


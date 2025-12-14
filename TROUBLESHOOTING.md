# Устранение ошибки 404 на Vercel

## Пошаговая диагностика

### 1. Проверьте структуру проекта

Убедитесь, что структура такая:
```
.
├── api/
│   ├── index.py
│   └── test.py (опционально, для теста)
├── bot.py
├── vercel.json
├── requirements.txt
└── runtime.txt
```

### 2. Проверьте vercel.json

Должен быть минимальный:
```json
{
  "functions": {
    "api/index.py": {
      "memory": 1024,
      "maxDuration": 30
    }
  }
}
```

### 3. Проверьте логи деплоя

1. Откройте Vercel Dashboard
2. Перейдите в ваш проект
3. Откройте вкладку "Deployments"
4. Выберите последний деплой
5. Проверьте логи сборки

**Что искать:**
- Ошибки импорта
- Ошибки установки зависимостей
- Предупреждения о структуре проекта

### 4. Проверьте, что функция задеплоилась

1. В Vercel Dashboard → ваш проект → "Functions"
2. Должна быть функция `api/index.py`
3. Если её нет - проблема в деплое

### 5. Проверьте endpoint

**Тестовый endpoint (должен работать):**
```bash
curl https://your-project.vercel.app/api/test
```

**Основной endpoint:**
```bash
curl https://your-project.vercel.app/api
```

**Если оба возвращают 404:**

1. **Проверьте домен:**
   - Убедитесь, что используете правильный домен из Vercel Dashboard
   - Проверьте, что проект задеплоен (статус "Ready")

2. **Проверьте маршрутизацию:**
   - В Vercel Dashboard → Settings → General
   - Проверьте "Framework Preset" - должно быть "Other" или пусто

3. **Перезапустите деплой:**
   ```bash
   vercel --prod --force
   ```

### 6. Альтернативный вариант vercel.json

Если текущий не работает, попробуйте:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/**/*.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/$1"
    }
  ]
}
```

### 7. Проверьте переменные окружения

1. Vercel Dashboard → Settings → Environment Variables
2. Убедитесь, что установлены:
   - `TELEGRAM_BOT_TOKEN`
   - `ALLOWED_TELEGRAM_IDS`

### 8. Проверьте логи функции

1. Vercel Dashboard → ваш проект → Functions → api/index.py
2. Откройте вкладку "Logs"
3. Отправьте GET запрос на `/api`
4. Проверьте логи - должны быть записи о запросе

### 9. Минимальный тест

Создайте файл `api/simple.py`:

```python
def handler(request):
    return {
        "statusCode": 200,
        "body": '{"test": "ok"}'
    }
```

Проверьте: `https://your-project.vercel.app/api/simple`

Если это работает, проблема в основном handler.

### 10. Контакты для помощи

Если ничего не помогает:
1. Проверьте [документацию Vercel Python](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
2. [Сообщество Vercel](https://community.vercel.com/)
3. Проверьте примеры в [GitHub Vercel Examples](https://github.com/vercel/examples)

## Частые ошибки

### Ошибка: "Function not found"
- Проверьте, что файл находится в `api/`
- Проверьте имя файла (должно быть `index.py` для `/api`)

### Ошибка: "Import error"
- Проверьте, что все зависимости в `requirements.txt`
- Проверьте логи деплоя на ошибки установки

### Ошибка: "Timeout"
- Увеличьте `maxDuration` в `vercel.json`
- Проверьте, что код не зависает


# Быстрое решение проблемы 404

## Проблема
Endpoint возвращает 404, хотя деплой прошел успешно.

## Решение 1: Проверьте структуру проекта

Убедитесь, что структура такая:
```
.
├── api/
│   ├── index.py  ← должен быть здесь
│   ├── test.py
│   └── hello.py
├── bot.py
├── vercel.json
└── requirements.txt
```

## Решение 2: Проверьте в Vercel Dashboard

1. Откройте ваш проект в Vercel Dashboard
2. Перейдите в **Functions** (вкладка слева)
3. Должны быть функции:
   - `api/index.py`
   - `api/test.py`
   - `api/hello.py`

**Если функций нет:**
- Проблема в деплое
- Проверьте логи деплоя на ошибки

## Решение 3: Проверьте endpoint

Попробуйте эти URL (замените `your-project` на ваш домен):

1. **Простой тест:**
   ```
   https://your-project.vercel.app/api/hello
   ```
   Должен вернуть: `{"status": "ok", "message": "Hello from Vercel Python!"}`

2. **Основной endpoint:**
   ```
   https://your-project.vercel.app/api
   ```

3. **Тестовый endpoint:**
   ```
   https://your-project.vercel.app/api/test
   ```

## Решение 4: Если все еще 404

### Вариант A: Пересоздайте проект

1. Удалите проект в Vercel Dashboard
2. Создайте новый проект
3. Задеплойте заново

### Вариант B: Используйте другой формат vercel.json

Попробуйте этот `vercel.json`:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api",
      "dest": "/api/index.py"
    }
  ]
}
```

### Вариант C: Проверьте домен

1. В Vercel Dashboard → Settings → Domains
2. Убедитесь, что используете правильный домен
3. Попробуйте использовать домен вида: `your-project-username.vercel.app`

## Решение 5: Проверьте логи

1. Vercel Dashboard → ваш проект → Functions → api/index.py
2. Откройте вкладку **Logs**
3. Отправьте GET запрос на `/api`
4. Проверьте, появляются ли логи

**Если логов нет:**
- Функция не вызывается
- Проблема в маршрутизации

**Если логи есть, но ошибка:**
- Проблема в коде функции
- Проверьте ошибки в логах

## Решение 6: Альтернативный подход

Если ничего не помогает, попробуйте использовать другой путь:

1. Переименуйте `api/index.py` в `api/bot.py`
2. Обновите `vercel.json`:
   ```json
   {
     "functions": {
       "api/bot.py": {
         "maxDuration": 30
       }
     }
   }
   ```
3. Используйте URL: `https://your-project.vercel.app/api/bot`

## Что проверить в первую очередь:

1. ✅ Деплой прошел успешно (видно из логов)
2. ❓ Функции видны в Vercel Dashboard → Functions?
3. ❓ Логи появляются при запросе?
4. ❓ Какой именно URL вы используете?

**Сообщите результаты этих проверок!**


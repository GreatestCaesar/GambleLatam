# Проверка логов для диагностики 404

## Критически важно проверить:

### 1. Логи функции в реальном времени

1. Откройте Vercel Dashboard
2. Проект → **Functions** → `api/minimal.py`
3. Откройте вкладку **Logs**
4. В другом окне откройте:
   ```
   https://gamblelatam4-8kwka7lrp-nebulamood.vercel.app/api/minimal
   ```
5. **Сразу вернитесь к логам** - должны появиться записи

**Что искать в логах:**
- Если логов НЕТ → функция не вызывается (проблема маршрутизации)
- Если логи ЕСТЬ, но ошибка → проблема в коде функции
- Если "Function not found" → проблема в деплое

### 2. Проверьте точный URL

Попробуйте эти варианты:

1. **С расширением .py:**
   ```
   https://gamblelatam4-8kwka7lrp-nebulamood.vercel.app/api/minimal.py
   ```

2. **Без расширения:**
   ```
   https://gamblelatam4-8kwka7lrp-nebulamood.vercel.app/api/minimal
   ```

3. **С trailing slash:**
   ```
   https://gamblelatam4-8kwka7lrp-nebulamood.vercel.app/api/minimal/
   ```

### 3. Проверьте в Functions

1. Vercel Dashboard → Functions → `api/minimal.py`
2. Нажмите на функцию
3. Проверьте:
   - **Runtime:** должно быть Python
   - **Handler:** должно быть `handler`
   - **Path:** должно быть `/api/minimal`

### 4. Проверьте через curl

```bash
curl -v https://gamblelatam4-8kwka7lrp-nebulamood.vercel.app/api/minimal
```

Посмотрите на заголовки ответа - там может быть информация о том, куда перенаправляется запрос.

### 5. Альтернативный тест

Попробуйте создать функцию в корне проекта (не в api/):

Создайте файл `test.py` в корне:
```python
def handler(request):
    return {"statusCode": 200, "body": '{"test": "ok"}'}
```

И проверьте: `https://your-project.vercel.app/test`

## Что сообщить:

1. ✅ Появляются ли логи при запросе `/api/minimal`?
2. ✅ Что показывают логи (если есть)?
3. ✅ Какой URL вы используете (с .py или без)?
4. ✅ Что показывает curl -v?


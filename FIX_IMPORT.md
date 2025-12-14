# Исправление проблемы с импортом bot.py

Если `/api/status` работает, но `/api` не работает, проблема в импорте `bot.py`.

## Решение: Переместить bot.py в api/

### Вариант 1: Скопировать bot.py в api/

1. Скопируйте `bot.py` → `api/bot.py`
2. В `api/index.py` измените импорт на:
   ```python
   from bot import init_application, check_user_access
   ```
   (без изменений, так как теперь bot.py в той же папке)

### Вариант 2: Использовать правильный путь

В `api/index.py` измените путь импорта:

```python
import os
import sys

# Правильный путь к корневой директории
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from bot import init_application, check_user_access
```

### Вариант 3: Создать симлинк (для локальной разработки)

На Windows:
```cmd
mklink api\bot.py ..\bot.py
```

На Linux/Mac:
```bash
ln -s ../bot.py api/bot.py
```

## После изменений:

1. Задеплойте снова: `vercel --prod --force`
2. Проверьте `/api` endpoint
3. Проверьте логи в Vercel Dashboard


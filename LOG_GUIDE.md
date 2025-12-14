# Где искать логи в Vercel

## 1. В панели Vercel

1. Откройте ваш проект в Vercel Dashboard
2. Перейдите в раздел **"Deployments"**
3. Выберите последний deployment
4. Нажмите на **"Functions"** или **"View Function Logs"**
5. Выберите функцию `api/index` (или другую, которая обрабатывает запросы)

## 2. В реальном времени

1. В Vercel Dashboard откройте **"Logs"** в боковом меню
2. Выберите ваш проект
3. Логи будут обновляться в реальном времени

## 3. Что искать в логах

### Успешный запуск браузера:
```
Browser launched successfully using build-time installed browsers
```
или
```
Browser launched successfully using system browser: /usr/bin/chromium
```
или
```
Browser launched successfully after installation in /tmp
```

### Ошибки, которые нужно искать:

#### Попытка 1 не сработала (это нормально):
```
Attempt 1 failed - default path: Executable doesn't exist at...
```

#### Попытка 2 - проверка системных браузеров:
```
Attempt 2: Checking for system browsers...
Found system browser at: /usr/bin/chromium
```
или
```
No system browsers found in standard locations
```

#### Попытка 3 - установка в /tmp:
```
Attempt 3: Checking available space in /tmp for browser installation...
Available space in /tmp: XXX.XX MB
```

**Если места достаточно:**
```
Sufficient space available. Installing browsers in /tmp...
Running: python3 -m playwright install chromium
Installation exit code: 0
Browsers installed successfully in /tmp
Browser launched successfully after installation in /tmp
```

**Если места недостаточно:**
```
Insufficient space in /tmp: XXX.XX MB (need at least 300 MB)
```

**Если установка не удалась:**
```
Failed to install browsers. Exit code: 1
Error details: [детали ошибки]
```

### Критическая ошибка:
```
All browser launch attempts failed. Cannot generate screenshot.
```

## 4. Как скопировать логи

1. В Vercel Dashboard откройте логи
2. Выделите нужные строки
3. Скопируйте (Ctrl+C / Cmd+C)
4. Вставьте сюда для анализа

## 5. Что делать дальше

После того как найдете логи, скопируйте:
- Все сообщения, которые начинаются с "Attempt"
- Сообщения об ошибках
- Сообщения о доступном месте в /tmp
- Сообщения об установке браузеров

Это поможет понять, на каком этапе происходит сбой.


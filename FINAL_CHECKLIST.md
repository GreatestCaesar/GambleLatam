# Финальный чеклист для решения 404

## Что проверить БЕЗ локальной установки:

### 1. Проверьте Source в Vercel Dashboard

1. Откройте ваш проект в Vercel Dashboard
2. Перейдите в **Source** (или **Files**)
3. Проверьте, видны ли файлы:
   - `api/minimal.py`
   - `api/index.py`
   - `test.py` (в корне)

**Если файлов нет:**
- Проблема в деплое
- Файлы не загружаются на Vercel

### 2. Проверьте точный домен

В Vercel Dashboard:
- **Settings → Domains**
- Или посмотрите домен в последнем деплое
- Используйте ТОЧНО тот домен, который там указан

Попробуйте эти варианты:
```
https://gamblelatam4-8kwka7lrp-nebulamood.vercel.app/test
https://gamblelatam4-8kwka7lrp-nebulamood.vercel.app/api/minimal
```

### 3. Проверьте логи функции

1. Vercel Dashboard → **Functions** → `api/minimal.py`
2. Откройте вкладку **Logs**
3. Откройте в браузере: `https://your-domain.vercel.app/api/minimal`
4. **Сразу вернитесь к логам** - должны появиться записи

**Если логов НЕТ:**
- Функция не вызывается
- Проблема в маршрутизации

**Если логи ЕСТЬ:**
- Функция вызывается
- Проблема в коде функции

### 4. Проверьте Build Logs

1. Vercel Dashboard → **Deployments**
2. Выберите последний деплой
3. Откройте **Build Logs**
4. Ищите строки:
   - `Installing required dependencies from requirements.txt`
   - `Build Completed`
   - Ошибки (если есть)

### 5. Проверьте настройки проекта

1. Vercel Dashboard → **Settings → General**
2. Проверьте:
   - **Framework Preset:** Other
   - **Root Directory:** `.` (пусто или точка)
   - **Build Command:** пусто
   - **Output Directory:** пусто
   - **Install Command:** пусто или `pip install -r requirements.txt`

### 6. Проверьте переменные окружения

1. Vercel Dashboard → **Settings → Environment Variables**
2. Должны быть:
   - `TELEGRAM_BOT_TOKEN`
   - `ALLOWED_TELEGRAM_IDS`

### 7. Попробуйте функцию в корне

Я создал `test.py` в корне проекта. После деплоя проверьте:
```
https://your-domain.vercel.app/test
```

Если это работает, значит Python функции работают, но проблема в папке `api/`.

## Что сделать СЕЙЧАС:

1. ✅ Задеплойте снова: `vercel --prod --force` (через GitHub или CLI)
2. ✅ Проверьте Source - видны ли файлы?
3. ✅ Проверьте `/test` endpoint (функция в корне)
4. ✅ Проверьте `/api/minimal` endpoint
5. ✅ Проверьте логи функции при запросе

## Сообщите результаты:

1. Видны ли файлы в Source?
2. Что возвращает `/test`?
3. Что возвращает `/api/minimal`?
4. Появляются ли логи при запросе?
5. Что показывают Build Logs?


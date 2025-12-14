FROM python:3.11-slim

# Устанавливаем системные зависимости для Playwright
RUN apt-get update -qq && \
    apt-get install -y -qq \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxcb1 \
    libcairo2 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем браузеры Playwright
RUN python -m playwright install chromium

# Копируем остальные файлы
COPY . .

# Открываем порт
EXPOSE 5000

# Запускаем приложение через gunicorn для production
# Используем 1 worker, так как asyncio event loop не работает хорошо с несколькими workers
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "webhook:app"]


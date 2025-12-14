#!/bin/bash
# Скрипт для установки зависимостей и браузеров Playwright
pip install -r requirements.txt
python -m playwright install chromium
python -m playwright install-deps chromium

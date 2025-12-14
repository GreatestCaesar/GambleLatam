"""
Диагностический endpoint для проверки состояния браузеров Playwright
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import subprocess
import shutil

# Добавляем родительскую директорию в путь для импорта
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

class handler(BaseHTTPRequestHandler):
    """Диагностический endpoint для проверки браузеров"""
    
    def do_GET(self):
        """Обработка GET запросов для диагностики"""
        try:
            info = {
                "status": "ok",
                "checks": {}
            }
            
            # Проверка 1: Доступное место в /tmp
            try:
                tmp_stat = shutil.disk_usage('/tmp')
                free_space_mb = tmp_stat.free / (1024 * 1024)
                total_space_mb = tmp_stat.total / (1024 * 1024)
                info["checks"]["tmp_space"] = {
                    "available_mb": round(free_space_mb, 2),
                    "total_mb": round(total_space_mb, 2),
                    "sufficient": free_space_mb > 300
                }
            except Exception as e:
                info["checks"]["tmp_space"] = {"error": str(e)}
            
            # Проверка 2: Системные браузеры
            system_browsers = [
                '/usr/bin/chromium',
                '/usr/bin/chromium-browser',
                '/usr/bin/google-chrome',
                '/usr/bin/google-chrome-stable'
            ]
            found_browsers = []
            for browser_path in system_browsers:
                if os.path.exists(browser_path):
                    found_browsers.append(browser_path)
            info["checks"]["system_browsers"] = {
                "found": found_browsers,
                "count": len(found_browsers)
            }
            
            # Проверка 3: Playwright браузеры (стандартный путь)
            default_playwright_path = os.path.expanduser("~/.cache/ms-playwright")
            playwright_browsers = []
            if os.path.exists(default_playwright_path):
                for root, dirs, files in os.walk(default_playwright_path):
                    if 'chrome' in root or 'chromium' in root:
                        playwright_browsers.append(root)
            info["checks"]["playwright_browsers"] = {
                "default_path": default_playwright_path,
                "exists": os.path.exists(default_playwright_path),
                "found_browsers": playwright_browsers
            }
            
            # Проверка 4: Playwright браузеры в /tmp
            tmp_playwright_path = '/tmp/.cache/ms-playwright'
            tmp_browsers = []
            if os.path.exists(tmp_playwright_path):
                for root, dirs, files in os.walk(tmp_playwright_path):
                    if 'chrome' in root or 'chromium' in root:
                        tmp_browsers.append(root)
            info["checks"]["tmp_playwright_browsers"] = {
                "path": tmp_playwright_path,
                "exists": os.path.exists(tmp_playwright_path),
                "found_browsers": tmp_browsers
            }
            
            # Проверка 5: Переменные окружения
            info["checks"]["environment"] = {
                "PLAYWRIGHT_BROWSERS_PATH": os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "not set"),
                "HOME": os.environ.get("HOME", "not set"),
                "USER": os.environ.get("USER", "not set")
            }
            
            # Проверка 6: Попытка импорта Playwright
            try:
                from playwright.async_api import async_playwright
                info["checks"]["playwright_import"] = {"status": "success"}
            except Exception as e:
                info["checks"]["playwright_import"] = {"status": "failed", "error": str(e)}
            
            # Проверка 7: Попытка установки (только проверка команды, не выполнение)
            try:
                result = subprocess.run(
                    ['python3', '-m', 'playwright', '--version'],
                    check=False,
                    timeout=10,
                    capture_output=True,
                    text=True
                )
                info["checks"]["playwright_version"] = {
                    "exit_code": result.returncode,
                    "stdout": result.stdout.strip() if result.stdout else None,
                    "stderr": result.stderr.strip() if result.stderr else None
                }
            except Exception as e:
                info["checks"]["playwright_version"] = {"error": str(e)}
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(info, indent=2).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())


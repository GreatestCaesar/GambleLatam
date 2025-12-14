"""
Диагностический endpoint для проверки работы бота
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import logging

# Добавляем родительскую директорию в путь
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Диагностика"""
        try:
            diagnostics = {
                "status": "ok",
                "checks": {}
            }
            
            # Проверка переменных окружения
            diagnostics["checks"]["TELEGRAM_BOT_TOKEN"] = "SET" if os.getenv('TELEGRAM_BOT_TOKEN') else "NOT SET"
            diagnostics["checks"]["ALLOWED_TELEGRAM_IDS"] = "SET" if os.getenv('ALLOWED_TELEGRAM_IDS') else "NOT SET"
            
            # Проверка импортов
            try:
                from bot import init_application, check_user_access
                diagnostics["checks"]["bot_import"] = "OK"
                
                # Проверка создания приложения
                try:
                    app = init_application()
                    diagnostics["checks"]["app_creation"] = "OK"
                    diagnostics["checks"]["app_type"] = str(type(app))
                except Exception as e:
                    diagnostics["checks"]["app_creation"] = f"ERROR: {str(e)}"
            except Exception as e:
                diagnostics["checks"]["bot_import"] = f"ERROR: {str(e)}"
            
            # Проверка telegram импорта
            try:
                from telegram import Update
                diagnostics["checks"]["telegram_import"] = "OK"
            except Exception as e:
                diagnostics["checks"]["telegram_import"] = f"ERROR: {str(e)}"
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(diagnostics, indent=2).encode())
        except Exception as e:
            logger.error(f"Error in debug: {e}", exc_info=True)
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())


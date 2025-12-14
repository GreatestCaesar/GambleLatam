"""
Тестовый endpoint для проверки переменных окружения
"""
from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Проверка переменных окружения"""
        try:
            # Получаем переменные окружения
            telegram_token = os.getenv('TELEGRAM_BOT_TOKEN', 'NOT SET')
            allowed_ids = os.getenv('ALLOWED_TELEGRAM_IDS', 'NOT SET')
            
            # Парсим allowed IDs
            allowed_ids_list = []
            if allowed_ids != 'NOT SET':
                for part in allowed_ids.replace(',', ' ').split():
                    try:
                        allowed_ids_list.append(int(part.strip()))
                    except ValueError:
                        continue
            
            response = {
                "status": "ok",
                "telegram_token_set": telegram_token != 'NOT SET',
                "telegram_token_preview": telegram_token[:10] + "..." if len(telegram_token) > 10 else telegram_token,
                "allowed_telegram_ids_set": allowed_ids != 'NOT SET',
                "allowed_telegram_ids_raw": allowed_ids[:100] if len(allowed_ids) > 100 else allowed_ids,
                "allowed_telegram_ids_parsed": allowed_ids_list,
                "allowed_telegram_ids_count": len(allowed_ids_list)
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())


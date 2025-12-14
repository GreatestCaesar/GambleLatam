"""
Endpoint для установки webhook через браузер
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.parse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Установка webhook через GET запрос"""
        try:
            # Получаем токен из переменной окружения
            token = os.getenv('TELEGRAM_BOT_TOKEN')
            if not token:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "ok": False,
                    "error": "TELEGRAM_BOT_TOKEN not set"
                }).encode())
                return
            
            # Получаем URL проекта из заголовков или переменной окружения
            # В Vercel можно использовать VERCEL_URL или VERCEL_BRANCH_URL
            vercel_url = os.getenv('VERCEL_URL', '') or os.getenv('VERCEL_BRANCH_URL', '')
            
            # Пытаемся получить из заголовка Host
            host = self.headers.get('Host', '')
            if host and not host.startswith('http'):
                vercel_url = f"https://{host}"
            
            # Если все еще нет URL, используем известный домен
            if not vercel_url:
                # Пытаемся получить из Referer или других заголовков
                referer = self.headers.get('Referer', '')
                if referer:
                    from urllib.parse import urlparse
                    parsed = urlparse(referer)
                    vercel_url = f"{parsed.scheme}://{parsed.netloc}"
            
            # Если все еще нет, используем известный домен из ошибки
            if not vercel_url:
                vercel_url = "https://gamblelatam.vercel.app"
            
            # URL для webhook
            webhook_url = f"{vercel_url}/api/index"
            
            logger.info(f"Setting webhook to: {webhook_url}")
            
            # Устанавливаем webhook через Telegram API
            set_webhook_url = f"https://api.telegram.org/bot{token}/setWebhook"
            data = urllib.parse.urlencode({
                'url': webhook_url
            }).encode()
            
            try:
                req = urllib.request.Request(set_webhook_url, data=data)
                with urllib.request.urlopen(req, timeout=10) as response:
                    result = json.loads(response.read().decode())
                    
                    response_data = {
                        "ok": result.get("ok", False),
                        "result": result.get("result", False),
                        "description": result.get("description", ""),
                        "webhook_url": webhook_url,
                        "message": "Webhook установлен успешно!" if result.get("ok") else f"Ошибка: {result.get('description', 'Unknown error')}"
                    }
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data, indent=2, ensure_ascii=False).encode())
            except Exception as e:
                logger.error(f"Failed to set webhook: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "ok": False,
                    "error": f"Failed to set webhook: {str(e)}"
                }).encode())
                
        except Exception as e:
            logger.error(f"Error in set-webhook: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

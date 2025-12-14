"""
Webhook handler для Telegram бота
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import sys

# Добавляем родительскую директорию в путь
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from bot import init_application, check_user_access
    from telegram import Update
    import asyncio
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Инициализируем приложение
    application = None
    try:
        application = init_application()
        logger.info("Application initialized")
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        application = None
        
except ImportError as e:
    logger = None
    application = None
    init_application = None
    check_user_access = None
    Update = None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Обработка GET запросов"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "ok",
            "service": "Telegram Bot Webhook"
        }).encode())
    
    def do_POST(self):
        """Обработка POST запросов от Telegram"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            if application is None:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": "Application not initialized"}).encode())
                return
            
            # Создаем Update объект
            update = Update.de_json(data, application.bot)
            
            if update and update.effective_user:
                user_id = update.effective_user.id
                
                # Проверяем доступ
                if check_user_access and not check_user_access(user_id):
                    if logger:
                        logger.warning(f"Access denied for user {user_id}")
                    self.send_response(403)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"ok": False, "error": "Access denied"}).encode())
                    return
                
                # Обрабатываем обновление
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    loop.run_until_complete(application.process_update(update))
                    if logger:
                        logger.info(f"Processed update for user {user_id}")
                except Exception as e:
                    if logger:
                        logger.error(f"Error processing: {e}")
            
            # Успешный ответ
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
            
        except Exception as e:
            if logger:
                logger.error(f"Error: {e}", exc_info=True)
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

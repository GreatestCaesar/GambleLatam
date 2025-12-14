"""
Основной handler для Telegram бота
Использует формат BaseHTTPRequestHandler для Vercel Python
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import asyncio
import logging

# Добавляем родительскую директорию в путь для импорта bot
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from bot import init_application, check_user_access
    from telegram import Update
except ImportError as e:
    logging.error(f"Import error: {e}")
    init_application = None
    check_user_access = None
    Update = None

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализируем приложение при загрузке модуля
application = None
try:
    if init_application:
        application = init_application()
        logger.info("Application initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize application: {e}", exc_info=True)
    application = None


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler"""
    
    def do_GET(self):
        """Обработка GET запросов (для проверки работоспособности)"""
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "service": "Telegram Bot Webhook",
                "message": "Bot is running",
                "application_initialized": application is not None
            }).encode())
        except Exception as e:
            logger.error(f"Error in GET: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def do_POST(self):
        """Обработка POST запросов от Telegram"""
        try:
            if application is None:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "ok": False,
                    "error": "Application not initialized"
                }).encode())
                return
            
            # Получаем данные запроса
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.error(f"Failed to parse body: {e}")
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": "Invalid JSON"}).encode())
                return
            
            # Создаем Update объект
            if not Update:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": "Update class not imported"}).encode())
                return
            
            update = Update.de_json(data, application.bot)
            
            if update and update.effective_user:
                user_id = update.effective_user.id
                
                # Проверяем доступ пользователя
                if check_user_access and not check_user_access(user_id):
                    logger.warning(f"Access denied for user {user_id}")
                    self.send_response(403)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"ok": False, "error": "Access denied"}).encode())
                    return
                
                # Обрабатываем обновление асинхронно
                try:
                    # Получаем или создаем event loop
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_closed():
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    # Запускаем обработку обновления
                    loop.run_until_complete(application.process_update(update))
                    logger.info(f"Processed update for user {user_id}")
                    
                except Exception as e:
                    logger.error(f"Error in async processing: {e}", exc_info=True)
                    # Все равно возвращаем успешный ответ
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"ok": True, "note": "Update processed with errors"}).encode())
                    return
            else:
                logger.warning("Update without effective_user")
            
            # Отправляем успешный ответ
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
            
        except Exception as e:
            logger.error(f"Error processing update: {e}", exc_info=True)
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

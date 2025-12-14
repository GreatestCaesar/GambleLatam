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

# НЕ инициализируем приложение при загрузке модуля
# В serverless окружении нужно создавать новое приложение для каждого запроса
# или правильно управлять event loop
application_factory = init_application if init_application else None


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
                "application_factory_available": application_factory is not None
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
            if application_factory is None:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "ok": False,
                    "error": "Application factory not available"
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
            
            # Создаем новое приложение для каждого запроса
            # Это решает проблему с event loop в serverless окружении
            try:
                application = application_factory()
                logger.info("Application created successfully")
            except Exception as e:
                logger.error(f"Failed to create application: {e}", exc_info=True)
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": f"Failed to create application: {str(e)}"}).encode())
                return
            
            # Создаем Update объект
            try:
                update = Update.de_json(data, application.bot)
                logger.info(f"Update created: {update.update_id if update else 'None'}")
            except Exception as e:
                logger.error(f"Failed to create Update: {e}", exc_info=True)
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": f"Failed to create Update: {str(e)}"}).encode())
                return
            
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
                    # Создаем новый event loop для этого запроса
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    async def process_update_async():
                        # Инициализируем приложение в этом event loop
                        await application.initialize()
                        # Обрабатываем обновление
                        await application.process_update(update)
                        # Закрываем приложение
                        await application.shutdown()
                    
                    # Запускаем обработку обновления
                    loop.run_until_complete(process_update_async())
                    loop.close()
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

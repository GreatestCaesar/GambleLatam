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
            # Логируем наличие переменных окружения для диагностики
            env_vars = [k for k in os.environ.keys() if 'TELEGRAM' in k or 'ALLOWED' in k]
            logger.info(f"Relevant env vars found: {env_vars}")
            if 'ALLOWED_TELEGRAM_IDS' in os.environ:
                allowed_ids_preview = os.environ['ALLOWED_TELEGRAM_IDS'][:50]
                logger.info(f"ALLOWED_TELEGRAM_IDS preview: {allowed_ids_preview}...")
            
            if application_factory is None:
                logger.error("Application factory not available")
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
            
            # Создаем Update объект (bot может быть None до инициализации, это нормально)
            try:
                # Для создания Update не нужен инициализированный bot
                update = Update.de_json(data, None)
                logger.info(f"Update created: {update.update_id if update else 'None'}")
            except Exception as e:
                logger.error(f"Failed to create Update: {e}", exc_info=True)
                logger.error(f"Data received: {str(data)[:500]}")
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": f"Failed to create Update: {str(e)}"}).encode())
                return
            
            # Проверяем тип обновления
            update_type = None
            user_id = None
            
            if update:
                if update.message:
                    update_type = "message"
                    user_id = update.message.from_user.id if update.message.from_user else None
                elif update.callback_query:
                    update_type = "callback_query"
                    user_id = update.callback_query.from_user.id if update.callback_query.from_user else None
                elif update.effective_user:
                    update_type = "other"
                    user_id = update.effective_user.id
            
            logger.info(f"Processing update {update.update_id if update else 'None'}, type: {update_type}, user_id: {user_id}")
            
            if user_id:
                # Проверяем доступ пользователя
                if not check_user_access:
                    logger.error("check_user_access function is not available!")
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"ok": False, "error": "Access check function not available"}).encode())
                    return
                
                if not check_user_access(user_id):
                    logger.warning(f"Access denied for user {user_id}")
                    self.send_response(403)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"ok": False, "error": "Access denied", "user_id": user_id}).encode())
                    return
                
                logger.info(f"Access granted for user {user_id}")
            else:
                logger.warning(f"Update without user_id: {update_type}")
            
            # Обрабатываем обновление асинхронно (для всех обновлений)
            try:
                # Создаем новый event loop для этого запроса
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def process_update_async():
                    try:
                        # Инициализируем приложение в этом event loop
                        logger.info(f"Initializing application for update {update.update_id if update else 'None'}")
                        try:
                            await application.initialize()
                            logger.info(f"Application initialized successfully")
                        except Exception as init_error:
                            logger.error(f"Failed to initialize application: {init_error}", exc_info=True)
                            raise
                        
                        logger.info(f"Processing update {update.update_id if update else 'None'}")
                        # Обрабатываем обновление
                        try:
                            await application.process_update(update)
                            logger.info(f"Update {update.update_id if update else 'None'} processed successfully")
                        except Exception as process_error:
                            logger.error(f"Error processing update: {process_error}", exc_info=True)
                            raise
                    except Exception as e:
                        logger.error(f"Error in process_update_async: {e}", exc_info=True)
                        raise
                    finally:
                        # Закрываем приложение
                        try:
                            await application.shutdown()
                            logger.info("Application shut down successfully")
                        except Exception as e:
                            logger.error(f"Error shutting down application: {e}", exc_info=True)
                
                # Запускаем обработку обновления
                loop.run_until_complete(process_update_async())
                loop.close()
                logger.info(f"Processed update {update.update_id if update else 'None'}")
                
            except Exception as e:
                logger.error(f"Error in async processing: {e}", exc_info=True)
                # Возвращаем ошибку, чтобы Telegram знал, что нужно повторить
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_msg = str(e)[:200]  # Ограничиваем длину сообщения
                self.wfile.write(json.dumps({
                    "ok": False, 
                    "error": error_msg,
                    "update_id": update.update_id if update else None
                }).encode())
                return
            
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

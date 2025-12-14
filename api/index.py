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
            logger.info("=" * 50)
            logger.info("New POST request received")
            
            # Логируем наличие переменных окружения для диагностики
            env_vars = [k for k in os.environ.keys() if 'TELEGRAM' in k or 'ALLOWED' in k]
            logger.info(f"Relevant env vars found: {env_vars}")
            
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
            
            if not Update:
                logger.error("Update class not imported")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": "Update class not imported"}).encode())
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
            
            # Создаем новое приложение для каждого запроса
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
            
            # Обрабатываем обновление асинхронно
            # Update будет создан после инициализации приложения, чтобы иметь правильный bot объект
            try:
                # Создаем новый event loop для этого запроса
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def process_update_async():
                    try:
                        # Инициализируем приложение в этом event loop
                        logger.info("Initializing application")
                        try:
                            await application.initialize()
                            logger.info("Application initialized successfully")
                        except Exception as init_error:
                            logger.error(f"Failed to initialize application: {init_error}", exc_info=True)
                            raise
                        
                        # Теперь создаем Update с правильным bot объектом
                        try:
                            # Логируем сырые данные для диагностики
                            logger.info(f"Raw update data keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                            if isinstance(data, dict) and 'callback_query' in data:
                                logger.info(f"Callback query data: {data['callback_query']}")
                            
                            update = Update.de_json(data, application.bot)
                            logger.info(f"Update created: {update.update_id if update else 'None'}")
                        except Exception as update_error:
                            logger.error(f"Failed to create Update: {update_error}", exc_info=True)
                            logger.error(f"Data that failed: {str(data)[:500]}")
                            raise
                        
                        if not update:
                            raise ValueError("Update is None after de_json")
                        
                        # Проверяем тип обновления и получаем user_id
                        update_type = None
                        user_id = None
                        
                        if update.message:
                            update_type = "message"
                            user_id = update.message.from_user.id if update.message.from_user else None
                            logger.info(f"Update is a message: {update.message.text if update.message.text else 'no text'}")
                        elif update.callback_query:
                            update_type = "callback_query"
                            user_id = update.callback_query.from_user.id if update.callback_query.from_user else None
                            logger.info(f"Update is a callback_query: data={update.callback_query.data}, message_id={update.callback_query.message.message_id if update.callback_query.message else 'no message'}")
                        elif update.effective_user:
                            update_type = "other"
                            user_id = update.effective_user.id
                        
                        logger.info(f"Processing update {update.update_id}, type: {update_type}, user_id: {user_id}")
                        
                        # Проверяем доступ пользователя
                        if user_id:
                            if not check_user_access:
                                logger.error("check_user_access function is not available!")
                                raise RuntimeError("Access check function not available")
                            
                            if not check_user_access(user_id):
                                logger.warning(f"Access denied for user {user_id}")
                                raise PermissionError(f"Access denied for user {user_id}")
                            
                            logger.info(f"Access granted for user {user_id}")
                        else:
                            logger.warning(f"Update without user_id: {update_type}")
                        
                        # Обрабатываем обновление
                        logger.info(f"Processing update {update.update_id}, type: {update_type}")
                        try:
                            # Логируем детали перед обработкой
                            if update_type == "callback_query":
                                logger.info(f"Callback query details: data={update.callback_query.data}, from_user={update.callback_query.from_user.id if update.callback_query.from_user else None}")
                            
                            await application.process_update(update)
                            logger.info(f"Update {update.update_id} processed successfully")
                        except Exception as process_error:
                            logger.error(f"Error processing update: {process_error}", exc_info=True)
                            logger.error(f"Update type was: {update_type}, Update ID: {update.update_id}")
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
                logger.info("Processed update successfully")
                
            except PermissionError as e:
                logger.warning(f"Permission denied: {e}")
                self.send_response(403)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())
                return
            except Exception as e:
                logger.error(f"Error in async processing: {e}", exc_info=True)
                # Возвращаем ошибку, чтобы Telegram знал, что нужно повторить
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_msg = str(e)[:200]  # Ограничиваем длину сообщения
                self.wfile.write(json.dumps({
                    "ok": False, 
                    "error": error_msg
                }).encode())
                return
            
            # Отправляем успешный ответ
            logger.info("Sending success response")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error("=" * 50)
            logger.error(f"CRITICAL ERROR in do_POST: {e}", exc_info=True)
            logger.error("=" * 50)
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_msg = str(e)[:500]  # Ограничиваем длину
            self.wfile.write(json.dumps({
                "ok": False, 
                "error": error_msg,
                "error_type": type(e).__name__
            }).encode())

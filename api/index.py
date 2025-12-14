"""
Vercel Serverless Function for Telegram Bot
"""
import os
import sys
import json
import logging
import asyncio

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


def handler(request):
    """
    Vercel serverless function handler
    
    Args:
        request: Request dict from Vercel
        
    Returns:
        dict: Response with statusCode, headers, and body
    """
    # Сначала логируем, что функция вызвана
    try:
        logger.info("=" * 50)
        logger.info("Handler called!")
        logger.info(f"Request type: {type(request)}")
        if isinstance(request, dict):
            logger.info(f"Request method: {request.get('method', 'unknown')}")
        logger.info("=" * 50)
    except:
        pass  # Если логирование не работает, продолжаем
    
    try:
        # Логируем запрос для отладки
        logger.info(f"Received request: {type(request)}, method: {request.get('method') if isinstance(request, dict) else 'unknown'}")
        
        if application is None:
            logger.error("Application is None")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "ok": False, 
                    "error": "Application not initialized",
                    "debug": "Check logs for initialization errors"
                })
            }
        
        # Получаем метод запроса
        if isinstance(request, dict):
            method = request.get('method', 'GET')
            body_str = request.get('body', '{}')
        else:
            method = getattr(request, 'method', 'GET')
            body_str = getattr(request, 'body', '{}') or '{}'
        
        # Обработка GET запросов (для проверки работоспособности)
        if method == 'GET':
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "status": "ok",
                    "service": "Telegram Bot Webhook",
                    "message": "Bot is running",
                    "application_initialized": application is not None
                })
            }
        
        # Обработка POST запросов от Telegram
        if method == 'POST':
            try:
                # Парсим body
                try:
                    body = json.loads(body_str) if isinstance(body_str, str) else body_str
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"Failed to parse body: {body_str[:200]}, error: {e}")
                    body = {}
                
                if not body:
                    logger.warning("Empty request body")
                    return {
                        "statusCode": 400,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"ok": False, "error": "Empty body"})
                    }
                
                # Создаем Update объект
                if not Update:
                    return {
                        "statusCode": 500,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"ok": False, "error": "Update class not imported"})
                    }
                
                update = Update.de_json(body, application.bot)
                
                if update and update.effective_user:
                    user_id = update.effective_user.id
                    
                    # Проверяем доступ пользователя
                    if check_user_access and not check_user_access(user_id):
                        logger.warning(f"Access denied for user {user_id}")
                        return {
                            "statusCode": 403,
                            "headers": {"Content-Type": "application/json"},
                            "body": json.dumps({"ok": False, "error": "Access denied"})
                        }
                    
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
                        return {
                            "statusCode": 200,
                            "headers": {"Content-Type": "application/json"},
                            "body": json.dumps({"ok": True, "note": "Update processed with errors"})
                        }
                else:
                    logger.warning("Update without effective_user")
                
                # Отправляем успешный ответ
                return {
                    "statusCode": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"ok": True})
                }
                
            except Exception as e:
                logger.error(f"Error processing update: {e}", exc_info=True)
                return {
                    "statusCode": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"ok": False, "error": str(e)})
                }
        
        # Неподдерживаемый метод
        return {
            "statusCode": 405,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"ok": False, "error": "Method not allowed"})
        }
        
    except Exception as e:
        logger.error(f"Handler error: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"ok": False, "error": f"Handler error: {str(e)}"})
        }

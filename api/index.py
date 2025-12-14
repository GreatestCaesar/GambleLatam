"""
Vercel Serverless Function for Telegram Bot
"""
import os
import sys
import json
import logging
import asyncio

# Добавляем родительскую директорию в путь для импорта bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import init_application, check_user_access
from telegram import Update

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализируем приложение при загрузке модуля
try:
    application = init_application()
    logger.info("Application initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize application: {e}", exc_info=True)
    application = None


def handler(request):
    """
    Vercel serverless function handler
    
    Args:
        request: Request object from Vercel
        
    Returns:
        dict: Response with statusCode, headers, and body
    """
    
    if application is None:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"ok": False, "error": "Application not initialized"})
        }
    
    # Обработка GET запросов (для проверки работоспособности)
    if request.method == 'GET':
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "status": "ok",
                "service": "Telegram Bot Webhook",
                "message": "Bot is running"
            })
        }
    
    # Обработка POST запросов от Telegram
    if request.method == 'POST':
        try:
            # Получаем данные запроса
            body = request.get_json()
            
            if not body:
                logger.warning("Empty request body")
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"ok": False, "error": "Empty body"})
                }
            
            # Создаем Update объект
            update = Update.de_json(body, application.bot)
            
            if update and update.effective_user:
                user_id = update.effective_user.id
                
                # Проверяем доступ пользователя
                if not check_user_access(user_id):
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
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    # Запускаем обработку обновления
                    loop.run_until_complete(application.process_update(update))
                    logger.info(f"Processed update for user {user_id}")
                    
                except Exception as e:
                    logger.error(f"Error in async processing: {e}", exc_info=True)
                    # Все равно возвращаем успешный ответ, чтобы Telegram не повторял запрос
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

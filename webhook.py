"""
Webhook endpoint для Railway
Использует Flask для обработки запросов от Telegram
"""
from flask import Flask, request, jsonify
import os
import sys
import asyncio
import logging

# Добавляем текущую директорию в путь для импорта bot
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from bot import init_application, check_user_access
from telegram import Update

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Инициализируем приложение один раз при старте
application = None

def get_application():
    """Получает или создает Application"""
    global application
    if application is None:
        application = init_application()
        # Инициализируем приложение в новом event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.initialize())
    return application

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработка webhook запросов от Telegram"""
    try:
        # Получаем данные запроса
        data = request.get_json()
        
        if not data:
            logger.warning("Empty request received")
            return jsonify({"ok": False, "error": "Empty request"}), 400
        
        logger.info(f"Update received: {data.get('update_id', 'unknown')}")
        
        # Получаем приложение
        app_instance = get_application()
        
        # Создаем Update объект
        update = Update.de_json(data, app_instance.bot)
        
        if not update:
            logger.error("Failed to create Update object")
            return jsonify({"ok": False, "error": "Invalid update"}), 400
        
        # Проверяем доступ пользователя
        user_id = None
        if update.message:
            user_id = update.message.from_user.id if update.message.from_user else None
        elif update.callback_query:
            user_id = update.callback_query.from_user.id if update.callback_query.from_user else None
        elif update.effective_user:
            user_id = update.effective_user.id
        
        if user_id:
            if not check_user_access(user_id):
                logger.warning(f"Access denied for user {user_id}")
                return jsonify({"ok": False, "error": "Access denied"}), 403
        
        # Обрабатываем обновление асинхронно
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(app_instance.process_update(update))
            logger.info(f"Update {update.update_id} processed successfully")
        finally:
            loop.close()
        
        return jsonify({"ok": True})
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "service": "Telegram Bot Webhook",
        "application_initialized": application is not None
    })

@app.route('/', methods=['GET'])
def index():
    """Главная страница"""
    return jsonify({
        "status": "ok",
        "service": "Telegram Bot Webhook",
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health"
        }
    })

if __name__ == '__main__':
    # Получаем порт из переменной окружения (Railway устанавливает PORT)
    port = int(os.getenv('PORT', 5000))
    
    # Инициализируем приложение при старте
    get_application()
    
    logger.info(f"Starting webhook server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)


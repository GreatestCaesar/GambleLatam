"""
Скрипт для удаления webhook с Telegram
"""
import requests
import os
import sys

def delete_webhook():
    """Удаляет webhook из Telegram"""
    # Получаем токен из переменной окружения или аргумента командной строки
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        if len(sys.argv) > 1:
            token = sys.argv[1]
        else:
            print("❌ Ошибка: TELEGRAM_BOT_TOKEN не установлен")
            print("Использование:")
            print("  python delete_webhook.py <BOT_TOKEN>")
            print("  или установите переменную окружения TELEGRAM_BOT_TOKEN")
            return False
    
    # Удаляем webhook
    url = f"https://api.telegram.org/bot{token}/deleteWebhook"
    
    try:
        response = requests.post(url, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            print("✅ Webhook успешно удален!")
            print(f"Результат: {result.get('result', True)}")
            print(f"Описание: {result.get('description', 'Webhook удален')}")
            return True
        else:
            print(f"❌ Ошибка при удалении webhook: {result.get('description', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при запросе: {e}")
        return False

if __name__ == '__main__':
    delete_webhook()


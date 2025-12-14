"""
Скрипт для установки webhook на Railway
"""
import requests
import os
import sys

def set_webhook():
    """Устанавливает webhook для Telegram бота"""
    # Получаем токен из переменной окружения или аргумента
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        if len(sys.argv) > 1:
            token = sys.argv[1]
        else:
            print("❌ Ошибка: TELEGRAM_BOT_TOKEN не установлен")
            print("Использование:")
            print("  python set_railway_webhook.py <BOT_TOKEN> <RAILWAY_URL>")
            print("  или установите переменную окружения TELEGRAM_BOT_TOKEN")
            return False
    
    # Получаем Railway URL из переменной окружения или аргумента
    railway_url = os.getenv('RAILWAY_PUBLIC_DOMAIN')
    
    if not railway_url:
        if len(sys.argv) > 2:
            railway_url = sys.argv[2]
        else:
            print("❌ Ошибка: Railway URL не указан")
            print("Использование:")
            print("  python set_railway_webhook.py <BOT_TOKEN> <RAILWAY_URL>")
            print("  или установите переменную окружения RAILWAY_PUBLIC_DOMAIN")
            print("\nПример Railway URL: your-app.railway.app")
            return False
    
    # Убираем протокол, если он есть
    railway_url = railway_url.replace('https://', '').replace('http://', '')
    
    # Формируем webhook URL
    webhook_url = f"https://{railway_url}/webhook"
    
    print(f"🔗 Устанавливаю webhook: {webhook_url}")
    
    # Проверяем текущий webhook
    check_url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
    try:
        response = requests.get(check_url, timeout=10)
        result = response.json()
        if result.get('ok'):
            current_webhook = result.get('result', {}).get('url', '')
            pending = result.get('result', {}).get('pending_update_count', 0)
            print(f"📋 Текущий webhook: {current_webhook}")
            print(f"📋 Ожидающих обновлений: {pending}")
    except Exception as e:
        print(f"⚠️  Не удалось проверить текущий webhook: {e}")
    
    # Устанавливаем новый webhook
    set_url = f"https://api.telegram.org/bot{token}/setWebhook"
    
    try:
        response = requests.post(
            set_url,
            json={"url": webhook_url},
            timeout=10
        )
        result = response.json()
        
        if result.get('ok'):
            print("✅ Webhook успешно установлен!")
            print(f"✅ URL: {webhook_url}")
            print(f"✅ Описание: {result.get('description', 'OK')}")
            
            # Проверяем еще раз
            response = requests.get(check_url, timeout=10)
            check_result = response.json()
            if check_result.get('ok'):
                verified_url = check_result.get('result', {}).get('url', '')
                if verified_url == webhook_url:
                    print("✅ Webhook подтвержден!")
                else:
                    print(f"⚠️  Webhook установлен, но URL отличается: {verified_url}")
            
            return True
        else:
            print(f"❌ Ошибка при установке webhook: {result.get('description', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при запросе: {e}")
        return False

if __name__ == '__main__':
    set_webhook()


"""
Упрощенная версия index.py без сложных импортов
"""
import json

def handler(request):
    """Простой handler для теста"""
    try:
        method = request.get('method', 'GET') if isinstance(request, dict) else 'GET'
        
        if method == 'GET':
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "status": "ok",
                    "service": "Telegram Bot Webhook",
                    "message": "Simple version works"
                })
            }
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"ok": True})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }


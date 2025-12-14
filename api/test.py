"""
Простой тестовый endpoint для проверки работы Vercel Python
"""
import json

def handler(request):
    """Простой тестовый handler"""
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "status": "ok",
            "message": "Test endpoint works!",
            "method": request.get('method', 'GET') if isinstance(request, dict) else 'GET'
        })
    }


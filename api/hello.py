"""
Простой тест для проверки работы Vercel Python
"""
import json

def handler(request):
    """Простой handler для теста"""
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "status": "ok",
            "message": "Hello from Vercel Python!",
            "method": request.get('method', 'GET') if isinstance(request, dict) else 'GET'
        })
    }


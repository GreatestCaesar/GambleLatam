"""
Простой endpoint для проверки работы Vercel Python
Без импортов из родительской директории
"""
import json

def handler(request):
    """Простой handler для проверки"""
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "status": "ok",
            "message": "Vercel Python is working!",
            "endpoint": "/api/status",
            "method": request.get('method', 'GET') if isinstance(request, dict) else 'GET'
        })
    }


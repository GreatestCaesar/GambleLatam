"""
Простой endpoint для проверки работы Vercel Python
Без импортов из родительской директории
"""

def handler(request):
    """Простой handler для проверки"""
    try:
        # Получаем метод
        method = 'GET'
        if isinstance(request, dict):
            method = request.get('method', 'GET')
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": '{"status": "ok", "message": "Vercel Python is working!", "endpoint": "/api/status", "method": "' + method + '"}'
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": '{"error": "' + str(e) + '"}'
        }

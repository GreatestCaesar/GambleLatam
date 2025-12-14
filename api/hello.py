"""
Простой тест для проверки работы Vercel Python
"""

def handler(request):
    """Простой handler для теста"""
    try:
        method = 'GET'
        if isinstance(request, dict):
            method = request.get('method', 'GET')
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": '{"status": "ok", "message": "Hello from Vercel Python!", "method": "' + method + '"}'
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": '{"error": "' + str(e) + '"}'
        }

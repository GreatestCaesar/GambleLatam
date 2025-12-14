"""
Альтернативный endpoint для webhook
"""
def handler(request):
    """Обработчик для webhook"""
    method = request.get('method', 'GET') if isinstance(request, dict) else 'GET'
    
    if method == 'GET':
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": '{"status": "ok", "message": "Webhook endpoint works", "method": "GET"}'
        }
    
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": '{"status": "ok", "message": "Webhook endpoint works", "method": "' + method + '"}'
    }


"""
Минимальный handler для теста
"""
def handler(request):
    """Обработчик запросов"""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": '{"test": "ok", "message": "Minimal handler works!"}'
    }

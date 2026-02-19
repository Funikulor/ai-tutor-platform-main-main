"""
Простая тестовая функция для проверки работы Netlify Functions
"""
import json

def handler(event, context):
    """Простой тестовый handler"""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "message": "Netlify Function работает!",
            "event": {
                "path": event.get("path"),
                "httpMethod": event.get("httpMethod"),
                "queryStringParameters": event.get("queryStringParameters")
            }
        })
    }



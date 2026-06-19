from api.main import app


def handler(event, context):
    return {"statusCode": 200, "body": "Use the FastAPI container deployment for full API support."}

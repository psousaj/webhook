import json
from django.http.request import HttpRequest
from rest_framework.response import Response
from rest_framework.decorators import api_view

from webhook.logger import Logger

logger = Logger(__name__)


@api_view(['POST'])
def webhook_receiver(request: HttpRequest):
    data = json.loads(request.body) if request.body else {}
    logger.info(f"Received webhook request")
    logger.info(data)
    # verify_messager.verify(data)
    return Response(
        {
            "code": "201",
            "message": "Webhook received a request",
            "data": [data]
        }, status=201)

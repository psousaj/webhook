import inspect
import json
import os
import random
import sys
import traceback
from django.http.request import HttpRequest
from rest_framework.response import Response
from django.http.response import JsonResponse
from rest_framework.decorators import api_view

from webhook.utils.logger import Logger
from messages_api import event

logger = Logger(__name__)


@api_view(['POST'])
def webhook_receiver(request: HttpRequest):
    data = json.loads(request.body) if request.body else {}
    try:
        event.manage(data)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        filename = inspect.getframeinfo(exc_tb.tb_frame).filename
        line_number = exc_tb.tb_lineno
        function_name = exc_tb.tb_frame.f_code.co_name
        logger.debug(
            f"Exceção ocorreu na função {function_name}, linha {line_number}: {e}")

        # Obter o rastreamento da pilha
        traceback_list = traceback.extract_tb(exc_tb)

        # Iterar pelos itens de rastreamento e imprimir a linha do código
        for traceback_item in traceback_list:
            line_number = traceback_item.lineno
            line_text = traceback_item.line
            print(
                f"Linha: {line_number}, Código: {line_text}")

        logger.info(f"Exception occurred. {e}")
    return Response(
        {
            "code": "201",
            "message": "Webhook received a request",
            "data": [data]
        }, status=201)

@api_view(['POST'])
def webhook_avaliation(request:HttpRequest):
    data = json.loads(request.body) if request.body else {}

    base_path = f'json/{data.get("event")}'

    if not os.path.exists(base_path):
        os.makedirs(base_path)

    with open(f'{base_path}/json_file{random.randint(0, 100)}.json', 'w') as f:
        json.dump(data, f)

    return JsonResponse(data)
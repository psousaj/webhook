import os
import sys
import time
import inspect
import heroku3
import traceback
from httpx import Client
from dotenv import load_dotenv
from celery import shared_task
from webhook.utils.logger import Logger
import os
import requests
from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from webhook.utils.logger import Logger
from messages_api.event import get_chat_protocol, get_current_period, get_contact_number

load_dotenv()
logger = Logger(__name__)
os.environ.get('', )
HEROKU_API_KEY = os.environ.get('HEROKU_API_KEY', os.getenv('HEROKU_API_KEY'))
HEROKU_APP_NAME = 'woz'
HEROKU_API = os.environ.get('HEROKU_API', os.getenv('HEROKU_API'))
CHECK_INTERVAL_SECONDS = 30
DYNO_NAME = 'web.1'  # or whatever your web dyno is called
DYNO_URL = os.environ.get('WEB_URL', os.getenv('WEB_URL'))


@shared_task(name='check_dyno_state')
def check_dyno_state():
    heroku_conn = heroku3.from_key(HEROKU_API_KEY)
    app = heroku_conn.apps()[HEROKU_APP_NAME]
    header = {
        "Accept": "application/vnd.heroku+json; version=3",
        "Authorization": f"Bearer {HEROKU_API_KEY}",
        "Content-Type": "application/json"
    }

    while True:

        with Client(base_url=f'{HEROKU_API}', headers=header) as client:
            try:
                response = client.get(DYNO_URL)

                if response.status_code == 404:
                    url = f"/apps/{HEROKU_APP_NAME}/dynos/{DYNO_NAME}"

                    response_state = client.get(url)
                    response_json = response_state.json()

                    try:
                        if response_json['state'] != 'starting' and response_json['state'] != 'up':
                            logger.info(f'Restarting Dyno: {DYNO_NAME}')
                            response_restart = client.delete(
                                url, headers=header)
                        else:
                            logger.info(
                                f'Dyno: {DYNO_NAME} state = {response_json["state"]}')
                    except Exception as e:
                        logger.info(f'Restarting Dyno: {DYNO_NAME}')
                        response_restart = client.delete(url)
                else:
                    logger.info(f'Web dyno is working correctly.')
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                filename = inspect.getframeinfo(exc_tb.tb_frame).filename
                line_number = exc_tb.tb_lineno
                function_name = exc_tb.tb_frame.f_code.co_name
                # Obter o rastreamento da pilha
                traceback_list = traceback.extract_tb(exc_tb)

                # Iterar pelos itens de rastreamento e imprimir a linha do código
                for traceback_item in traceback_list:
                    filename = traceback_item.filename
                    line_number = traceback_item.lineno
                    line_text = traceback_item.line
                    logger.debug(
                        f"Function: {function_name} Linha: {line_number}, Código: {line_text}")

                logger.info(f"Exception occurred. {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)

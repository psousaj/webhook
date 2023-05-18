import os
import time
import requests
import heroku3
from dotenv import load_dotenv
from webhook.logger import Logger
from celery import shared_task

load_dotenv()
logger = Logger(__name__)

HEROKU_API_KEY = os.getenv('HEROKU_API_KEY')
HEROKU_APP_NAME = 'woz'
HEROKU_API = os.getenv('HEROKU_API')
DYNO_NAME = 'web'  # or whatever your web dyno is called
CHECK_INTERVAL_SECONDS = 180
DYNO_URL = os.getenv('WEB_URL')
DYNO_ID = os.getenv('HEROKU_DYNO_ID')


@shared_task(name='check_state')
def init_check_state():
    heroku_conn = heroku3.from_key(HEROKU_API_KEY)
    app = heroku_conn.apps()[HEROKU_APP_NAME]

    while True:
        try:
            response = requests.get(DYNO_URL)

            if response.status_code == 404:
                url = f"{HEROKU_API}/apps/{HEROKU_APP_NAME}/dynos/{DYNO_ID}"
                header = {
                    "Accept": "application/vnd.heroku+json; version=3",
                    "Authorization": f"Bearer {HEROKU_API_KEY}",
                    "Content-Type": "application/json"
                }
                response_state = requests.get(url, headers=header)
                response_json = response_state.json()

                if response_json['state'] != 'starting' and response_json['state'] != 'up':
                    logger.info(f'Restarting Dyno: {DYNO_NAME}')
                    response_restart = requests.delete(url, headers=header)
                    logger.info(f'{response_restart.json()}')
                else:
                    logger.info(
                        f'Dyno: {DYNO_NAME} state = {response_json["state"]}')
            else:
                logger.info('Web dyno is working correctly.')
        except Exception as e:
            logger.debug(f'erro: {e}')

        time.sleep(CHECK_INTERVAL_SECONDS)


init_check_state.delay()

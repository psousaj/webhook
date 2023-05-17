import os
import time
import requests
import heroku3
from dotenv import load_dotenv
from webhook.logger import Logger

load_dotenv()
logger = Logger(__name__)

HEROKU_API_KEY = os.getenv('HEROKU_API_KEY')
HEROKU_APP_NAME = 'webhook'
WEB_DYNO_NAME = 'web'  # or whatever your web dyno is called
CHECK_INTERVAL_SECONDS = 180
WEB_DYNO_URL = os.getenv('WEB_URL')

heroku_conn = heroku3.from_key(HEROKU_API_KEY)
app = heroku_conn.apps()[HEROKU_APP_NAME]

while True:
    try:
        response = requests.get(WEB_DYNO_URL)
        response.raise_for_status()  # raises an exception if the HTTP status is 4xx or 5xx
    except Exception as e:
        print("Error when accessing web dyno, restarting it...")
        logger.debug(f'erro: {e}')
        web_dyno = app.dynos()[WEB_DYNO_NAME]
        web_dyno.restart()
    else:
        print("Web dyno is working correctly.")
        logger.info('Web dyno is working correctly.')

    time.sleep(CHECK_INTERVAL_SECONDS)

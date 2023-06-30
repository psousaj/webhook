import datetime
import os
import time
from httpx import Client
from rocketry import Rocketry
from rocketry.conds import every, time_of_day
from dotenv import load_dotenv

from webhook.utils.tools import Logger 

load_dotenv()
app = Rocketry()
logger = Logger(__name__)

def load_env(var):
    return os.environ.get(var, os.getenv(var))

def currently_datetime():
    return datetime.datetime.now().strftime("%d/%m/%Y - %H:%M:%S")

def send_report(client:Client, text:str, **kwargs):
    request = client.request(
                'POST', 
                WEBHOOK_SEND_REPORT_URL, 
                params={"group": "REPORT"}, 
                json={"text": text},
                headers = {"Accept": "application/json"}
)
    return request.text

APP='WEBHOOK'
HEROKU_API_KEY = load_env('HEROKU_API_KEY')
HEROKU_API = load_env('HEROKU_API')
HEROKU_APP_NAME = 'woz'
DYNO_NAME = ['worker.1', 'web.1']
ALLOWED_DYNO_STATES = ['starting', 'up']
NOT_ALLOWED_DYNO_STATES = ['crashed', 'down', 'idle']
CHECK_STATE_INTERVAL = every("5 minutes") & time_of_day.between("08:00", "21:00")
WEBHOOK_SEND_REPORT_URL = f'{load_env("WEBHOOK_API")}/control/report/send-message'

client_request_header = {
    "Accept": "application/vnd.heroku+json; version=3",
    "Authorization": f"Bearer {HEROKU_API_KEY}",
    "Content-Type": "application/json"
}

@app.task(CHECK_STATE_INTERVAL)
def check_state():
    with Client(base_url=f'{HEROKU_API}', headers=client_request_header) as client:
        dyno_is_currently_up = {}
        for dyno in DYNO_NAME:
            base_url = f'/apps/{HEROKU_APP_NAME}/dynos'
            max_retries = 5
            retries = 0
            while True:
                dyno_state_request = client.get(f'{base_url}/{dyno}')
                if dyno_state_request.status_code == 200:
                    dyno_state_request = dyno_state_request.json()
                    state = dyno_state_request.get('state')
                    logger.info(f'Checking {dyno} state = \'{state}\'')

                    if state in ALLOWED_DYNO_STATES:
                        dyno_is_currently_up[dyno] = True
                        break
                    if state in NOT_ALLOWED_DYNO_STATES:
                        dyno_is_currently_up[dyno] = False
                        break
                    else:
                        logger.info(f'{dyno} Dyno. There\'s something wrong here, state:{state}')

                    break  # Sai do loop while se a resposta for bem-sucedida (status 200)

                if retries >= max_retries:
                    text = f'{APP}: Maximum retries reached for {dyno}. Unable to retrieve state - Checked-In: {currently_datetime()}'
                    logger.info(text)
                    report = send_report(client=client, text=text)
                    print(report)

                elif dyno_state_request.status_code == 404:
                    # Refaz a verificação se a resposta for 404
                    retries += 1
                    logger.info(f'Retrying {dyno} state check ({retries}/{max_retries})')
                    continue  # Volta ao início do loop while para refazer a verificação
                

        if not all(dyno_is_currently_up.values()):
            logger.info('Restarting all dynos for troubleshoting any RAM issue')
            client.delete(f'{base_url}')
            time.sleep(2)

            report = send_report(
                client = client,
                text = f"{APP}: Todos os dynos foram reiniciado para resolver problemas com memória! Cheked-In: {currently_datetime()}"
            )
            print(report)
            return

        logger.info(f"{APP}: Todos os dynos estão rodando bem! Checked-In: {currently_datetime()}")
        return

if __name__ == "__main__":
    app.run()
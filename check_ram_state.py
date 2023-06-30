import os
import requests
import datetime
import time
from rocketry import Rocketry
from rocketry.conds import every, time_of_day
from httpx import Client
from dotenv import load_dotenv
from webhook.utils.tools import Logger

load_dotenv()
logger = Logger(__name__)
def load_env(var):
    return os.environ.get(var, os.getenv(var))

APP='WEBHOOK'
TIMEOUT=120
HEROKU_API_KEY = load_env('HEROKU_API_KEY')
HEROKU_API = load_env('HEROKU_API')
HEROKU_APP_NAME = 'woz'
DYNO_NAME = ['worker.1', 'web.1']
ALLOWED_DYNO_STATES = ['starting', 'up']
NOT_ALLOWED_DYNO_STATES = ['crashed', 'down', 'idle']
CHECK_STATE_INTERVAL = every("2 minutes") & time_of_day.between("08:00", "21:00")
WEBHOOK_SEND_REPORT_URL = f'{load_env("WEBHOOK_API")}/control/report/send-message'
LOG_STREAM_URL_RETRIEVE = f'/apps/{HEROKU_APP_NAME}/log-sessions'

client_request_header = {
    "Accept": "application/vnd.heroku+json; version=3",
    "Authorization": f"Bearer {HEROKU_API_KEY}",
    "Content-Type": "application/json"
}

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

def restart_dynos(client: Client, text = None):
    client.delete(f'/apps/{HEROKU_APP_NAME}/dynos', headers=client_request_header)
    time.sleep(2)
    report = send_report(client, f"{APP}: Todos os dynos foram reiniciado para resolver problemas Checked-In: {currently_datetime()}" if not text else text)
    print(report)
    return

def refresh_log_stream(client: Client):
    response = client.post(LOG_STREAM_URL_RETRIEVE)
    return response.json()['logplex_url'].replace('tail=false', 'tail=true')

def check_state(client:Client):
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

app = Rocketry()

# @app.task(CHECK_STATE_INTERVAL)
def check_memory():
    client = Client(base_url=HEROKU_API, headers=client_request_header, timeout=TIMEOUT)
    log_stream_url = load_env('LOG_STREAM_URL')

    while True:
        response = requests.get(log_stream_url, stream=True)
    
        if response.status_code not in range(200, 202):
            print('Esse link de stream expirou, buscando um novo')
            log_stream_url = refresh_log_stream(client)
            continue
        else:
            # check_state(client)

            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    # print(decoded_line)
                    if 'heroku[web.1]: Error R14 (Memory quota exceeded)' in decoded_line or 'heroku[worker.1]: Error R14 (Memory quota exceeded)' in decoded_line:
                        print("Memory quota exceeded error found. Restarting dynos...")
                        restart_dynos(client, text=f"Todos os dynos foram reiniciado para resolver problemas com memória RAM Checked-In: {currently_datetime()}")
                        time.sleep(5)
                        continue


if __name__ == "__main__":
    # app.run()
    check_memory()

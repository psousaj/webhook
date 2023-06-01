import os
from httpx import Client, get
from dotenv import load_dotenv

from webhook.logger import Logger

load_dotenv()
logger = Logger(__name__)


def any_request(url, body=None, method=get, json=True) -> get:
    header = {
        "Authorization": f"Bearer {os.environ.get('TOKEN_API', os.getenv('TOKEN_API'))}",
        "Content-Type": "application/json",
    }

    with Client(base_url=os.environ.get('API_URL', os.getenv('API_URL')), headers=header) as client:
        if method == 'get':
            get_response: get = client.get(url)
            return get_response.json() if json else get_response
        if method == 'post':
            response = client.post(url, json=body)
            if response.status_code == 200:
                return response.json() if json else response
            else:
                raise ValueError(
                    f'Something wrong - {response} - {response.json()}')


def get_chat_protocol(ticketId):
    try:
        header = {
            "Authorization": f"Bearer {os.environ.get('TOKEN_API', os.getenv('TOKEN_API'))}",
            "Content-Type": "application/json",
        }

        with Client(base_url=os.environ.get('API_URL', os.getenv('API_URL'))) as client:
            response = client.get(
                f"/tickets/{ticketId}",
                headers=header
            )

            if response.status_code == 200:
                data = response.json()
                return data['protocol']
    except Exception as e:
        logger.error(f"Exception occurred: \n{e}")

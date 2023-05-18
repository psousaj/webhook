import os
from httpx import Client
from dotenv import load_dotenv

from webhook.logger import Logger

load_dotenv()
logger = Logger(__name__)


def any_request(url):
    header = {
        "Authorization": f"Bearer {os.environ.get('TOKEN_API', os.getenv('TOKEN_API'))}",
        "Content-Type": "application/json",
    }

    with Client(base_url=os.environ.get('API_URL', os.getenv('API_URL')), headers=header) as client:
        return client.get(url).json()


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

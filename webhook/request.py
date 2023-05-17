import os
from httpx import Client
from dotenv import load_dotenv

from webhook.logger import Logger

load_dotenv()
logger = Logger(__name__)


def get_digisac_api(url: str, body=None):
    try:
        header = {
            "Authorization": f"Bearer {os.getenv('TOKEN_API')}",
            "Content-Type": "application/json",
        }

        with Client(base_url=os.getenv('API_URL')) as client:
            response = client.get(
                f"/{url}",
                json=body,
                headers=header
            )

            if response.status_code == 200:
                data = response.json()
                return data['protocol']
    except Exception as e:
        logger.error(f"Exception occurred: \n{e}")

import os
import logging
from httpx import get, Client
from datetime import datetime as dt
from dotenv import load_dotenv

from webhook.utils.get_objects import get_ticket, get_message

load_dotenv()

class Logger:

    def __init__(self, name) -> None:
        # Configuração do logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Criando um handler para o log no terminal
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(logging.DEBUG)

        # Criando um handler para o log em arquivo de texto
        # self.file_handler = logging.FileHandler('webhook_log.txt')
        # self.file_handler.setLevel(logging.DEBUG)

        # Definindo o formato das mensagens de log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s -%(levelname)s- %(message)s', datefmt='%d/%m/%Y|%H:%M:%S')
        self.console_handler.setFormatter(formatter)
        # self.file_handler.setFormatter(formatter)

        # Adicionando os handlers ao logger
        self.logger.addHandler(self.console_handler)
        # self.logger.addHandler(self.file_handler)

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)


##-- Logger instances to use
logger = Logger(__name__)


##-- Digisac requests
def any_digisac_request(url, body=None, method=get, json=True):
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



##--Contact utils
def get_contact_number(contact_id: str, only_number=False):
    from webhook.utils.get_objects import get_contact
    contact = get_contact(contact_id=contact_id)

    if contact:
        if not only_number:
            return f"{contact.country_code}{contact.ddd}{contact.contact_number}"
        else:
            return f"{contact.contact_number}"

    return None

def get_current_period(file_name=False) -> str:
    if file_name:
        return dt.today().strftime('%B/%Y').capitalize()

    return dt.today().strftime('%m/%y')



##-- Additional functions
def get_event_status(event, message_id: str = None, ticket_id: str = None):
    if event == 'ticket':
        ticket = get_ticket(ticket_id=ticket_id)
        return ticket.is_open if ticket else False

    if event == 'message':
        message = get_message(message_id=message_id)
        return message.status if message else 0

def update_ticket_last_message(ticket_id:str):
    response = any_digisac_request(f'/tickets/{ticket_id}', method='get', json=False)

    if response.status_code == 200:
        try:
            digisac_ticket = response.json()
            last_message_id = digisac_ticket.get('lastMessageId')
            is_open = digisac_ticket.get('isOpen')
            
            ticket = get_ticket(ticket_id=ticket_id)
            ticket.last_message_id = last_message_id
            ticket.is_open = is_open
            ticket.save()

            return "Show Papai. Atualizado!!"
        except Exception as e:
            raise ValueError(
                f"Algo de errado não está certo - {ticket_id}/{str(e)}")

    return "Nada foi feito! Ticket provavelmente ainda não foi criado"

def message_exists_in_digisac(message_id):
    message = any_digisac_request(f'/messages/{message_id}', method='get', json=True)

    if message['sent']:
        return True
    else: return False

def message_is_saved(message_id) -> bool:
    # Esse método retorna None se não encontrar o objeto, logo num if qualquer resposta
    # não deverá ter problema
    message = get_message(message_id=message_id)

    return True if message else False
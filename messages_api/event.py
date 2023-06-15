import os
import requests
from celery import shared_task
from datetime import datetime as dt

from webhook.utils.request import get_chat_protocol, any_request as digisac_api
from webhook.utils.logger import Logger
from webhook.utils.get_objects import get_contact, get_ticket, get_message


logger = Logger(__name__)
WEBHOOK_API = os.environ.get("WEBHOOK_API", os.getenv("WEBHOOK_API"))

def get_event_status(event, message_id: str = None, ticket_id: str = None):
    if event == 'ticket':
        ticket = get_ticket(ticket_id=ticket_id)
        return ticket.is_open if ticket else False

    if event == 'message':
        message = get_message(message_id=message_id)
        return message.status if message else 0


def get_contact_number(contact_id: str, only_number=False):
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


def uṕdate_ticket_last_message(ticket_id:str):
    response = digisac_api(f'/tickets/{ticket_id}', method='get', json=False)

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


def manage(data):
    event_handlers = {
        'message.created': (handle_message_created, ['id', 'isFromMe']),
        'message.updated': (handle_message_updated, ['id']),
        'ticket.created': (handle_ticket_created, ['id', 'contactId', 'lastMessageId']),
        'ticket.updated': (handle_ticket_updated, ['id'])
    }

    event = data.get('event')
    event_handler_func, params = event_handlers.get(event, (None, []))

    if event_handler_func:
        args = [data.get(param) for param in params]
        
        return event_handler_func.apply_async(args=[*args], kwargs={"data":data})

    return None



def message_exists_in_digisac(message_id):
    message = digisac_api(f'/messages/{message_id}', method='get')

    if message['sent']:
        return True
    else: return False


def message_is_saved(message_id) -> bool:
    # Esse método retorna None se não encontrar o objeto, logo num if qualquer resposta
    # não deverá ter problema
    message = get_message(message_id=message_id)

    return message

@shared_task(name='create_message', autoretry_for=((ValueError,)), retry_backoff=True, max_retries=3)
def handle_message_created(message_id, isFromMe, data=...):
    message_exists = message_exists_in_digisac(message_id=message_id)
    message_saved = message_is_saved(message_id=message_id)

    if message_exists and message_saved:
        handle_message_updated.apply_async(args=[message_id], kwargs={"data":data})
        return "Mensagem já existe mandada pra atualização"

    url = f"{WEBHOOK_API}/messages/create"

    contact_id = data.get('contactId')
    date = get_current_period()
    number = get_contact_number(contact_id=contact_id)
    parameters = {"phone": number, "period": date}
    message_type = data.get("type")
    message_body = {
        "message_id": message_id,
        "contact_id": contact_id,
        "timestamp": data.get('timestamp'),
        "status": data['data'].get('ack'),
        "ticket": data.get('ticketId'),
        "message_type": data.get('type'),
        "is_from_me": isFromMe,
        "text": data.get("text", message_type)
    }

    if number is None:
        raise ValueError(
            f'Consulta do telefone na {url} com id {contact_id} falhou')
    # if not isFromMe:
    response = requests.post(url, json=message_body, params=parameters)

    uṕdate_ticket_last_message(ticket_id=data.get('ticketId'))

    if not isFromMe and not response.status_code in range(400, 501):
        check_url = f'{WEBHOOK_API}/control/check_response'
        requests.get(check_url, params={"contact_id": contact_id})

    if response.status_code == 409:
        # logger.debug(f'{response} - {response.text}')
        return "Esta mensagem já existe por algum motivo chegou até aqui novamente. Verifique os logs"

    if response.status_code != 201:
        text = f"Failed to create message_id: {message_id}\n{response}-\n{response.text}"
        # logger.debug(text)
        raise ValueError(text)

    return response


@shared_task(name='update_message', retry_backoff=True, max_retries=3)
def handle_message_updated(message_id, data=...):
    if not message_id:
        return "Message vazio. diabo é isso?"
    
    message_exists = message_exists_in_digisac(message_id=message_id)
    message_saved = message_is_saved(message_id)

    if message_exists and not message_saved:
        handle_message_created.apply_async(args=[message_id, data.get('isFromMe')], kwargs={"data":data})
        return "Mensagem existe e não foi salva antes"
    try:
        message = get_message(message_id=message_id)
        actual_status = get_event_status('message', message_id=message_id)
        status = int(data['data'].get('ack')),
        if actual_status < status:
            # url = f"{WEBHOOK_API}/messages/update"
            # response = requests.patch(url, params={'id': message_id, 'status': status})

            if message:
                message.status = status
                message.save()
        else:
            return f"Status:{status} menor que o atual da mensagem com id: {message_id}"
        
    except Exception as e:
        logger.debug(e)

    return "Mensagem atualizada com sucesso" 


@shared_task(name='create_ticket', retry_backoff=True, max_retry=3)
def handle_ticket_created(ticket_id, contact_id, last_message_id):
    url = f'{WEBHOOK_API}/messages/create/ticket'
    params = {
        "id": ticket_id,
        "period": get_current_period(),
        "contact": contact_id,
        "last_message": last_message_id
    }

    response = requests.post(url, params=params)
    if response.status_code != 201:
        text = f"Failed to create ticket with id: {ticket_id}\n{response}-{response.text}"
        logger.debug(text)
        return text

    return response


@shared_task(name='update_ticket', autoretry_for=((ValueError, )), max_retries=3)
def handle_ticket_updated(ticket_id, data=...):

    try:
        actual_status = get_event_status('ticket', ticket_id=ticket_id)
        is_open = bool((data['data']['isOpen']))
        last_message_id = (data['data']['lastMessageId'])
        if actual_status and not is_open:
            url = f"{os.environ.get('WEBHOOK_API', os.getenv('WEBHOOK_API'))}/messages/update/ticket?id={ticket_id}&open=0&last_message={last_message_id}"
            response = requests.patch(url)

            if response.status_code in range(400, 404):
                logger.debug(f"Something wrong - {response.json()}")
                raise Exception(f"Something wrong - {response.json()}")

            if response.status_code != 200:
                text = f"{response}-{response.text}"
                logger.debug(text)

                raise ValueError(text)

            if response.status_code == 200:
                return response
        else:
            return (f"Status:{actual_status} - o ticket com id: {ticket_id} já está fechado ou ainda não foi criado")
    except ValueError as e:
        logger.debug(e)

    return response


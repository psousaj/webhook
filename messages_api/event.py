import os
import requests
from celery import shared_task

from control.functions import check_client_response
from webhook.utils.get_objects import get_message, get_ticket
from webhook.utils.logger import Logger
from webhook.utils.tools import (
        get_event_status, 
        message_is_saved, 
        get_current_period, 
        get_contact_number, 
        message_exists_in_digisac, 
        update_ticket_last_message,
    )

logger = Logger(__name__)

def load_env(var):
    return os.environ.get(var, os.getenv(var))

IS_LOCALHOST = load_env("IS_LOCALHOST")
WEBHOOK_API = load_env("WEBHOOK_API_LOCAL") if IS_LOCALHOST else load_env("WEBHOOK_API")


##-- Handler to events
@shared_task(name="handler_task")
def manage(data):
    event_handlers = {
        'message.created': (handle_message_created, ['id', 'isFromMe']),
        'message.updated': (handle_message_updated, ['id']),
        'ticket.created': (handle_ticket_created, ['id', 'contactId', 'lastMessageId']),
        'ticket.updated': (handle_ticket_updated, ['id'])
    }

    event = data.get('event')
    data = data.get('data')
    event_handler_func, params = event_handlers.get(event, (None, []))

    if (event == 'message.created' and not type(data) == list):
        if data.get('type', None) == 'ticket':
            return 

    if event_handler_func:
        args = [data.get(param) for param in params]
        
        event_handler_func.apply_async(args=args, kwargs={"data":data})

    return f"Event: {event} handled to the refers function"


##-- Tasks to handle events
@shared_task(name='create_message')
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
        "status": data['data']['ack'],
        "ticket": data.get('ticketId'),
        "message_type": data.get('type'),
        "is_from_me": isFromMe,
        "text": data.get("text", message_type)
    }

    if number is None:
        raise ValueError(
            f'Consulta do telefone:{number} na {url} com id {contact_id} falhou')
    # if not isFromMe:
    response = requests.post(url, json=message_body, params=parameters)

    update_ticket_last_message(ticket_id=data.get('ticketId'))

    if not isFromMe and not response.status_code in range(400, 501):
        check_client_response.apply_async(args=[contact_id])

    if response.status_code == 409:
        return "Esta mensagem já existe por algum motivo chegou até aqui novamente. Verifique os logs"

    if response.status_code != 201:
        text = f"Failed to create message_id: {message_id}\n{response}-\n{response.text}"
        raise ValueError(text)

    return response

@shared_task(name='update_message')
def handle_message_updated(message_id, data=...):
    if not message_id:
        return "Message vazio. diabo é isso?"
    
    message_exists = message_exists_in_digisac(message_id=message_id)
    message_saved = message_is_saved(message_id)

    if message_exists and not message_saved:
        handle_message_created.apply_async(args=[message_id, data.get('isFromMe')], kwargs={"data":data})
        return "Mensagem existe e não foi salva antes"
    try:
        data = data.get('data')
        message = get_message(message_id=message_id)
        actual_status = get_event_status('message', message_id=message_id)
        status = data['ack'][0] if isinstance(data['ack'], tuple) else data.get('ack')
        if actual_status < status:
            if message:
                message.status = status
                message.save()
        else:
            return f"Status:{status} menor que o atual da mensagem com id: {message_id}"
        
    except Exception as e:
        logger.debug(e)
        raise Exception(f"erro: {str(e)} - actual_staus:{type(actual_status)} e status = {type(status)}")

    return "Mensagem atualizada com sucesso" 

@shared_task(name='create_ticket')
def handle_ticket_created(ticket_id, contact_id, last_message_id, data=...):
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

@shared_task(name='update_ticket')
def handle_ticket_updated(ticket_id, data=...):
    actual_status = get_event_status('ticket', ticket_id=ticket_id)
    last_message_id = data.get('lastMessageId')
    is_open = data.get('isOpen')

    if actual_status and not is_open:
        ticket = get_ticket(ticket_id=ticket_id)

        try:
            if ticket:
                ticket.is_open = is_open
                ticket.last_message_id = last_message_id
                ticket.save()

        except Exception as e:
            raise ValueError(str(e))

        return "Ticket atualizado com sucesso"
    else:
        return f"Ticket com id: {ticket_id} já está fechado ou ainda não foi criado"



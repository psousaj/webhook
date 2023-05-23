import os
import json
import requests
from datetime import datetime as dt

from webhook.logger import Logger
from webhook.request import get_chat_protocol
from webhook.logger import Logger
# from messages_api.models import Message
# from messages_api.serializer import MessageSerializer

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist

logger = Logger(__name__)


def get_event_status(event, message_id: str = None, ticket_id: str = None) -> int:
    if event == 'ticket':
        url = f"{os.getenv('WEBHOOK_API')}/messages/tickets/status"
        response = requests.get(
            url, params={"id": ticket_id})

        if response.status_code == 200:
            response = response.json()[0]
            if response['is_open']:
                return True

        return False

    if event == 'message':
        url = f"{os.getenv('WEBHOOK_API')}/messages/list"
        response = requests.get(url, params={"id": message_id})

        if response.status_code == 200:
            return int(response.json()[0]['status'])


def extract_value(input_list):
    if (isinstance(input_list, list) or isinstance(input_list, tuple)):
        return input_list[0]

    return input_list


def get_phone_number(contactId: str):
    url = f"{os.getenv('WEBHOOK_API')}/contacts"
    response = requests.get(url, params={"id": contactId})

    if response.status_code == 200:
        contact = response.json()

        return f"{contact['country_code']}{contact['ddd']}{contact['contact_number']}"

    return None


def get_current_period() -> str:
    return dt.today().strftime('%m/%y')


def manage(data):
    try:
        event = data['event']
        # Protocolo para encaminhar no grupo
        protocol = get_chat_protocol(data["data"]["ticketId"])
        isFromMe: bool = data['data']['isFromMe'],
        message_id: str = data['data']['id'],

    except Exception as e:
        pass

    try:
        if event == 'message.created':
            if data['data']['origin'] == 'ticket':
                return

            return handle_message_created.apply_async(
                args=[data, extract_value(isFromMe)])
        if event == 'message.updated':
            return handle_message_updated.apply_async(
                args=[extract_value(message_id), data], countdown=5, queue='message_update')
        if event == 'ticket.created':
            id = extract_value(data['data']['id'])
            return handle_ticket_created.apply_async(args=[id])
        if event == 'ticket.updated':
            id = extract_value(data['data']['id'])
            return handle_ticket_updated.apply_async(args=[id, data])
    except KeyError as e:
        logger.debug(e)
    except TypeError as e:
        logger.debug(e)


@shared_task(name='create_message', retry_backoff=True, max_retry=3)
def handle_message_created(data, isFromMe: bool):
    url = "http://woz.serveo.net/webhook/messages/create"
    contact_id = data['data']['contactId']
    date = get_current_period()
    number = get_phone_number(contact_id)
    parameters = {"phone": number, "period": date['current_period']}
    message_body = {
        "message_id": data['data']['id'],
        "contact_id": contact_id,
        "timestamp": data['timestamp'],
        "status": data['data']['data']['ack'],
        "ticket": data['data']['ticketId'],
        "message_type": data['data']['type'],
        "is_from_me": isFromMe,
        "text": data['data']['text']
    }

    if number is None:
        raise ValueError(f'Consulta do telefone na {url} com id {contact_id}')
    # if not isFromMe:
    response = requests.post(url, json=message_body, params=parameters)
    if response.status_code != 201:
        text = f"Failed to create message_id: {data['data']['id']}\n{response}-{response.text}"
        logger.debug(text)
        raise ValueError(text)

    return response


@shared_task(bind=True, name='update_message', autoretry_for=((ObjectDoesNotExist),), retry_backoff=True, max_retries=3)
def handle_message_updated(self, message_id: str, data):

    try:
        actual_status = get_event_status('message', message_id=message_id)
        status = int(extract_value(data['data']['data']['ack'])),
        if actual_status < extract_value(status):
            url = f"{os.getenv('WEBHOOK_API')}/messages/update"
            response = requests.patch(
                url, params={'id': message_id, 'status': extract_value(status)})

            if response.status_code != 200:
                text = f"{response}-{response.text}"
                logger.debug(text)

                raise Exception(f"{text} - {status}")
        else:
            return f"Status:{status} menor que o atual da mensagem com id: {message_id}"
    except ValueError as e:
        raise self.retry(exc=f"{e} - {status}", countdown=60)
    except Exception as e:
        raise self.retry(exc=e, countdown=60)

    return response


@shared_task(name='create_ticket', retry_backoff=True, max_retry=3)
def handle_ticket_created(ticket_id: str):
    url = f'{os.getenv("WEBHOOK_API")}/messages/create/ticket'
    params = {
        "id": ticket_id,
        "period": get_current_period()
    }

    response = requests.post(url, params=params)
    if response.status_code != 201:
        text = f"Failed to create message_id: {id}\n{response}-{response.text}"
        logger.debug(text)
        return text

    return response


@shared_task(name='update_ticket', autoretry_for=((ValueError, )), max_retries=3)
def handle_ticket_updated(ticket_id: str, data):

    try:
        actual_status = get_event_status('ticket', ticket_id=ticket_id)
        is_open = bool(extract_value(data['data']['isOpen']))
        if actual_status and not is_open:
            url = f"{os.getenv('WEBHOOK_API')}/messages/update/ticket?id={ticket_id}&open=0"
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
            return (f"Status:False - o ticket com id: {ticket_id} já está fechado")
    except ValueError as e:
        logger.debug(e)

    return response

# def handle_message_confirm(data, cnpj, id_mess, confirm_file, name_company):
#     if 'text' in data['data']:
#         text = str(data['data']['text']).lower()
#         if text == 'sim':
#             response_messeger.send_finish(cnpj)
#             update_control_messager.update_question(
#                 data['data']['ticketId'], 'question-confirm', '4')
#         else:
#             handle_attempt(cnpj, 'question-confirm', name_company)
#     else:
#         handle_attempt(cnpj, 'question-confirm', name_company)


# def handle_message_text(data, cnpj, id_mess, confirm_file, name_company):
#     text = str(data['data']['text']).lower()
#     if text in ('sim', 'quero'):
#         folder, name = download_json_and_das_company.download(cnpj)
#         if folder:
#             send_files_competences.send(cnpj, name, folder, id_mess)
#             response_messeger.send_finish(cnpj)
#             update_control_messager.update_question(
#                 data['data']['ticketId'], 'question', '4')
#             close_ticket.close(cnpj)
#     elif text in ('nao', 'não'):
#         response_messeger.send_finish(cnpj)
#         update_control_messager.update_question(
#             data['data']['ticketId'], 'question', '4')
#         close_ticket.close(cnpj)
#     else:
#         handle_attempt(data, cnpj, 'question', name_company)


# def handle_attempt(data, cnpj, question, name_company):
#     attempt = verify_attempt.check_question(cnpj, question)
#     if attempt < 3:
#         response_messeger.send_negation_confirm(cnpj)
#         update_attempt.update_question(cnpj, question)
#     else:
#         response_messeger.send_tranfer(cnpj)
#         text_messeger = f"O cliente {name_company} solicita um atendimento - protocolo {protocol}"
#         send_message_group.send(text_messeger)
#         update_control_messager.update_question(
#             data['data']['ticketId'], question, '4')


# def handle_other_cases(data, cnpj, name_company):
#     response_messeger.send(data['data']['contactId'])
#     close_ticket.close(cnpj)
#     text_messeger = f"O cliente {name_company} solicita um atendimento"
#     send_message_group.send(text_messeger)

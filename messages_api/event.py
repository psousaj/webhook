import os
import json
import requests

from webhook.logger import Logger
from webhook.request import get_chat_protocol
from webhook.logger import Logger
# from messages_api.models import Message
# from messages_api.serializer import MessageSerializer

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist

logger = Logger(__name__)


def extract_value(input_list):
    if (isinstance(input_list, list) or isinstance(input_list, tuple)) and len(input_list) == 1:
        return input_list[0]


def get_phone_number(contactId: str):
    url = f"{os.getenv('COMPANIES_API')}/establishments/"
    response = requests.get(url)

    if response.status_code == 200:
        response = response.json()
        for est in response:
            # Garante que company_contact seja None se est['company_contact'] for uma lista vazia.
            company_contact = next(iter(est['company_contact']), None)
            est_contact_id = None if not company_contact else company_contact[
                'contact_id_digisac']
            if est_contact_id == contactId:
                return f"{company_contact['country_code']}{company_contact['ddd']}{company_contact['contact_number']}"

    return None


def get_date_dict() -> json:
    url = "http://localhost:8080/functions/date"
    return requests.get(url).json()


def manage(data):
    event = data['event']
    # Protocolo para encaminhar no grupo
    protocol = get_chat_protocol(data["data"]["ticketId"])
    # params = {
    #     'data': data,
    #     'isFromMe': data['data']['isFromMe'],
    #     'message_id': data['data']['id'],
    #     'status': data['data']['data']['ack'],
    # }
    isFromMe: bool = data['data']['isFromMe'],
    message_id: str = data['data']['id'],
    status: int = int(data['data']['data']['ack']),

    # Mapeia eventos para suas funções de manipulação correspondentes
    handler = {
        'message.created': handle_message_created,
        'message.updated': handle_message_updated,
        'ticket.created': "handle_ticket_created",
        'ticket.updated': "handle_ticket_updated"
    }

    try:
        if event == 'message.created':
            handle_message_created.apply_async(
                args=[data, extract_value(isFromMe)])
        if event == 'message.updated':
            handle_message_updated.apply_async(
                args=[extract_value(message_id), extract_value(status)], countdown=5)
        # # Obtém a função de manipulação apropriada para o evento
        # handler = handler[event]
        # func = handler[0]
        # params = handler[1]
        # # Invoca a função de manipulação com os parâmetros apropriados
        # return func.apply_async(args=params)
    except KeyError as e:
        logger.debug(e)


@shared_task(name='create_message', retry_backoff=True, max_retry=3)
def handle_message_created(data, isFromMe: bool):
    url = "http://woz.serveo.net/webhook/messages/create"
    contact_id = data['data']['contactId']
    date = get_date_dict()
    number = get_phone_number(contact_id)
    parameters = {"phone": number, "period": date['current_period']}
    message_body = {
        "message_id": data['data']['id'],
        "contact_id": contact_id,
        "timestamp": data['timestamp'],
        "status": data['data']['data']['ack'],
        "ticket_id": data['data']['ticketId'],
        "message_type": data['data']['type'],
        "is_from_me": isFromMe,
        "text": data['data']['text']
    }

    # if not isFromMe:
    response = requests.post(url, json=message_body, params=parameters)
    if response.status_code != 201:
        text = f"Failed to create message_id: {data['data']['id']}\n{response}-{response.text}"
        logger.debug(text)
        return text

    return response


@shared_task(bind=True, name='update_message', autoretry_for=((ObjectDoesNotExist),), retry_backoff=True, max_retries=3)
def handle_message_updated(self, message_id, status):
    try:
        url = f"{os.getenv('WEBHOOK_API')}/messages/update?id={message_id}&status={status}"
        response = requests.patch(url)

        if response.status_code != 200:
            text = f"{response}-{response.text}"
            logger.debug(text)

            raise Exception(text)
    except Exception as e:
        raise self.retry(exc=e, countdown=60)

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

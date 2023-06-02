from celery import shared_task
from webhook.request import get_chat_protocol, any_request
from webhook.logger import Logger
from contacts.get_objects import get_contact
from datetime import datetime as dt
import requests
import os


logger = Logger(__name__)


def get_event_status(event, message_id: str = None, ticket_id: str = None) -> int:
    if event == 'ticket':
        url = f"{os.environ.get('WEBHOOK_API', os.getenv('WEBHOOK_API'))}/messages/tickets/status"
        response = requests.get(
            url, params={"id": ticket_id})

        if response.status_code == 200:
            response = response.json()[0]
            if response['is_open']:
                return True

            return False
        elif response.status_code == 404:
            return False
    try:
        if event == 'message':
            url = f"{os.environ.get('WEBHOOK_API', os.getenv('WEBHOOK_API'))}/messages/list"
            response = requests.get(url, params={"id": message_id})

            if response.status_code == 200:
                return int(response.json()[0]['status'])
            else:
                return 0
    except KeyError as e:
        logger.debug(str(e))
    except Exception as e:
        logger.debug(e)


def extract_value(input_list):
    if (isinstance(input_list, list) or isinstance(input_list, tuple)):
        return input_list[0]

    return input_list


def get_phone_number(contactId: str, only_number=False):
    contact = get_contact(contactId)

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


def uṕdate_ticket_last_message(ticket_id):
    response = any_request(f'/tickets/{ticket_id}', method='get', json=False)

    if response.status_code == 200:
        ticket = response.json()
        last_message_id = ticket['lastMessageId']
        is_open = 1 if ticket['isOpen'] else 0
        params = {
            "id": ticket_id,
            "open": is_open,
            "last_message": last_message_id
        }
        ticket_response = requests.patch(
            f'{os.environ.get("WEBHOOK_API", os.getenv("WEBHOOK_API"))}/messages/update/ticket', params=params)

        if ticket_response.status_code == 200:
            return "Show Papai. Atualizado!!"
        elif ticket_response.status_code in range(405, 501):
            raise ValueError(
                f"Algo de errado não está certo - {ticket_response} - {ticket_response.text}")

        return "Nada foi feito! Ticket provavelmente ainda não foi criado"


def manage(data):
    try:
        event = data['event']
        # Protocolo para encaminhar no grupo
        isFromMe: bool = data['data']['isFromMe'],
        message_id: str = data['data']['id'],
    except Exception as e:
        message_id = None

    try:
        if event == 'message.created':
            if data['data']['origin'] == 'ticket':
                return

            return handle_message_created.apply_async(
                args=[data, extract_value(isFromMe)])

        if event == 'message.updated':
            return handle_message_updated.apply_async(
                args=[extract_value(message_id), data], countdown=5)
        if event == 'ticket.created':
            id = extract_value(data['data']['id'])
            contact_id = extract_value(data['data']['contactId'])
            last_message_id = extract_value(
                data['data']['lastMessageId']) if not "null" else "FIRST_MESSAGE"
            return handle_ticket_created.apply_async(args=[id, contact_id, last_message_id])
        if event == 'ticket.updated':
            id = extract_value(data['data']['id'])
            return handle_ticket_updated.apply_async(args=[id, data])
    except KeyError as e:
        logger.debug(e)
    except TypeError as e:
        logger.debug(e)


def message_exists_in_digisac(message_id):
    message = any_request(f'/messages/{message_id}', method='get')

    if message['sent']:
        return True


def message_is_saved(message_id):
    url = f"{os.environ.get('WEBHOOK_API', os.getenv('WEBHOOK_API'))}/messages/list"
    response = requests.get(url, params={"id": message_id})

    if response.status_code != 200:
        return False
    elif response.status_code == 200:
        return True


@shared_task(name='create_message', autoretry_for=((ValueError,)), retry_backoff=True, max_retry=3)
def handle_message_created(data, isFromMe: bool):
    message_exists = message_exists_in_digisac(data['data']['id'])
    message_saved = message_is_saved(data['data']['id'])

    if message_exists and message_saved:
        handle_message_updated.apply_async(
            args=[extract_value(data['data']['id']), data])
        return "Mensagem já existe mandada pra atualização"

    url = f"{os.environ.get('WEBHOOK_API', os.getenv('WEBHOOK_API'))}/messages/create"
    contact_id = data['data']['contactId']
    date = get_current_period()
    number = get_phone_number(contact_id)
    parameters = {"phone": number, "period": date}
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
        raise ValueError(
            f'Consulta do telefone na {url} com id {contact_id} falhou')
    # if not isFromMe:
    response = requests.post(url, json=message_body, params=parameters)

    uṕdate_ticket_last_message(
        ticket_id=extract_value(data['data']['ticketId']))

    if not isFromMe and not response.status_code in range(400, 501):
        check_url = f'{os.environ.get("WEBHOOK_API", os.getenv("WEBHOOK_API"))}/control/check_response'
        requests.get(check_url, params={"contact_id": contact_id})

    if response.status_code == 409:
        logger.debug(f'{response} - {response.text}')
        return "Esta mensagem já existe por algum motivo chegou até aqui novamente. Verifique os logs"

    if response.status_code != 201:
        text = f"Failed to create message_id: {data['data']['id']}\n{response}-\n{response.text}"
        logger.debug(text)
        raise ValueError(text)

    return response


@shared_task(bind=True, name='update_message', retry_backoff=True, max_retries=3)
def handle_message_updated(self, message_id: str, data):
    if not message_id:
        return "Message vazio. diabo é isso?"
    message_exists = message_exists_in_digisac(message_id=message_id)
    message_saved = message_is_saved(message_id)

    if message_exists and not message_saved:
        handle_message_created.apply_async(
            args=[data, extract_value(data['data']['isFromMe'])])

        return "Mensagem existe e não foi salva antes"
    try:
        actual_status = get_event_status(
            'message', message_id=message_id) if not None else 0
        status = int(extract_value(data['data']['data']['ack'])),
        if actual_status < extract_value(status):
            url = f"{os.environ.get('WEBHOOK_API', os.getenv('WEBHOOK_API'))}/messages/update"
            response = requests.patch(
                url, params={'id': message_id, 'status': extract_value(status)})

            if response.status_code != 200:
                text = f"{response}-{response.text}"
                logger.debug(text)

                raise Exception(f"{text} - {status}")
        else:
            return f"Status:{status} menor que o atual da mensagem com id: {message_id}"
    except TypeError as e:
        self.retry(exc=f"{e} - {status}", countdown=30)
    except KeyError as e:
        return f"Bug: str({e})"
    except ValueError as e:
        self.retry(exc=f"{e} - {status}", countdown=30)
    except Exception as e:
        self.retry(exc=f"{e} - {status}", countdown=30)

    return response


@shared_task(name='create_ticket', retry_backoff=True, max_retry=3)
def handle_ticket_created(ticket_id: str, contact_id, last_message_id):
    url = f'{os.environ.get("WEBHOOK_API", os.getenv("WEBHOOK_API"))}/messages/create/ticket'
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
def handle_ticket_updated(ticket_id: str, data):

    try:
        actual_status = get_event_status('ticket', ticket_id=ticket_id)
        is_open = bool(extract_value(data['data']['isOpen']))
        last_message_id = extract_value(data['data']['lastMessageId'])
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

import os
import re
from celery import shared_task
from datetime import datetime as dt
from django.shortcuts import get_object_or_404

import requests
from messages_api.event import get_current_period, get_phone_number
from webhook.request import any_request
from webhook.logger import Logger
from control.models import MessageControl
from control.text import saudacao, disclaimer, get_pendencies_text


from rest_framework.decorators import api_view
from rest_framework.response import Response

logger = Logger(__name__)


def is_match(input_word, responses, exact_match):
    if exact_match:
        return any(word in input_word.split() for word in responses.split('|'))

    return bool(re.search(responses, input_word, re.IGNORECASE))


def process_input(sentence, contact_id, retries, pendencies, exact_match):
    positive_responses = r"\b(sim|bacana|ok|tá|ta|bom|recebi|receb|na\shora|ótimo|beleza|blz|entendi|show|confirmado|confirme|tá\sótimo|massa|s|manda|mande|envia|pode|👍|👍🏾|👍🏻|👍🏼|👍🏿|pode\sser)\b"
    # |não\smande|nao\smande
    negative_responses = r"\b(n|nao|pare|parar|stop|não)\b"
    assistance_requests = r"\b(atendente|humano|pessoa|atendimento|atedente|sair)\b"

    if is_match(sentence, positive_responses, exact_match) and not is_match(sentence, negative_responses, exact_match):
        if pendencies:
            send_message(
                contact_id, text="Vou enviar os arquivos agora mesmo!")
        else:
            send_message(contact_id, text="Obrigado por confirmar!")

        return True

    if pendencies and is_match(sentence, negative_responses, exact_match):
        send_message(
            contact_id, text="Tudo bem! Caso necessite de mais alguma coisa, não hesite em nos perguntar!")
        return True

    if is_match(sentence, assistance_requests, exact_match) or retries >= 3:
        send_message(
            contact_id, text="Estou lhe encaminhando para um de nossos atendentes. Aguarde por favor!\n\nOlá, SOU SEU ATENDENTE FICTÍCIO!!")
        return True

    return False


def generate_error_message(retries, pendencies) -> str:
    base_message = "\nDesculpe, não entendi. Por favor, responda SIM, OK ou "
    if pendencies:
        base_message += "NÃO caso não queira os boletos agora."
    else:
        base_message += "RECEBI."

    if retries >= 2:
        base_message += '\nSe precisar falar com um de nossos atendentes digite "atendente"'
    return base_message


@shared_task(bind=True, name='check_response', retry_backoff=True, max_retries=5)
def check_client_response(self, contact_id):
    try:
        contact_number = get_phone_number(contact_id, only_number=True)
        contact_number = get_phone_number(contact_id, only_number=True)
        period = dt.strptime(get_current_period(),
                             "%m/%y").strftime('%Y-%m-%d')
        logger.info(period)
        control = get_object_or_404(
            MessageControl, contact=contact_number, period=period)

        # if control.DoesNotExist:
        #     raise ValueError('Controle de chamado inexistente')
        if control.status == 0 and not control.is_from_me_last_message():
            message_text = control.get_last_message_text()
            pendencies = control.pendencies
            control_retries = control.retries
            retries = 1

            # process_input(message_text, contact_id, retries,
            #               pendencies, exact_match=False)

            while True:
                while not process_input(message_text, control_retries, pendencies, exact_match=False):
                    if control_retries >= 3 and not process_input(message_text, control_retries, pendencies, exact_match=False):
                        close_ticket(contact_id)
                        break

                    user_input = send_message(
                        contact_id, text=generate_error_message(control_retries, pendencies))
                    retries += 1

                break
        elif control.status == 0 and control.is_from_me_last_message():
            # time.sleep(15)
            return "Aguardando resposta ainda"

    except Exception as e:
        logger.debug(e)
        raise self.retry(exc=f"{e}", countdown=30)


@shared_task(name='close-ticket')
def close_ticket(contact_id):
    return any_request(f'/contacts/{contact_id}/ticket/close', method='post', json=False)


@shared_task(name='open-ticket')
def open_ticket(contact_id):
    return any_request(f'/contacts/{contact_id}/ticket/transfer', method='post', json=False)


def get_message_json(contact_id, message, file_b64, subject="Sem Assunto"):
    body = {
        "text": "PDF" if file_b64 else message,
        "type": "chat || comment",
        "contactId": contact_id,
        "subject": subject,
        "file" if file_b64 else None: {
            "base64": file_b64,
            "mimetype": "application/pdf",
            "name": f"DAS MEI {get_current_period(file_name = True)}"
        }
    }

    return body


def send_message(contact_id, text="", file=None, create_ticket=False):
    body = get_message_json(contact_id, text, file)

    if create_ticket:
        open_ticket(contact_id)
        return any_request('/messages', body=body, method='post')

    return any_request('/messages', body=body, method='post')


@api_view(['GET'])
def init_app(request):
    url = f"{os.environ.get('WEBHOOK_API', os.getenv('WEBHOOK_API'))}/contacts"
    response = requests.get(
        url, params={'cnpj': request.query_params.get('cnpj')})

    # try:
    if response.status_code == 200:
        contact = response.json()
        contact_id = contact[0]['contact_id']
        file = request.data.get('pdf')
        pendencies = request.data.get('pendencies')
        pendencies_text = get_pendencies_text(pendencies)

        send_message(contact_id, text=saudacao, create_ticket=True)
        send_message(contact_id, file=file)

        if pendencies:
            send_message(contact_id, text=pendencies_text)
        else:
            send_message(contact_id, text=disclaimer)

    return Response({'success': 'message_sent'})
    # except Exception as e:
    #     logger.debug(str(e))
    #     return Response({'error': str(e)}, status=500)

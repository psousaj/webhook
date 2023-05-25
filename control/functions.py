import os
import re
import time
from celery import shared_task
from datetime import datetime as dt
from django.http import Http404, JsonResponse
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


def format_responses(responses):
    responses = re.sub(r"\\b|\(\)|\(|\)", "", responses)
    responses = responses.replace('\\s', " ")
    return responses


def is_match(input_word, responses, exact_match):
    if exact_match:
        responses = format_responses(responses)
        return any(word in input_word.split() for word in responses.split('|'))

    return bool(re.search(responses, input_word, re.IGNORECASE))


def process_input(sentence, contact_id, retries, pendencies, exact_match):
    positive_responses = r"\b(sim|bacana|ok|tá|ta|bom|recebi|receb|na\shora|ótimo|beleza|blz|entendi|show|confirmado|confirme|tá\sótimo|massa|s|manda|mande|envia|pode|👍|👍🏾|👍🏻|👍🏼|👍🏿|pode\sser)\b"
    # |não\smande|nao\smande
    negative_responses = r"\b(n|nao|pare|parar|stop|não|\?)\b"
    assistance_requests = r"\b(atendente|humano|pessoa|atendimento|atedente|sair|porque|Porque|Por que|por que|Por quê)\b"

    if is_match(sentence, positive_responses, exact_match) and not is_match(sentence, negative_responses, exact_match):
        if pendencies:
            send_message(
                contact_id, text="Vou enviar os arquivos agora mesmo!")
            close_ticket.apply_async(args=[contact_id])
        else:
            send_message(contact_id, text="Obrigado por confirmar!")
            close_ticket.apply_async(args=[contact_id])
        return "Atendimento encerrado com sucesso!"

    if pendencies and is_match(sentence, negative_responses, exact_match):
        send_message(
            contact_id, text="Tudo bem! Caso necessite de mais alguma coisa, não hesite em nos perguntar!")
        close_ticket.apply_async(args=[contact_id])
        return "Atendimento Encerrado com sucesso! Cliente não quis o boleto"

    if is_match(sentence, assistance_requests, exact_match) or retries >= 3:
        send_message(
            contact_id, text="Tudo bem! Estou lhe encaminhando para um de nossos atendentes. Aguarde por favor!\n\nOlá, SOU SEU ATENDENTE FICTÍCIO!!")
        close_ticket.apply_async(args=[contact_id])
        return "Encaminhado para um atendente"

    error_text: str = generate_error_message(retries, pendencies)
    send_message(contact_id, text=error_text)
    return "Mensagem de erro enviada"


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
        period = dt.strptime(get_current_period(),
                             "%m/%y").strftime('%Y-%m-%d')
        control = get_object_or_404(
            MessageControl, contact=contact_number, period=period)

        if control.status == 0 and not control.is_from_me_last_message():
            message_text = control.get_last_message_text()
            pendencies = control.pendencies
            retries = control.retries
            control.retries += 1
            control.save()

            return process_input(message_text, contact_id, retries,
                                 pendencies, exact_match=False)
        return "Aguardando resposta do cliente"

    except Exception as e:
        logger.debug(e)
        raise self.retry(exc=f"{e}", countdown=15)


@shared_task(name='close-ticket')
def close_ticket(contact_id):
    contact_number = get_phone_number(contact_id, only_number=True)
    period = dt.strptime(get_current_period(),
                         "%m/%y").strftime('%Y-%m-%d')
    control = get_object_or_404(
        MessageControl, contact=contact_number, period=period)

    # Fechar Control:
    control.status = 1
    control.save()
    # Fechar Ticket
    any_request(f'/contacts/{contact_id}/ticket/close',
                method='post', json=False)


def get_control_object(contact_id):
    try:
        contact_number = get_phone_number(contact_id, only_number=True)
        period = dt.strptime(get_current_period(),
                             "%m/%y").strftime('%Y-%m-%d')
        control = get_object_or_404(
            MessageControl, contact=contact_number, period=period)

        return control
    except Http404 as e:
        logger.debug(str(e))
        return None


@shared_task(name='update_control_pendencies')
def update_ticket_control_pendencies(contact_id, pendencies):
    control = get_control_object(contact_id)
    while not control:
        time.sleep(1)
    control.pendencies = pendencies
    control.save()

    return f"Pendencias atualizadas contact_id: {contact_id}"


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

    # if create_ticket:
    #     any_request('/messages', body=body_create_ticket, method='post')
    #     return any_request('/messages', body=body, method='post')

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
            update_ticket_control_pendencies.apply_async(
                args=[contact_id, True])
        else:
            send_message(contact_id, text=disclaimer)

    return Response({'success': 'message_sent'})
    # except Exception as e:
    #     logger.debug(str(e))
    #     return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def check_client_response_viewset(request):
    try:
        contact_id = request.query_params.get('contact_id')
        check_client_response.apply_async(args=[contact_id])

        return JsonResponse({"Status": "Message check is in process"})
    except Exception as e:
        logger.debug(str(e))
        return Response({'Status': 'Something was wrong', 'message': f'{str(e)}'}, status=500)

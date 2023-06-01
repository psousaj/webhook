import os
import re
import time
from celery import shared_task
from datetime import datetime as dt
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404

from messages_api.event import get_current_period, get_phone_number
from contacts.get_objects import get_contact, get_any_contact
from webhook.request import any_request
from webhook.logger import Logger
from webhook.get_objects import get_pendencies
from control.models import MessageControl
from control.text import saudacao, disclaimer, get_pendencies_text


from rest_framework.decorators import api_view
from rest_framework.response import Response

logger = Logger(__name__)

POSITIVE_RESPONSES = r"\b(sim|bacana|ok|tá|ta|bom|recebi|receb|na\shora|ótimo|beleza|blz|entendi|show|confirmado|confirme|tá\sótimo|massa|s|manda|mande|envia|pode|👍|👍🏾|👍🏻|👍🏼|👍🏿|pode\sser)\b"
NEGATIVE_RESPONSES = r"\b(n|nao|pare|parar|stop|não|\?|nada)\b"
ASSISTANCE_REQUESTS = r"\b(atendente|humano|pessoa|atendimento|atedente|sair|porque|Porque|Por que|por que|Por quê)\b"


def format_responses(responses):
    responses = re.sub(r"\\b|\(\)|\(|\)", "", responses)
    responses = responses.replace('\\s', " ")
    return responses


def is_match(input_word, responses, exact_match):
    if exact_match:
        responses = format_responses(responses)
        return any(word in input_word.split() for word in responses.split('|'))

    return bool(re.search(responses, input_word, re.IGNORECASE))


def process_input(sentence: str, contact_id: str, retries, pendencies: bool, exact_match, message_confirmed=False, ticket_closed=False, client_needs_help=False):
    if (message_confirmed and ticket_closed and not client_needs_help) or message_confirmed and not client_needs_help:
        send_message(
            contact_id, text=f"Esse canal é apenas para o envio de documentos.\nDeseja falar com um atendente? (Sim / Não)")
        switch_client_needs_help.apply_async(args=[contact_id, True])
        return "Mensagem não esperada. Troca de canal enviada"

    if message_confirmed and client_needs_help:
        if is_match(sentence, POSITIVE_RESPONSES, exact_match) and not is_match(sentence, NEGATIVE_RESPONSES, exact_match):
            transfer_ticket.apply_async(args=[contact_id], kwargs={
                                        "motivo": "Atendente solicitado no canal de documentos"})
            send_message(
                contact_id, text="Estou solicitando um atendente para você. Aguarde um pouco por gentileza.")
            ticket_message = close_ticket.apply_async(
                args=[contact_id], countdown=60)
            switch_client_needs_help.apply_async(args=[contact_id, False])
            return f"Troca de canal enviada e {ticket_message}"
        elif is_match(sentence, NEGATIVE_RESPONSES, exact_match):
            send_message(
                contact_id, text="Tudo bem! Caso necessite de mais alguma coisa, não hesite em nos perguntar!")
            switch_client_needs_help.apply_async(args=[contact_id, False])
            confirm_message.apply_async(args=[contact_id])
            return "Atendimento inesperado encerrado com sucesso! Cliente não quis atendente"
        else:
            send_message(
                contact_id, text="Este canal é para documentos, se precisar de um atendente informe por gentileza (Sim/Não)")
            ticket_message = close_ticket.apply_async(
                args=[contact_id], countdown=60)
            return "Dúvida. resposta indefinida: não disse explicitamente se quer atendente"

    if is_match(sentence, POSITIVE_RESPONSES, exact_match) and not message_confirmed:
        if pendencies:
            send_message(
                contact_id, text="Vou enviar os arquivos agora mesmo!")
            get_contact_pendencies_and_send.apply_async(args=[contact_id])
            confirm_message.apply_async(args=[contact_id])
            return "Cliente solicitou os arquivos"
        else:
            send_message(contact_id, text="Obrigado por confirmar!")
            confirm_message.apply_async(args=[contact_id])
        return "Atendimento encerrado com sucesso!"

    if pendencies and is_match(sentence, NEGATIVE_RESPONSES, exact_match):
        send_message(
            contact_id, text="Tudo bem! Caso necessite de mais alguma coisa, não hesite em nos perguntar!")
        confirm_message.apply_async(args=[contact_id])
        return "Atendimento Encerrado com sucesso! Cliente não quis o boleto"

    if is_match(sentence, ASSISTANCE_REQUESTS, exact_match) or retries >= 3 and not ticket_closed:
        send_message(
            contact_id, text="Tudo bem! Em instantes um de nossos atendentes entrará em contato!")
        confirm_message.apply_async(args=[contact_id], kwargs={"timeout": 0})

        if retries >= 3:
            transfer_ticket.apply_async(args=[contact_id], kwargs={
                "motivo": "3 tentativas de resposta não compreendidas automaticamente"})
        else:
            transfer_ticket.apply_async(args=[contact_id], kwargs={
                                        "motivo": "Atendente solicitado no canal de documentos"})

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


@shared_task(name='client-needs-help')
def switch_client_needs_help(contact_id, boolean):
    contact = get_contact(contact_id)
    period = dt.strptime(get_current_period(),
                         "%m/%y").strftime('%Y-%m-%d')
    control = get_object_or_404(
        MessageControl, contact=contact.contact_number, period=period)

    control.client_needs_help = boolean

    return control.save()


@shared_task(bind=True, name='check_response', retry_backoff=True, max_retries=3)
def check_client_response(self, contact_id):
    try:
        contact_number = get_phone_number(contact_id, only_number=True)
        period = dt.strptime(
            get_current_period(),
            "%m/%y"
        ).strftime('%Y-%m-%d')
        control = get_object_or_404(
            MessageControl,
            contact=contact_number,
            period=period
        )

        # Se a última mensagem é do sistema, então retorna diretamente
        if control.is_from_me_last_message():
            return f"Aguardando resposta do cliente"

        message_text = control.get_last_message_text()
        pendencies = control.pendencies
        retries = control.retries

        # Caso o status seja 0 (Aguardando Resposta)
        if control.status == 0:
            control.retries += 1
            control.save()

        # Caso o status seja 1 (Fechado)
        elif control.status == 1:

            # Verifica se a resposta é positiva
            if is_match(message_text, POSITIVE_RESPONSES, exact_match=False and not is_match(message_text, NEGATIVE_RESPONSES, exact_match=False)):
                control.client_needs_help = True
            # else:
                # control.client_needs_help = False

            control.save()

        return process_input(message_text, contact_id, retries, pendencies,
                             message_confirmed=(control.status == 1),
                             ticket_closed=not control.ticket.is_open,
                             client_needs_help=control.client_needs_help,
                             exact_match=False)

    except Exception as e:
        logger.debug(e)
        raise self.retry(exc=f"{e}", countdown=15)


@shared_task(name='close-ticket')
def close_ticket(contact_id):
    response = any_request(f'/contacts/{contact_id}/ticket/close',
                           method='post', json=False)
    if response.status_code == 200:
        return "ticket fechado"

    return f"Erro na requisição - {response.text}"


@shared_task(name='confirm-message')
def confirm_message(contact_id, closeTicket=True, timeout=120):
    contact_number = get_phone_number(contact_id, only_number=True)
    period = dt.strptime(get_current_period(),
                         "%m/%y").strftime('%Y-%m-%d')
    control = get_object_or_404(
        MessageControl, contact=contact_number, period=period)

    # Fechar Control:
    control.status = 1
    control.save()
    # Fechar Ticket
    if closeTicket:
        close_ticket.apply_async(args=[contact_id], countdown=timeout)

    return "Mensagem confirmada" if not closeTicket else "Mensagem confirmada, ticket não foi fechado"


@shared_task(name='transfer-ticket')
def transfer_ticket(contact_id, motivo=None):
    contact = get_contact(contact_id)
    protocol = get_object_or_404(
        MessageControl, contact=contact.contact_number)

    motivo_str = f"\n\nMotivo: {motivo}" if motivo is not None else ""
    send_message(
        os.environ.get('WOZ_GROUP_ID', os.getenv('WOZ_GROUP_ID')),
        text=f"O cliente: {contact.company_name}\nSOLICITA ATENDIMENTO{motivo_str}\n\nProtocolo: {protocol.get_protocol_number()}")

    return "Solicitação de atendimento enviada para o grupo WOZ - RELATÓRIOS"


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
        "text": "PDF" if file_b64 and not message else message,
        "type": "chat || comment",
        "contactId": contact_id,
        "subject": subject,
        "file" if file_b64 else None: {
            "base64": file_b64,
            "mimetype": "application/pdf",
            "name": f"DAS MEI {get_current_period(file_name = True)}" if not message else f"DAS MEI {message}"
        }
    }

    return body


def send_message(contact_id, text="", file=None):
    body = get_message_json(contact_id, text, file)

    return any_request('/messages', body=body, method='post')


@api_view(['GET'])
def init_app(request):
    try:
        contact = get_any_contact(cnpj=request.query_params.get('cnpj'))
        contact_teste = get_any_contact(cnpj='12345678')

        pendencies_list = get_pendencies(contact.contact_id)
        pendencies_list = pendencies_list[:5]
        # pendencies_list = None
        file = request.data.get('pdf')

        send_message(contact_teste.contact_id, text=saudacao)
        send_message(contact_teste.contact_id, file=file)

        if pendencies_list:
            pendencies_text = [
                pendencies.period.strftime("%B/%Y") for pendencies in pendencies_list
            ]
            pendencies_message = get_pendencies_text(
                ", ".join(pendencies_text)
            )

            send_message(contact_teste.contact_id, text=pendencies_message)
            update_ticket_control_pendencies.apply_async(
                args=[contact_teste.contact_id, True])
        else:
            send_message(contact_teste.contact_id, text=disclaimer)

        return Response({'success': 'message_sent'})
    except Exception as e:
        logger.debug(str(e))
        return Response({'error': str(e)}, status=500)


@shared_task(name='send-pendencies')
def get_contact_pendencies_and_send(contact_id):
    try:
        contact2 = get_contact(contact_id)
        contact = get_contact("a8f7d632-6441-427a-8210-aea66effa35d")
        pendencies_list = contact.get_pendencies()
        # pendencies_list = pendencies_list[:5]

        if len(pendencies_list) > 5:
            send_message(
                contact2.contact_id,
                text=f"Número de pendencias({len(pendencies_list)}) maior que 5, te encaminhei para um atendente.\nAguarde que logo entraremos em contato"
            )
            transfer_ticket.apply_async(args=[contact2.contact_id], kwargs={
                                        "motivo": f"Número de pendencias DAS({len(pendencies_list)}) maior que 5"})
            return "número de pendencias maior que 5, atendente solicitado"

        for pendencie in pendencies_list:
            competence = pendencie.period.strftime("%B/%m")
            send_files(contact2.contact_id, competence, pendencie.pdf)

        close_ticket.apply_async(args=[contact_id])
        return "pendencias enviadas ao cliente com sucesso"
    except Exception as e:
        return e


def send_files(contact_id, pendencie, file):
    try:
        send_message(contact_id, text=pendencie, file=file)
    except Exception as e:
        logger.debug(str(e))
        return Response(f"Deu certo não: {e}")

    return Response("Deu certo!")


@api_view(['GET'])
def check_client_response_viewset(request):
    try:
        contact_id = request.query_params.get('contact_id')
        check_client_response.apply_async(args=[contact_id])
        logger.info("FUI CHAMADO AQUI Ó")

        return JsonResponse({"Status": "Message check is in process"})
    except Exception as e:
        logger.debug(str(e))
        return Response({'Status': 'Something was wrong', 'message': f'{str(e)}'}, status=500)


@api_view(['GET'])
def transfer_ticket_viewset(request):
    cnpj = request.query_params.get('cnpj')
    contact = get_any_contact(cnpj=cnpj)

    transfer_ticket.apply_async(args=[contact.contact_id])

    return Response("Successfully requested for an atendant")

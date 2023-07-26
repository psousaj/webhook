import os
import re
from celery import shared_task
from datetime import datetime as dt

from rest_framework.decorators import api_view
from rest_framework.response import Response

from control.models import DASFileGrouping

from webhook.utils.text import Answers, BaseText, TransferTicketReasons as Reasons
from webhook.utils.get_objects import get_contact, get_message_control, get_company_contact
from webhook.utils.tools import (
    get_current_period, 
    get_contact_number, 
    any_digisac_request,
    group_das_to_send
)
from webhook.utils.logger import Logger

logger = Logger(__name__)
## -----
SAUDACAO_TEXT = BaseText.saudacao.value
DISCLAIMER_TEXT = BaseText.disclaimer.value
## -----
POSITIVE_RESPONSES = r"\b(sim|bacana|ok|tá|ta|bom|recebi|receb|na\shora|ótimo|beleza|blz|entendi|show|confirmado|confirme|tá\sótimo|massa|s|manda|mande|envia|pode|👍|👍🏾|👍🏻|👍🏼|👍🏿|pode\sser)\b"
NEGATIVE_RESPONSES = r"\b(n|nao|pare|parar|stop|não|\?|nada)\b"
ASSISTANCE_REQUESTS = r"\b(atendente|humano|pessoa|atendimento|atedente|sair|porque|Porque|Por que|por que|Por quê)\b"
NOT_CHAT_TYPES = r"\b(image|document|sticker)\b"


##-- Parses texts and get actions to anwers
def response_parse_handler(responses):
    responses = re.sub(r"\\b|\(\)|\(|\)", "", responses)
    responses = responses.replace('\\s', " ")
    return responses

def is_match(client_response_text, responses, exact_match):
    if exact_match:
        responses = response_parse_handler(responses)
        return any(word in client_response_text.split() for word in responses.split('|'))

    return bool(re.search(responses, client_response_text, re.IGNORECASE))

def process_input(sentence: str, contact_id: str, retries:int, pendencies: bool, exact_match:bool, chat_confirmed=False, ticket_closed=False, client_needs_help=False):
    
    # isso trata de: recebimento confirmado, ticket fechado, e se é uma mensagem inesperada (client_needs_help: False)
    # ou se o cliente confirmou, é mensagem inesperada, e o ticket ainda está agendado para fechar (se ele mandar mensagem assim que finalizar)
    # ex: obrigado, valeu, etc.
    if (chat_confirmed and ticket_closed and not client_needs_help) or chat_confirmed and not client_needs_help:
        send_message(contact_id, text=Answers.UNEXPECTED_MESSAGE.value)
        #Alterna o client_needs_help para True para analisar a resposta dele após essa mensagem
        switch_client_needs_help.apply_async(args=[contact_id, True])

        return "Mensagem não esperada. Troca de canal enviada"

    if chat_confirmed and client_needs_help:
        if is_match(sentence, POSITIVE_RESPONSES, exact_match) and not is_match(sentence, NEGATIVE_RESPONSES, exact_match):
            transfer_ticket.apply_async(args=[contact_id], kwargs={"motivo": Reasons.ASK_FOR_ATTENDANT.value})
            send_message(contact_id, text=Answers.ASK_FOR_ATTENDANT.value)
            ticket_message = close_ticket.apply_async(args=[contact_id], countdown=30)
            switch_client_needs_help.apply_async(args=[contact_id, False])

            return f"Troca de canal enviada e {ticket_message}"
        
        elif is_match(sentence, NEGATIVE_RESPONSES, exact_match):
            send_message(contact_id, text=Answers.DONT_NEED_ATTENDANT.value)
            switch_client_needs_help.apply_async(args=[contact_id, False])
            confirm_message.apply_async(args=[contact_id])

            return "Atendimento inesperado encerrado com sucesso! Cliente não quis atendente"
        
        else:
            send_message(contact_id, text=Answers.RETRY_ASK_FOR_ATTENDANT.value)
            ticket_message = close_ticket.apply_async(args=[contact_id], countdown=60)

            return "Dúvida. resposta indefinida: Perguntando novamente se quer atendente"

    if is_match(sentence, POSITIVE_RESPONSES, exact_match) and not chat_confirmed and not is_match(sentence, NEGATIVE_RESPONSES, exact_match):
        if pendencies:
            send_message(contact_id, text=Answers.PENDENCIES_SEND_CONFIRMED.value)
            get_contact_pendencies_and_send.apply_async(args=[contact_id])
            confirm_message.apply_async(args=[contact_id], kwargs={"closeTicket": False})

            return "Cliente solicitou os arquivos"
        
        else:
            send_message(contact_id, text=Answers.MESSAGE_CONFIRMED.value)
            confirm_message.apply_async(args=[contact_id])

        return "Atendimento encerrado com sucesso!"

    if pendencies and is_match(sentence, NEGATIVE_RESPONSES, exact_match):
        send_message(contact_id, text=Answers.NEGATIVE_RESPONSE.value)
        confirm_message.apply_async(args=[contact_id])

        return "Atendimento Encerrado com sucesso! Cliente não quis o boleto"

    if is_match(sentence, NOT_CHAT_TYPES, exact_match=True):
        send_message(contact_id, text=Answers.NOT_TEXT_MESSAGE_RECEIVED.value)

        return "Recebi um documento, imagem ou figurinha"

    if is_match(sentence, ASSISTANCE_REQUESTS, exact_match) or retries >= 3 and not ticket_closed:
        send_message(contact_id, text=Answers.ASK_ASSISTANCE.value)
        confirm_message.apply_async(args=[contact_id])

        if retries >= 3:
            transfer_ticket.apply_async(args=[contact_id], kwargs={"motivo": Reasons.EXCEPT_RETRIES.value})
        else:
            transfer_ticket.apply_async(args=[contact_id], kwargs={"motivo": Reasons.ASK_FOR_ATTENDANT.value})

        return "Encaminhado para um atendente"

    error_text = generate_error_message(retries, pendencies)
    send_message(contact_id, text=error_text)
    return "Mensagem de erro enviada"

def generate_error_message(retries, pendencies) -> str:
    base_message = Answers.BASE_ERROR_MESSAGE.value
    if pendencies:
        base_message += Answers.HAS_DEBITS_ERROR_COMPLETION.value
    else:
        base_message += Answers.NO_DEBIT_ERROR_COMPLETION.value

    if retries >= 2:
        base_message += Answers.ATTENDANT_ERROR_COMPLETION.value

    return base_message


##-- Manage message states
def get_control_object(contact_id):
    contact_number = get_contact_number(contact_id, only_number=True)
    period = dt.strptime(get_current_period(), "%m/%y").strftime('%Y-%m-%d')

    control = get_message_control(contact=contact_number, period=period)

    return control

def get_message_json(contact_id, message, file_b64, subject="Sem Assunto", competence=None):
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

    return any_digisac_request('/messages', body=body, method='post')

def send_files(contact_id, pendencie, file):
    try:
        send_message(contact_id, text=pendencie, file=file)
        return Response("Deu certo!")
    except Exception as e:
        return Response(f"Deu certo não: {e}")


##-- Functional tasks to app
@shared_task(name='client-needs-help')
def switch_client_needs_help(contact_id, boolean):
    control = get_control_object(contact_id=contact_id)

    control.client_needs_help = boolean

    return control.save()

@shared_task(name='check_response')
def check_client_response(contact_id):
    control = get_control_object(contact_id=contact_id)

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

        control.save()

    return process_input(message_text, contact_id, retries, pendencies,
                            chat_confirmed=(control.status == 1),
                            ticket_closed=not control.ticket.is_open,
                            client_needs_help=control.client_needs_help,
                            exact_match=False)

@shared_task(name='close-ticket')
def close_ticket(contact_id):
    response = any_digisac_request(f'/contacts/{contact_id}/ticket/close', method='post', json=False)
    if response.status_code == 200:
        return "ticket fechado"

    return f"Erro na requisição - {response.text}"

@shared_task(name='confirm-message')
def confirm_message(contact_id, closeTicket=True, timeout=30):
    control = get_control_object(contact_id=contact_id)
    # Fechar Control:
    control.status = 1
    control.save()
    # Fechar Ticket
    if closeTicket:
        close_ticket.apply_async(args=[contact_id], countdown=timeout)

    return "Mensagem confirmada" if not closeTicket else "Mensagem confirmada, ticket não foi fechado"

@shared_task(name='transfer-ticket')
def transfer_ticket(contact_id, motivo=None):
    contact = get_contact(contact_id=contact_id)
    protocol = get_control_object(contact_id=contact_id)

    motivo_str = f"\n\nMotivo: {motivo}" if motivo is not None else ""
    send_message(
        os.environ.get('WOZ_GROUP_ID', os.getenv('WOZ_GROUP_ID')),
        text=f"O cliente: {contact.company_contact.first().responsible_name}\nSOLICITA ATENDIMENTO{motivo_str}\n\nProtocolo: {protocol.get_protocol_number()}")

    return "Solicitação de atendimento enviada para o grupo WOZ - RELATÓRIOS"

@shared_task(name='update_control_pendencies')
def update_ticket_control_pendencies(contact_id, pendencies):
    control = get_control_object(contact_id=contact_id)

    control.pendencies = pendencies
    control.save()

    return f"Pendencias atualizadas contact_id: {contact_id}"

@shared_task(name='send-pendencies')
def get_contact_pendencies_and_send(contact_id):
    try:
        contact = get_contact(contact_id=contact_id)
        pendencies_list = contact.get_pendencies()

        if len(pendencies_list) > 5:
            send_message(
                contact_id,
                text=Answers.get_text_with_replace('MORE_THAN_FIVE_PENDENCIES', len(pendencies_list))
            )
            transfer_ticket.apply_async(
                args=[contact_id], 
                kwargs={
                    "motivo": Reasons.get_text_with_replace('MORE_THAN_FIVE_PENDENCIES',len(pendencies_list))
                }
            )

            return "número de pendencias maior que 5, atendente solicitado"

        for pendencie in pendencies_list:
            competence = pendencie.period.strftime("%B/%m")
            send_files(contact.contact_id, competence, pendencie.pdf)

        close_ticket.apply_async(args=[contact_id])
        return "pendencias enviadas ao cliente com sucesso"
    except Exception as e:
        return e


##-- Addtional views 
@api_view(['GET'])
def init_app(request):
    try:
        cnpj=request.query_params.get('cnpj')
        company_contact = get_company_contact(cnpj=cnpj)
        pendencies_list = company_contact.get_pendencies()

        file = request.data.get('pdf')
        company_contact.pdf = file
        company_contact.save()

        reduce = request.query_params.get('reduce')
        if reduce:
            reduce = int(reduce)
            if reduce == 0:
                pendencies_list = None

            pendencies_list = pendencies_list[:reduce]

        if len(company_contact.contact.company_contacts.all()) > 1:
            group_das_to_send(
                company_contact.contact,
                company_contact,
                get_current_period(dtime=True)
            ) 
            return Response({'success': 'Contato responsável por mais de uma empresa'})

        send_message(company_contact.contact.contact_id, text=SAUDACAO_TEXT)
        send_message(company_contact.contact.contact_id, file=file)

        if pendencies_list:
            pendencies_text = [
                pendencies.period.strftime("%B/%Y") for pendencies in pendencies_list
            ]
            pendencies_message = BaseText.get_pendencies_text(", ".join(pendencies_text))
           
            send_message(company_contact.contact_id, text=pendencies_message)
            update_ticket_control_pendencies.apply_async(args=[company_contact.contact_id, True])
        else:
            send_message(company_contact.contact_id, text=DISCLAIMER_TEXT)

        return Response({'success': 'message_sent'})
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])    
def send_groupinf_of_das(request):
    grouping_list = DASFileGrouping.objects.all()

    if grouping_list:
        for grouping in grouping_list:
            files_to_send = [(company.company_name, company.pdf) for company in grouping.companies.all()]
            contact = grouping.contact

            send_message(contact.contact_id, text=SAUDACAO_TEXT)
            for name, pdf in files_to_send:
                send_message(contact.contact_id, file=pdf, text=f"{name}")

            send_message(contact.contact_id, text=DISCLAIMER_TEXT)

        return Response({'success': f'{len(grouping_list)} contatos responsáveis por mais que uma empresa receberam os arquivos'})
    
    return Response({'info': 'Nenhum agrupamento de DAS esse mês'}, status=500)

@api_view(['POST'])
def send_message_to_client(request):
    contact_number = request.query_params.get('phone')
    contact = get_contact(contact_number=contact_number)

    text = '''
Empresários: Descubra a Nova Linha de Crédito do Pronamp! 🚀💼 

💰📈 Clique no link e saiba como impulsionar seu negócio com essa oportunidade única! 
🌟 #Pronamp #LinhaDeCrédito #Empresários #OportunidadeDeCrescimento

https://www.instagram.com/p/Cu-UcmTJwXR/
'''

    send_message(
        contact.contact_id, text=text
    )

    return Response(f"Mensagem enviada com sucesso para: {contact_number}")
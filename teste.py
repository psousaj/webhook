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
    if (isinstance(input_list, list) or isinstance(input_list, tuple)):
        return input_list[0]

    return input_list


def get_event_status(event, message_id: str = None, ticket_id: str = None) -> int:
    if event == 'ticket':
        url = "http://localhost:8000/webhook/messages/tickets/status"
        response = requests.get(
            url, params={"id": ticket_id})

        if response.status_code == 200:
            response = response.json()[0]
            if response['is_open']:
                status = response
                print(status)
                return True

        return False

    if event == 'message':
        url = "http://localhost:8000/webhook/messages/list"
        response = requests.get(url, params={"id": message_id})

        if response.status_code == 200:
            return int(response.json()[0]['status'])


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
        # if event == 'message.created':
        #     if data['data']['origin'] == 'ticket':
        #         return

        #     return handle_message_created.apply_async(
        #         args=[data, extract_value(isFromMe)])
        # if event == 'message.updated':
        #     return handle_message_updated.apply_async(
        #         args=[extract_value(message_id), data], countdown=5)
        # if event == 'ticket.created':
        #     id = extract_value(data['data']['id'])
        #     return handle_ticket_created.apply_async(args=[id])
        if event == 'ticket.updated':
            id = extract_value(data['data']['id'])
            return handle_ticket_updated(id, data)
    except KeyError as e:
        logger.debug(e)
    except TypeError as e:
        logger.debug(e)


def handle_ticket_updated(ticket_id: str, data):

    try:
        actual_status = get_event_status('ticket', ticket_id=ticket_id)
        is_open = bool(extract_value(data['data']['isOpen']))
        if actual_status and not is_open:
            url = f"{os.getenv('WEBHOOK_API')}/messages/update/tickets?id={ticket_id}&status=0"
            response = requests.patch(url)

            if response.status_code != 200:
                text = f"{response}-{response.text}"
                logger.debug(text)

                raise Exception(text)

            return response
        else:
            return (f"Status:False - o ticket com id: {ticket_id} já está fechado")
    except Exception as e:
        print(e)
        # raise retry(exc=e, countdown=60)


data = {
    "event": "ticket.updated",
    "data": {
        "id": "d51322e8-6a09-4d12-8385-96020dadf67a",
        "isOpen": "false",
        "comments": "",
        "protocol": "2023052231036",
        "origin": "automatic",
        "metrics": {
            "ticketTime": 121
        },
        "startedAt": "2023-05-22T18:36:27.414Z",
        "endedAt": "2023-05-22T18:38:28.715Z",
        "userId": None,
        "departmentId": "a78046d7-809d-4cdb-a72a-31dfbc47d862",
        "accountId": "966b70ba-27d8-43ae-a295-35e59f0007be",
        "contactId": "79db7607-6088-44c1-a010-ed4ef39d4f37",
        "currentTicketTransferId": None,
        "firstMessageId": "a1656844-5158-4eb5-9bb7-8302b99a9a76",
        "lastMessageId": "a1656844-5158-4eb5-9bb7-8302b99a9a76"
    },
    "webhookId": "27b4c18d-2ab0-4c70-a592-46bbe7e00bc8",
    "timestamp": "2023-05-22T18:38:28.810Z"
}
# manage(data)
handle_ticket_updated(data["data"]["id"], data)

from django.http import Http404
from django.shortcuts import get_object_or_404

from contacts.models import Contact, Pendencies
from control.models import MessageControl, TicketLink
from messages_api.models import Message, Ticket

def get_contact(**kwargs):
    try:
        contact = get_object_or_404(Contact, **kwargs)
        return contact
    except Http404:
        return None

def get_pendencies(**kwargs):
    try:
        pendencies = get_object_or_404(Pendencies, **kwargs)
        return pendencies
    except Http404:
        return None

def get_message_control(**kwargs):
    try:
        control = get_object_or_404(MessageControl, **kwargs)
        return control
    except Http404:
        return None

def get_ticket_link(**kwargs):
    try:
        ticket_link = get_object_or_404(TicketLink, **kwargs)
        return ticket_link
    except Http404:
        return None

def get_message(**kwargs):
    try:
        message = get_object_or_404(Message, **kwargs)
        return message
    except Http404:
        return None

def get_ticket(**kwargs):
    try:
        ticket = get_object_or_404(Ticket, **kwargs)
        return ticket
    except Http404:
        return None


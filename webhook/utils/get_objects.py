import time
from django.http import Http404
from django.shortcuts import get_object_or_404

from contacts.models import CompanyContact, Contact, Pendencies
from control.models import MessageControl, TicketLink, DASFileGrouping
from messages_api.models import Message, Ticket

max_retries = 5
att_tax = 0.1


def get_company_contact(**kwargs):
    retries = 0
    while retries < max_retries:
        try:
            contact = get_object_or_404(CompanyContact, **kwargs)
            return contact
        except Http404:
            time.sleep(att_tax)
            retries += 1
    return None


def get_contact(**kwargs):
    retries = 0
    while retries < max_retries:
        try:
            contact = get_object_or_404(Contact, **kwargs)
            return contact
        except Http404:
            time.sleep(att_tax)
            retries += 1
    return None


def get_pendencies(**kwargs):
    retries = 0
    while retries < max_retries:
        try:
            pendencies = get_object_or_404(Pendencies, **kwargs)
            return pendencies
        except Http404:
            time.sleep(0.5)
            retries += 1
    return None


def get_message_control(**kwargs):
    retries = 0
    while retries < max_retries:
        try:
            control = get_object_or_404(MessageControl, **kwargs)
            return control
        except Http404:
            time.sleep(att_tax)
            retries += 1
    return None


def get_ticket_link(**kwargs):
    retries = 0
    while retries < max_retries:
        try:
            ticket_link = get_object_or_404(TicketLink, **kwargs)
            return ticket_link
        except Http404:
            time.sleep(att_tax)
            retries += 1
    return None


def get_message(**kwargs):
    retries = 0
    while retries < max_retries:
        try:
            message = get_object_or_404(Message, **kwargs)
            return message
        except Http404:
            time.sleep(att_tax)
            retries += 1
    return None


def get_ticket(**kwargs):
    retries = 0
    while retries < max_retries:
        try:
            ticket = get_object_or_404(Ticket, **kwargs)
            return ticket
        except Http404:
            time.sleep(att_tax)
            retries += 1
    return None


def get_das_grouping(**kwargs):
    retries = 0
    while retries < max_retries:
        try:
            grouping = get_object_or_404(DASFileGrouping, **kwargs)
            return grouping
        except Http404:
            time.sleep(att_tax)
            retries += 1
    return None

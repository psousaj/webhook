from django.db import models

from messages_api.models import Ticket, Message
from webhook.request import any_request
# Create your models here.


from django.db import models


class MessageControl(models.Model):
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="ticket")
    pendencies = models.BooleanField(default=False)
    contact = models.CharField(max_length=255)
    period = models.CharField()
    status = models.IntegerField(
        choices=[(0, 'Aguardando Resposta'), (1, 'Fechado')], default=0)
    client_needs_help = models.BooleanField(default=False)
    retries = models.IntegerField(default=1)

    def is_from_me_last_message(self):
        ticket_link = self.get_ticket_link()
        if ticket_link and ticket_link.last_ticket and ticket_link.last_ticket.last_message_id != "FIRST_MESSAGE":
            last_message = Message.objects.get(
                message_id=ticket_link.last_ticket.last_message_id)
            return last_message.is_from_me
        elif self.ticket.last_message_id and self.ticket.last_message_id != "FIRST_MESSAGE":
            last_message = Message.objects.get(
                message_id=self.ticket.last_message_id)
            return last_message.is_from_me
        else:
            return True

    def get_last_message_text(self):
        ticket_link = self.get_ticket_link()
        if ticket_link and ticket_link.last_ticket and ticket_link.last_ticket.last_message_id != "FIRST_MESSAGE":
            last_message = Message.objects.get(
                message_id=ticket_link.last_ticket.last_message_id)
            return last_message.text
        elif self.ticket.last_message_id and self.ticket.last_message_id != "FIRST_MESSAGE":
            last_message = Message.objects.get(
                message_id=self.ticket.last_message_id)
            return last_message.text
        else:
            return None

    def get_protocol_number(self):
        ticket_id = self.ticket.ticket_id
        response = any_request(
            f'/tickets/{ticket_id}', method='get', json=False)

        if response.status_code == 200:
            return response.json()['protocol']
        else:
            return None

    def get_or_create_ticketlink(self):
        ticket_link, created = TicketLink.objects.get_or_create(
            message_control=self)
        return ticket_link

    def get_ticket_link(self):
        try:
            ticket_link = TicketLink.objects.get(message_control=self)
            return ticket_link
        except TicketLink.DoesNotExist:
            return None


class TicketLink(models.Model):
    message_control = models.OneToOneField(
        MessageControl, on_delete=models.CASCADE)
    additional_tickets = models.ManyToManyField(
        Ticket, related_name='ticketlinks', blank=True)
    last_ticket = models.ForeignKey(
        Ticket, related_name='last_ticketlink', null=True, on_delete=models.SET_NULL)

    def append_new_ticket(self, new_ticket):
        if not self.additional_tickets.filter(ticket_id=new_ticket.ticket_id).exists():
            self.additional_tickets.add(new_ticket)
            self.last_ticket = new_ticket
            self.save()

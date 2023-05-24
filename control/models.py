from django.db import models

from messages_api.models import Ticket, Message
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
    retries = models.IntegerField(default=1)

    def is_from_me_last_message(self):
        if self.ticket.last_message_id and self.ticket.last_message_id != "FIRST_MESSAGE":
            last_message = Message.objects.get(
                message_id=self.ticket.last_message_id)
            return last_message.is_from_me
        else:
            return True

    def get_last_message_text(self):
        if self.ticket.last_message_id and self.ticket.last_message_id != "FIRST_MESSAGE":
            last_message = Message.objects.get(
                message_id=self.ticket.last_message_id)
            return last_message.text
        else:
            return None
